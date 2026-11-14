"""Configuration and actual cryptographic approval unit checks."""

import stat
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from governed_dataops.contracts import Approval, Principal
from governed_dataops.settings import Settings, get_settings
from governed_dataops.signing import (
    generate_approval_keys,
    sign_approval,
    verify_approval_signature,
)


@pytest.mark.parametrize(
    "changes",
    [
        {"model_base_url": "https://api.external.example/v1"},
        {"model_base_url": "https://localhost.attacker.example/v1"},
        {"model_base_url": "http://user:password@localhost/v1"},
        {"model_base_url": "http://localhost/v1?forward=external"},
        {"model_base_url": "http://localhost/v1#fragment"},
        {"model_base_url": "file:///var/model"},
        {"model_name": "example-cloud"},
        {
            "model_provider": "external",
            "model_base_url": "https://api.external.example/v1",
            "model_api_key": "explicit-credential",
        },
        {
            "model_provider": "external",
            "model_base_url": "https://api.external.example/v1",
            "external_llm_authorized": True,
        },
        {
            "model_provider": "external",
            "model_base_url": "http://api.external.example/v1",
            "external_llm_authorized": True,
            "model_api_key": "explicit-credential",
        },
        {"model_provider": "silent-fallback"},
    ],
)
def test_unapproved_external_model_routes_fail_closed(changes):
    with pytest.raises(ValidationError):
        Settings(**changes)


def test_explicit_external_route_needs_consent_transport_and_credential():
    settings = Settings(
        model_provider="external",
        model_base_url="https://api.external.example/v1",
        external_llm_authorized=True,
        model_api_key="explicit-credential",
    )
    assert settings.model_provider == "external"
    assert Settings(model_base_url="http://model:8090/v1").model_provider == "local"


@pytest.mark.parametrize(
    "changes",
    [
        {"reader_token": "shared" * 6, "executor_token": "shared" * 6},
        {"approver_token": "shared" * 6, "operator_token": "shared" * 6},
        {"reader_token": "too-short"},
        {"scope": "../other"},
        {"executor_subject": "unbounded identity with spaces"},
        {"worker_concurrency": 0},
        {"worker_concurrency": 17},
        {"model_concurrency": 5},
        {"max_pending_incidents": 257},
        {"model_max_tokens": 2049},
        {"model_timeout_seconds": 181},
        {"approval_timeout_seconds": 3601},
    ],
)
def test_identity_and_resource_limits_cannot_be_bypassed_by_configuration(changes):
    with pytest.raises(ValidationError):
        Settings(**changes)


def test_role_tokens_and_model_credentials_are_not_in_settings_repr():
    settings = Settings(
        reader_token="secret-reader-token-123456789", model_api_key="secret-provider-key"
    )
    assert "secret-reader-token-123456789" not in repr(settings)
    assert "secret-provider-key" not in repr(settings)


def test_environment_configuration_is_typed_and_validated(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("DATAOPS_DEMO_MODE", "true")
    monkeypatch.setenv("DATAOPS_MAX_PENDING_INCIDENTS", "7")
    try:
        settings = get_settings()
        assert settings.demo_mode is True and settings.max_pending_incidents == 7
        get_settings.cache_clear()
        monkeypatch.setenv("DATAOPS_MODEL_CONCURRENCY", "999")
        with pytest.raises(ValidationError):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_role_credential_can_be_loaded_from_external_secret_file(tmp_path, monkeypatch):
    secret = tmp_path / "reader-token"
    secret.write_text("reader-from-file-1234567890abcdef\n")
    monkeypatch.delenv("DATAOPS_READER_TOKEN", raising=False)
    monkeypatch.setenv("DATAOPS_READER_TOKEN_FILE", str(secret))
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.reader_token == "reader-from-file-1234567890abcdef"
        assert settings.reader_token not in repr(settings)
    finally:
        get_settings.cache_clear()


def test_raw_credential_and_secret_file_configuration_is_ambiguous(tmp_path, monkeypatch):
    secret = tmp_path / "reader-token"
    secret.write_text("reader-from-file-1234567890abcdef\n")
    monkeypatch.setenv("DATAOPS_READER_TOKEN", "raw-reader-token-1234567890abcdef")
    monkeypatch.setenv("DATAOPS_READER_TOKEN_FILE", str(secret))
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="either reader_token or its file"):
            get_settings()
    finally:
        get_settings.cache_clear()


def approval():
    now = datetime.now(UTC)
    return Approval(
        plan_hash="a" * 64,
        incident_id="incident",
        target_id="target",
        environment="dev",
        scope="factory-a",
        expected_revision=2,
        policy_version="1.0",
        approver=Principal(subject="human", role="approver"),
        issued_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=2)).isoformat(),
    )


def test_real_approval_signature_is_bound_to_every_field_and_verifier_key(tmp_path):
    private, public = tmp_path / "private.pem", tmp_path / "public.pem"
    other_private, other_public = tmp_path / "other-private.pem", tmp_path / "other-public.pem"
    generate_approval_keys(private, public)
    generate_approval_keys(other_private, other_public)
    signed = sign_approval(approval(), private)
    assert verify_approval_signature(signed, public)
    assert not verify_approval_signature(signed, other_public)
    assert not verify_approval_signature(
        signed.model_copy(update={"target_id": "different"}), public
    )
    assert not verify_approval_signature(signed.model_copy(update={"expected_revision": 3}), public)
    assert not verify_approval_signature(
        signed.model_copy(update={"signature": "%%%invalid%%%"}), public
    )
    assert not verify_approval_signature(signed.model_copy(update={"signature": ""}), public)
    assert not verify_approval_signature(signed, tmp_path / "missing.pem")
    assert stat.S_IMODE(private.stat().st_mode) == 0o600


def test_key_generation_refuses_to_overwrite_identity(tmp_path):
    private, public = tmp_path / "private.pem", tmp_path / "public.pem"
    generate_approval_keys(private, public)
    original_private, original_public = private.read_bytes(), public.read_bytes()
    with pytest.raises(FileExistsError):
        generate_approval_keys(private, public)
    assert private.read_bytes() == original_private and public.read_bytes() == original_public
