#!/usr/bin/env python3
"""Run pinned Gitleaks against all reachable history or a Git-aware working snapshot.

Reports retain redacted native findings. A finding is never waived merely because
it resembles a digest. No repository allowlist, baseline, or inline waiver is used.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

VERSION = "8.30.1"
RELEASE_URL = f"https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}"
ASSET = f"gitleaks_{VERSION}_linux_x64.tar.gz"
ASSET_SHA256 = "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"
CHECKSUMS = f"gitleaks_{VERSION}_checksums.txt"
CHECKSUMS_SHA256 = "061476c21adaf5441516f96f185c1a4706a83cd6329b9b38762271b3d4a52fae"


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, check=check)


def install(root: Path) -> tuple[Path, dict]:
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
        raise RuntimeError("this checksum-pinned scanner supports Linux amd64 only")
    location = root / "var/tools" / f"gitleaks-{VERSION}"
    location.mkdir(parents=True, exist_ok=True)
    for name, expected in ((CHECKSUMS, CHECKSUMS_SHA256), (ASSET, ASSET_SHA256)):
        destination = location / name
        if not destination.exists():
            descriptor, temporary = tempfile.mkstemp(prefix="download-", dir=location)
            try:
                with (
                    os.fdopen(descriptor, "wb") as output,
                    urllib.request.urlopen(f"{RELEASE_URL}/{name}", timeout=30) as response,
                ):
                    shutil.copyfileobj(response, output)
                if digest(Path(temporary)) != expected:
                    raise RuntimeError(f"upstream checksum mismatch for {name}")
                Path(temporary).replace(destination)
            finally:
                Path(temporary).unlink(missing_ok=True)
        if digest(destination) != expected:
            raise RuntimeError(f"cached asset checksum mismatch for {name}")
    official = dict(
        line.split(maxsplit=1)[::-1]
        for line in (location / CHECKSUMS).read_text().splitlines()
        if line.strip()
    )
    if official.get(ASSET) != ASSET_SHA256:
        raise RuntimeError("archive checksum disagrees with the pinned official checksum manifest")
    extracted = location / "bin"
    extracted.mkdir(exist_ok=True)
    with tarfile.open(location / ASSET) as archive:
        for name in ("gitleaks", "LICENSE"):
            member = archive.getmember(name)
            if not member.isfile():
                raise RuntimeError("unexpected scanner archive entry")
            content = archive.extractfile(member)
            if content is None:
                raise RuntimeError("scanner archive is incomplete")
            expected = content.read()
            destination = extracted / name
            if destination.exists():
                if destination.read_bytes() != expected:
                    raise RuntimeError(f"installed scanner component changed: {name}")
            else:
                with destination.open("xb") as output:
                    output.write(expected)
                destination.chmod(0o755 if name == "gitleaks" else 0o644)
    binary = extracted / "gitleaks"
    reported = subprocess.run(
        [str(binary), "version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if reported != VERSION:
        raise RuntimeError("installed scanner reports an unexpected version")
    if "MIT License" not in (extracted / "LICENSE").read_text():
        raise RuntimeError("scanner archive licence is not the expected MIT licence")
    return binary, {
        "name": "gitleaks",
        "version": reported,
        "archive_url": f"{RELEASE_URL}/{ASSET}",
        "archive_sha256": ASSET_SHA256,
        "checksum_manifest_url": f"{RELEASE_URL}/{CHECKSUMS}",
        "checksum_manifest_sha256": CHECKSUMS_SHA256,
        "binary_sha256": digest(binary),
        "licence": "MIT",
        "licence_sha256": digest(extracted / "LICENSE"),
    }


def snapshot(root: Path, destination: Path) -> dict:
    """Always include tracked files, including paths now covered by .gitignore."""
    paths = sorted(
        set(
            git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").stdout.split(
                b"\0"
            )
        )
        - {b""}
    )
    manifest, removed, symbolic_links = [], [], []
    for raw in paths:
        relative = Path(os.fsdecode(raw))
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("Git returned an unsafe relative path")
        source, target = root / relative, destination / relative
        if source.is_symlink():
            # Do not follow a link outside the authorized repository. Scan its text.
            content = os.fsencode(os.readlink(source))
            symbolic_links.append(relative.as_posix())
        elif source.is_file():
            content = source.read_bytes()
        elif not source.exists():
            removed.append(relative.as_posix())
            continue
        else:
            raise RuntimeError(f"unscanned directory/submodule at {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        manifest.append(
            {
                "path": relative.as_posix(),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return {
        "file_count": len(manifest),
        "content_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "files": manifest,
        "tracked_deleted_paths": removed,
        "symlink_text_only": symbolic_links,
        "selection": "git ls-files --cached --others --exclude-standard; tracked ignored paths included",
    }


def run(root: Path, output: Path, working_tree: bool) -> int:
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "mode": "working_tree" if working_tree else "git_history",
        "status": "error",
        "history_scanned": False,
        "reviewed_non_secret_candidates": [],
        "unreviewed_findings": [],
        "limitations": [
            "Pattern detection cannot prove the absence of credentials or malicious dependencies.",
            "Upstream built-in rules and their default allowlists apply; no local exceptions are used.",
            "Working-tree mode respects Git ignores only for untracked files; history mode scans reachable refs.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        actual_root = Path(
            os.fsdecode(git(root, "rev-parse", "--show-toplevel").stdout).strip()
        ).resolve()
        if actual_root != root:
            raise RuntimeError("--root must name the repository root")
        head = git(root, "rev-parse", "--verify", "HEAD", check=False)
        report["head"] = head.stdout.decode().strip() if head.returncode == 0 else None
        report["reachable_commit_count"] = int(git(root, "rev-list", "--all", "--count").stdout)
        shallow = git(root, "rev-parse", "--is-shallow-repository").stdout.strip() == b"true"
        report["shallow_clone"] = shallow
        if not working_tree and (shallow or not report["reachable_commit_count"]):
            raise RuntimeError(
                "complete history requires at least one commit and a non-shallow clone"
            )
        binary, report["scanner"] = install(root)
        temporary_root = root / "var/tools"
        with tempfile.TemporaryDirectory(prefix="secret-scan-", dir=temporary_root) as temporary:
            temporary = Path(temporary)
            config = temporary / "default.toml"
            config.write_text("[extend]\nuseDefault = true\n")
            ignore = temporary / "empty.ignore"
            ignore.write_text("")
            native = temporary / "native.json"
            if working_tree:
                source = temporary / "snapshot"
                source.mkdir()
                report["snapshot"] = snapshot(root, source)
                command = [str(binary), "dir", str(source)]
            else:
                source = root
                command = [str(binary), "git", str(root), "--log-opts=--all --full-history -m"]
            command += [
                "--no-banner",
                "--redact=100",
                "--report-format=json",
                f"--report-path={native}",
                f"--config={config}",
                f"--gitleaks-ignore-path={ignore}",
                "--ignore-gitleaks-allow",
            ]
            environment = {k: v for k, v in os.environ.items() if not k.startswith("GITLEAKS_")}
            result = subprocess.run(
                command, cwd=temporary, env=environment, capture_output=True, text=True, timeout=300
            )
            # --redact=100 applies to both this native report and scanner diagnostics.
            report["scanner_exit_code"] = result.returncode
            report["scanner_stdout"] = result.stdout
            report["scanner_stderr"] = result.stderr
            findings = json.loads(native.read_text()) if native.exists() else None
            if (
                result.returncode not in {0, 1}
                or findings is None
                or not isinstance(findings, list)
            ):
                raise RuntimeError("scanner did not produce a completed JSON scan")
            report["native_findings"] = findings
            report["raw_finding_count"] = len(findings)
            report["unreviewed_findings"] = [f.get("Fingerprint", "") for f in findings]
            report["unreviewed_finding_count"] = len(findings)
            report["history_scanned"] = not working_tree
            report["status"] = "findings_require_review" if findings else "no_findings"
            code = 1 if findings else 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, tarfile.TarError) as exc:
        # Exceptions from subprocess never expose its captured output here.
        report["error"] = str(exc)
        code = 2
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "report": str(output),
                "status": report["status"],
                "raw_finding_count": report.get("raw_finding_count"),
                "history_scanned": report["history_scanned"],
            }
        )
    )
    return code


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("secret-scan.json"))
    parser.add_argument("--working-tree", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(args.root.resolve(), args.output.resolve(), args.working_tree))


if __name__ == "__main__":
    main()
