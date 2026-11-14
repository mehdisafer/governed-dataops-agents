"""Offline scanner-wrapper regressions; live scanner probes are separate evidence."""

import base64
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

from governed_dataops.contracts import Action, Plan, ToolName, effect_key

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/secret_scan.py"
SPEC = importlib.util.spec_from_file_location("secret_scan", SCRIPT)
scanner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scanner)


def test_worktree_snapshot_includes_tracked_ignored_files_but_never_follows_external_links(
    tmp_path,
):
    root, snapshot = tmp_path / "repo", tmp_path / "snapshot"
    root.mkdir()
    snapshot.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text("var/\n*.pem\n")
    (root / "var").mkdir()
    (root / "var/untracked.txt").write_text("ignored local tool data")
    (root / "tracked.pem").write_text("tracked synthetic credential marker")
    (root / "untracked.pem").write_text("ignored untracked synthetic marker")
    (root / "app.py").write_text("print('safe')\n")
    subprocess.run(["git", "-C", str(root), "add", "-f", "tracked.pem"], check=True)
    outside = tmp_path / "outside.txt"
    outside.write_text("must not be followed outside the repository")
    (root / "external-link").symlink_to(outside)
    report = scanner.snapshot(root, snapshot)
    paths = {item["path"] for item in report["files"]}
    assert "tracked.pem" in paths and "app.py" in paths
    assert "untracked.pem" not in paths and "var/untracked.txt" not in paths
    assert report["symlink_text_only"] == ["external-link"]
    assert not (snapshot / "external-link").is_symlink()
    assert (snapshot / "external-link").read_text() == str(outside)
    expanded = tmp_path / "expanded"
    expanded.mkdir()
    all_paths = {item["path"] for item in scanner.snapshot(root, expanded, root)["files"]}
    assert "untracked.pem" in all_paths and "var/untracked.txt" in all_paths


def test_modified_cached_scanner_checksum_manifest_is_rejected_before_execution(tmp_path):
    location = tmp_path / "var/tools" / f"gitleaks-{scanner.VERSION}"
    location.mkdir(parents=True)
    (location / scanner.CHECKSUMS).write_text("changed manifest")
    with pytest.raises(RuntimeError, match="cached asset checksum mismatch"):
        scanner.install(tmp_path)


@pytest.mark.parametrize(
    "findings,exit_code,expected",
    [
        (
            [
                {
                    "RuleID": "generic-api-key",
                    "Secret": "REDACTED",
                    "Match": "api_key=REDACTED",
                    "Fingerprint": "arbitrary-digest.txt:generic-api-key:1",
                }
            ],
            1,
            "findings_require_review",
        ),
        ([], 1, "error"),
    ],
)
def test_wrapper_never_waives_hash_shaped_candidates_or_inconsistent_scans(
    tmp_path, monkeypatch, findings, exit_code, expected
):
    def fake_git(root, *arguments, check=True):
        values = {
            ("rev-parse", "--show-toplevel"): str(root).encode(),
            ("rev-parse", "--verify", "HEAD"): b"synthetic-unit-head",
            ("rev-list", "--all", "--count"): b"1",
            ("rev-parse", "--is-shallow-repository"): b"false",
        }
        return subprocess.CompletedProcess(arguments, 0, stdout=values[arguments])

    def fake_run(arguments, **_kwargs):
        report = next(a.split("=", 1)[1] for a in arguments if a.startswith("--report-path="))
        Path(report).write_text(json.dumps(findings))
        return subprocess.CompletedProcess(arguments, exit_code, stdout="", stderr="unit fixture")

    (tmp_path / "var/tools").mkdir(parents=True)
    monkeypatch.setattr(scanner, "git", fake_git)
    monkeypatch.setattr(
        scanner, "install", lambda _root: (Path("/unit-scanner"), {"version": scanner.VERSION})
    )
    monkeypatch.setattr(scanner.subprocess, "run", fake_run)
    output = tmp_path / "report.json"
    assert scanner.run(tmp_path, output, False) != 0
    report = json.loads(output.read_text())
    assert report["status"] == expected
    assert report["reviewed_non_secret_candidates"] == []
    if findings:
        assert report["native_findings"] == findings
        assert report["raw_finding_count"] == report["unreviewed_finding_count"] == 1


def test_history_scan_refuses_a_shallow_checkout(tmp_path, monkeypatch):
    def fake_git(root, *arguments, check=True):
        values = {
            ("rev-parse", "--show-toplevel"): str(root).encode(),
            ("rev-parse", "--verify", "HEAD"): b"synthetic-unit-head",
            ("rev-list", "--all", "--count"): b"1",
            ("rev-parse", "--is-shallow-repository"): b"true",
        }
        return subprocess.CompletedProcess(arguments, 0, stdout=values[arguments])

    monkeypatch.setattr(scanner, "git", fake_git)
    output = tmp_path / "report.json"
    assert scanner.run(tmp_path, output, False) == 2
    report = json.loads(output.read_text())
    assert not report["history_scanned"]
    assert "non-shallow" in report["error"]


def semantic_fixture(
    *,
    encoded=False,
    key_field="idempotency_key",
    arbitrary_key=False,
    changed_plan=False,
    extra_use=False,
    encoding="anNvbi9wbGFpbg==",
):
    plan = Plan(
        incident_id="unit-incident",
        target_id="unit-target",
        environment="dev",
        scope="factory-a",
        evidence_id="unit-evidence",
        expected_revision=0,
        actions=[Action(tool=ToolName.REFRESH)],
        rationale="synthetic review fixture",
    )
    candidate = effect_key(plan, 0)
    if arbitrary_key:
        candidate = hashlib.sha256(b"arbitrary noncredential test digest").hexdigest()
    if changed_plan:
        plan.rationale = "different canonical plan"
    payload = {"plan": plan.model_dump(mode="json"), "effect": {key_field: candidate}}
    if extra_use:
        payload["api_key"] = candidate
    if encoded:
        document = {
            "events": [
                {
                    "payloads": [
                        {
                            "metadata": {"encoding": encoding},
                            "data": base64.b64encode(
                                json.dumps(payload, separators=(",", ":")).encode()
                            ).decode(),
                        }
                    ]
                }
            ]
        }
        line_field = '"data"'
        match = key_field + '":"REDACTED"'
    else:
        document = payload
        line_field = '"' + key_field + '"'
        match = key_field + '": "REDACTED"'
    raw = json.dumps(document, indent=2).encode()
    number = next(i for i, line in enumerate(raw.decode().splitlines(), 1) if line_field in line)
    finding = {
        "RuleID": "generic-api-key",
        "Secret": "REDACTED",
        "Match": match,
        "StartLine": number,
        "EndLine": number,
        "Tags": ["decoded:base64", "decode-depth:1"] if encoded else [],
    }
    entry = {
        "fingerprint": "trace.json:generic-api-key:" + str(number),
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "redacted_match_sha256": hashlib.sha256(match.encode()).hexdigest(),
        "kind": "effect_key",
        "reason": "unit synthetic semantic proof",
    }
    return raw, finding, entry


@pytest.mark.parametrize("encoded", [False, True])
def test_exact_operation_key_requires_complete_canonical_plan_in_same_artifact(tmp_path, encoded):
    raw, finding, entry = semantic_fixture(encoded=encoded)
    proof = scanner.verify_review(tmp_path, raw, finding, entry)
    assert proof and proof["kind"] == "effect_key" and proof["action_index"] == 0
    assert scanner.verify_review(tmp_path, raw + b" ", finding, entry) is None


@pytest.mark.parametrize(
    "updates",
    [
        {"arbitrary_key": True},
        {"changed_plan": True},
        {"key_field": "api_key"},
        {"encoded": True, "key_field": "api_key"},
        {"encoded": True, "extra_use": True},
        {"encoded": True, "encoding": "not-json-plain"},
    ],
)
def test_even_explicit_review_cannot_waive_forged_or_api_key_shaped_digests(tmp_path, updates):
    raw, finding, entry = semantic_fixture(**updates)
    assert scanner.verify_review(tmp_path, raw, finding, entry) is None


def test_valid_semantic_proof_requires_exact_recorded_occurrence(tmp_path):
    raw, finding, entry = semantic_fixture()
    artifact = tmp_path / "trace.json"
    artifact.write_bytes(raw)
    finding.update({"File": str(artifact), "Fingerprint": "native-fingerprint"})
    registry = tmp_path / "reviews.json"
    wrong = {**entry, "fingerprint": "different.json:generic-api-key:1"}
    registry.write_text(json.dumps({"version": 1, "entries": [wrong]}))
    reviewed, unresolved = scanner.adjudicate(tmp_path, tmp_path, [finding], registry, False)
    assert reviewed == [] and unresolved == ["native-fingerprint"]
    registry.write_text(json.dumps({"version": 1, "entries": [entry]}))
    reviewed, unresolved = scanner.adjudicate(tmp_path, tmp_path, [finding], registry, False)
    assert len(reviewed) == 1 and unresolved == []


@pytest.mark.parametrize("schema", ["native", "container"])
@pytest.mark.parametrize("dirty,forged", [(False, False), (True, False), (False, True)])
def test_source_hash_proof_recomputes_named_commit_blob_and_refuses_dirty_manifest(
    tmp_path, monkeypatch, dirty, forged, schema
):
    original = b"synthetic source bytes\n"
    candidate = hashlib.sha256(b"forged source" if forged else original).hexdigest()
    manifest = {
        "commit": "a" * 40,
        "tracked_worktree_clean": not dirty,
        "untracked_source_files": [],
        "files": {"src/api.py": candidate},
    }
    if schema == "container":
        manifest = {
            "commit": manifest["commit"],
            "tracked_and_clean": not dirty,
            "files": manifest["files"],
        }
    raw = json.dumps({"source": manifest}, indent=2).encode()
    line = next(i for i, text in enumerate(raw.decode().splitlines(), 1) if '"src/api.py"' in text)
    match = 'api.py": "REDACTED"'
    finding = {
        "RuleID": "generic-api-key",
        "Secret": "REDACTED",
        "Match": match,
        "StartLine": line,
        "EndLine": line,
        "Tags": [],
    }
    entry = {
        "kind": "source_digest",
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "redacted_match_sha256": hashlib.sha256(match.encode()).hexdigest(),
    }
    calls = []

    def fake_git(root, *arguments, check=True):
        calls.append(arguments)
        return subprocess.CompletedProcess(arguments, 0, stdout=original)

    monkeypatch.setattr(scanner, "git", fake_git)
    proof = scanner.verify_review(tmp_path, raw, finding, entry)
    assert bool(proof) is (not dirty and not forged)
    if not dirty:
        assert calls == [("show", "a" * 40 + ":src/api.py")]


@pytest.mark.parametrize(
    "extra",
    [
        {"tracked_worktree_clean": False},
        {"untracked_source_files": ["src/untracked.py"]},
        {"invented_clean_override": True},
    ],
)
def test_container_source_proof_refuses_ambiguous_or_extended_manifest_schema(tmp_path, extra):
    candidate = hashlib.sha256(b"source").hexdigest()
    manifest = {
        "commit": "a" * 40,
        "tracked_and_clean": True,
        "files": {"src/api.py": candidate},
        **extra,
    }
    raw = json.dumps({"source": manifest}, indent=2).encode()
    line = next(i for i, text in enumerate(raw.decode().splitlines(), 1) if '"src/api.py"' in text)
    match = 'api.py": "REDACTED"'
    finding = {
        "RuleID": "generic-api-key",
        "Secret": "REDACTED",
        "Match": match,
        "StartLine": line,
        "EndLine": line,
        "Tags": [],
    }
    entry = {
        "kind": "source_digest",
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "redacted_match_sha256": hashlib.sha256(match.encode()).hexdigest(),
    }
    assert scanner.verify_review(tmp_path, raw, finding, entry) is None
