"""Tests for the packaging licence gate, including negative cases."""

import runpy
from pathlib import Path
from zipfile import ZipFile

import pytest

# CircleCI invokes the pytest entry point, which does not add the repository root
# to sys.path. Load this standalone review script by its exact path instead.
inspect_wheel = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts" / "verify_wheel_license.py")
)["inspect_wheel"]

INFO = "governed_dataops_agents-0.1.0a1.dist-info/"


@pytest.fixture
def fixture(tmp_path: Path):
    license_file = tmp_path / "LICENSE"
    license_file.write_text("Apache License\nVersion 2.0, January 2004\n")
    return tmp_path, license_file


def wheel(
    folder: Path,
    content: bytes,
    expression: str = "Apache-2.0",
    declared_file: str = "LICENSE",
    include_license: bool = True,
    extra_path: str | None = None,
) -> Path:
    name = folder / "governed_dataops_agents-0.1.0a1-py3-none-any.whl"
    with ZipFile(name, "w") as output:
        output.writestr("governed_dataops/__init__.py", "x=1\n")
        output.writestr(
            INFO + "METADATA",
            "Metadata-Version: 2.4\nName: governed-dataops-agents\n"
            f"License-Expression: {expression}\nLicense-File: {declared_file}\n\n",
        )
        if include_license:
            output.writestr(INFO + "licenses/LICENSE", content)
        if extra_path is not None:
            output.writestr(extra_path, "do not package")
    return name


def test_valid_wheel(fixture):
    root, license_file = fixture
    report = inspect_wheel(wheel(root, license_file.read_bytes()), license_file)
    assert report["status"] == "passed"
    assert report["license_expression"] == "Apache-2.0"


@pytest.mark.parametrize("spdx", ["MIT", "", "Apache-2.0 OR MIT"])
def test_wrong_spdx_fails(fixture, spdx):
    root, license_file = fixture
    with pytest.raises(ValueError, match="License-Expression"):
        inspect_wheel(wheel(root, license_file.read_bytes(), expression=spdx), license_file)


def test_missing_license_fails(fixture):
    root, license_file = fixture
    with pytest.raises(ValueError, match="embedded"):
        inspect_wheel(wheel(root, license_file.read_bytes(), include_license=False), license_file)


def test_changed_license_fails(fixture):
    root, license_file = fixture
    with pytest.raises(ValueError, match="bytes differ"):
        inspect_wheel(wheel(root, b"modified"), license_file)


def test_wrong_license_declaration_fails(fixture):
    root, license_file = fixture
    with pytest.raises(ValueError, match="License-File"):
        inspect_wheel(wheel(root, license_file.read_bytes(), declared_file="OTHER"), license_file)


@pytest.mark.parametrize("path", [
    "evidence/effect-log.json",
    "var/config.json",
    ".secrets/operator-token",
    "governed_dataops/approval-private.pem",
    "runtime/state.db",
    "../escape.txt",
])
def test_sensitive_members_rejected(fixture, path):
    root, license_file = fixture
    with pytest.raises(ValueError, match="prohibited"):
        inspect_wheel(wheel(root, license_file.read_bytes(), extra_path=path), license_file)
