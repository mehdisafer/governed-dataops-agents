#!/usr/bin/env python3
"""Inspect wheel licence metadata, embedded Apache text, and excluded sensitive files."""

import argparse
import hashlib
import json
from email import policy
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

RESTRICTED_PARTS = {"evidence", "runtime", "var", "secrets", ".secrets", ".git"}
RESTRICTED_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".pem", ".key", ".env")


def inspect_wheel(wheel: Path, license_path: Path) -> dict:
    expected = license_path.read_bytes()
    if b"Apache License" not in expected[:150] or b"Version 2.0, January 2004" not in expected[:300]:
        raise ValueError("root LICENSE does not contain the selected Apache-2.0 text")
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate wheel members")
        forbidden = [
            name for name in names
            if name.startswith("/")
            or ".." in PurePosixPath(name).parts
            or any(part in RESTRICTED_PARTS for part in PurePosixPath(name).parts)
            or name.lower().endswith(RESTRICTED_SUFFIXES)
        ]
        if forbidden:
            raise ValueError("wheel contains prohibited private or runtime material")
        metadata_members = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata_members) != 1:
            raise ValueError("exactly one wheel METADATA file is required")
        metadata = BytesParser(policy=policy.default).parsebytes(
            archive.read(metadata_members[0])
        )
        if metadata.get_all("License-Expression", []) != ["Apache-2.0"]:
            raise ValueError("expected one Apache-2.0 License-Expression")
        if metadata.get_all("License-File", []) != ["LICENSE"]:
            raise ValueError("expected one License-File: LICENSE declaration")
        license_members = [name for name in names if name.endswith(".dist-info/licenses/LICENSE")]
        if len(license_members) != 1:
            raise ValueError("exactly one embedded PEP 639 LICENSE is required")
        data = archive.read(license_members[0])
        if data != expected:
            raise ValueError("embedded licence bytes differ from root LICENSE")
        if not any(name.startswith("governed_dataops/") for name in names):
            raise ValueError("project Python module missing from wheel")
    return {
        "status": "passed",
        "wheel": wheel.name,
        "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "license_expression": "Apache-2.0",
        "license_sha256": hashlib.sha256(data).hexdigest(),
        "license_member": license_members[0],
        "entry_count": len(names),
        "forbidden_member_count": 0,
        "scope": "built wheel only; not package publication or legal compatibility",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--license-file", type=Path, default=Path("LICENSE"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    wheels = sorted(args.wheel_dir.glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit("expected exactly one wheel in the output directory")
    report = inspect_wheel(wheels[0], args.license_file)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
