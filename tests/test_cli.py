"""The generated secret layout is consumed by the real reference deployment."""

import json
import stat

import pytest

from governed_dataops.cli import initialize
from governed_dataops.settings import Settings


def test_initialization_is_private_non_disclosing_and_refuses_overwrite(tmp_path, capsys):
    initialize(tmp_path)
    output = capsys.readouterr().out
    config = {
        key.removeprefix("DATAOPS_").lower(): json.loads(value)
        for key, value in (
            line.split("=", 1) for line in (tmp_path / ".env").read_text().splitlines()
        )
    }
    values = {}
    for key, value in config.items():
        if key.endswith("_token_file"):
            path = tmp_path / ".secrets" / key.removesuffix("_token_file").replace("_", "-")
            path = path.with_name(path.name + "-token")
            token = path.read_text()
            assert token not in output and len(token) >= 32
            assert stat.S_IMODE(path.stat().st_mode) == 0o600
            values[key.removesuffix("_file")] = token
        else:
            values[key] = value
    settings = Settings(**values)
    assert settings.demo_mode and settings.environment == "dev"
    assert stat.S_IMODE((tmp_path / ".secrets").stat().st_mode) == 0o700
    assert stat.S_IMODE((tmp_path / ".secrets/approval-private.pem").stat().st_mode) == 0o600
    original = (tmp_path / ".secrets/operator-token").read_bytes()
    with pytest.raises(SystemExit, match="refusing to replace"):
        initialize(tmp_path)
    assert (tmp_path / ".secrets/operator-token").read_bytes() == original
