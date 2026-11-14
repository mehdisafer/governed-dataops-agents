#!/usr/bin/env python3
"""Inventory installed distributions, lock pins and locally present runtime assets.

Licence strings are package declarations, not a legal compatibility assessment.
This command performs no downloads and does not start any service.
"""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sqlite3
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def installed_component(distribution) -> dict:
    metadata = distribution.metadata
    license_files = []
    for relative in distribution.files or []:
        if relative.name.lower().startswith(("license", "licence", "copying", "notice")):
            source = Path(distribution.locate_file(relative))
            if source.is_file():
                license_files.append(
                    {
                        "path": str(relative),
                        "bytes": source.stat().st_size,
                        "sha256": digest(source),
                    }
                )
    expression = metadata.get("License-Expression")
    declared = metadata.get("License")
    classifiers = [c for c in metadata.get_all("Classifier", []) if c.startswith("License ::")]
    declared = None if declared in {None, "", "UNKNOWN"} else declared
    known = bool(expression or declared or classifiers)
    return {
        "name": metadata.get("Name", "unknown"),
        "version": distribution.version,
        "pypi_url": f"https://pypi.org/project/{metadata.get('Name', '')}/{distribution.version}/",
        "project_urls": metadata.get_all("Project-URL", []),
        "home_page": metadata.get("Home-page"),
        "license_expression": expression,
        "license_declared": declared,
        "license_classifiers": classifiers,
        "license_files": license_files,
        "license_status": "declared_metadata" if known else "unresolved_metadata",
        "requires_python": metadata.get("Requires-Python"),
    }


def inventory(root: Path, runtime_dir: Path) -> dict:
    lock = root / "uv.lock"
    project = tomllib.loads((root / "pyproject.toml").read_text())
    locked = tomllib.loads(lock.read_text())
    installed = sorted(
        [installed_component(d) for d in importlib.metadata.distributions()],
        key=lambda component: component["name"].lower(),
    )
    runtime = {"manifest_present": False, "assets": [], "execution_observed_by_inventory": False}
    manifest_path = runtime_dir / "provisioning.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        runtime["manifest_present"] = True
        runtime["manifest_sha256"] = digest(manifest_path)
        runtime["created_at"] = manifest.get("created_at")
        runtime["declared_licence_sources"] = manifest.get("licence_sources", {})
        for asset in manifest.get("assets", []):
            record = {k: v for k, v in asset.items() if k != "command"}
            record["local_file_present"] = False
            record["local_bytes_match_pin"] = False
            name = Path(asset["name"])
            if name.is_absolute() or ".." in name.parts:
                raise ValueError("runtime manifest asset name is unsafe")
            for path in (runtime_dir / name, runtime_dir / "downloads" / name):
                if path.is_file():
                    actual_size, actual_hash = path.stat().st_size, digest(path)
                    record.update(
                        {
                            "local_file_present": True,
                            "observed_bytes": actual_size,
                            "observed_sha256": actual_hash,
                            "local_bytes_match_pin": actual_size == asset.get("bytes")
                            and actual_hash == asset.get("sha256"),
                        }
                    )
                    break
            runtime["assets"].append(record)
    return {
        "created_at": datetime.now(UTC).isoformat(),
        "scope": "installed Python environment (including dev tools), complete uv lock, optional local runtime artifacts",
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": sys.platform,
            "sqlite_version": sqlite3.sqlite_version,
        },
        "project": {
            "name": project["project"]["name"],
            "version": project["project"]["version"],
            "own_license_selected": bool(project["project"].get("license")),
            "direct_dependencies": project["project"].get("dependencies", []),
        },
        "lock": {
            "sha256": digest(lock),
            "packages": [
                {"name": p["name"], "version": p["version"], "source": p.get("source", {})}
                for p in locked["package"]
            ],
        },
        "installed": installed,
        "unresolved_license_metadata": [
            {
                "name": d["name"],
                "version": d["version"],
                "license_files_present": bool(d["license_files"]),
            }
            for d in installed
            if d["license_status"] == "unresolved_metadata"
        ],
        "runtime": runtime,
        "limitations": [
            "Metadata declarations and asset checksums do not establish licence compatibility or security certification.",
            "Missing or unresolved metadata remains listed; no package is silently exempted.",
            "Installed distributions include development dependencies; the separate pip-audit report covers its frozen requirements input.",
            "This inventory does not execute runtimes, inspect OCI layers, or audit native/system-package vulnerabilities.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--runtime-dir", type=Path, default=Path("var/runtime"))
    parser.add_argument("--output", type=Path, default=Path("component-inventory.json"))
    args = parser.parse_args()
    result = inventory(args.root.resolve(), args.runtime_dir.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "installed_distributions": len(result["installed"]),
                "locked_packages": len(result["lock"]["packages"]),
                "unresolved_license_metadata": result["unresolved_license_metadata"],
                "runtime_assets": len(result["runtime"]["assets"]),
            }
        )
    )


if __name__ == "__main__":
    main()
