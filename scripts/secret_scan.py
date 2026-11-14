#!/usr/bin/env python3
"""Run pinned Gitleaks against all reachable history or a Git-aware working snapshot.

Reports retain redacted native findings. Explicit artifact-bound review records
require independent semantic recomputation; a hexadecimal shape is not a waiver.
"""

import argparse
import base64
import hashlib
import json
import os
import platform
import re
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


def snapshot(root: Path, destination: Path, directory: Path | None = None) -> dict:
    """Always include tracked files, including paths now covered by .gitignore."""
    if directory is not None:
        if not directory.is_dir() or not directory.is_relative_to(root):
            raise ValueError("expanded directory must exist within the repository")
        paths = sorted(
            os.fsencode(p.relative_to(root))
            for p in directory.rglob("*")
            if p.is_file() or p.is_symlink()
        )
    else:
        paths = sorted(
            set(
                git(
                    root, "ls-files", "--cached", "--others", "--exclude-standard", "-z"
                ).stdout.split(b"\0")
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
        "selection": (
            "all expanded directory files, including Git-ignored files"
            if directory
            else "git ls-files --cached --others --exclude-standard; tracked ignored paths included"
        ),
    }


def strict_json(raw: str | bytes):
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key in proof artifact")
            result[key] = value
        return result

    def reject_constant(_value):
        raise ValueError("non-finite JSON value in proof artifact")

    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)


def json_nodes(value, pointer=""):
    """Decode only actual Temporal JSON/plain payload envelopes, never arbitrary logs."""
    yield pointer, value
    if isinstance(value, dict):
        if value.get("metadata", {}).get("encoding") == "anNvbi9wbGFpbg==" and isinstance(
            value.get("data"), str
        ):
            decoded = strict_json(base64.b64decode(value["data"], validate=True))
            yield from json_nodes(decoded, pointer + "/data#json-plain")
        for key, child in value.items():
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from json_nodes(child, pointer + "/" + escaped)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from json_nodes(child, pointer + "/" + str(index))


def fingerprint(finding: dict, relative: str) -> str:
    """Portable identity; content SHA and exact redacted match bind the occurrence."""
    return f"{relative}:{finding.get('RuleID')}:{finding.get('StartLine')}"


def verify_review(root: Path, artifact: bytes, finding: dict, entry: dict) -> dict | None:
    """Fail closed unless a recorded occurrence is reproducibly non-secret."""
    try:
        if finding.get("RuleID") != "generic-api-key" or finding.get("Secret") != "REDACTED":
            return None
        if hashlib.sha256(artifact).hexdigest() != entry.get("artifact_sha256"):
            return None
        if hashlib.sha256(finding["Match"].encode()).hexdigest() != entry.get(
            "redacted_match_sha256"
        ):
            return None
        if finding["StartLine"] != finding["EndLine"] or finding["StartLine"] < 1:
            return None
        lines = artifact.decode().splitlines()
        line = lines[finding["StartLine"] - 1].strip().rstrip(",")
        field = strict_json("{" + line + "}")
        document = strict_json(artifact)
        if entry["kind"] == "effect_key":
            from governed_dataops.contracts import Plan, effect_key

            nodes = list(json_nodes(document))
            if set(field) == {"idempotency_key"} and not finding.get("Tags"):
                candidates, matched_text = [field["idempotency_key"]], line
            elif set(field) == {"data"} and set(finding.get("Tags", [])) == {
                "decoded:base64",
                "decode-depth:1",
            }:
                # The source line must be an actual payload with JSON/plain metadata.
                envelopes = [
                    v
                    for _, v in nodes
                    if isinstance(v, dict)
                    and v.get("data") == field["data"]
                    and v.get("metadata", {}).get("encoding") == "anNvbi9wbGFpbg=="
                ]
                if not envelopes:
                    return None
                matched_text = base64.b64decode(field["data"], validate=True).decode()
                payload = strict_json(matched_text)
                candidates = [
                    v["idempotency_key"]
                    for _, v in json_nodes(payload)
                    if isinstance(v, dict) and "idempotency_key" in v
                ]
            else:
                return None
            matches = []
            for candidate in set(candidates):
                if not isinstance(candidate, str) or not re.fullmatch(r"[a-f0-9]{64}", candidate):
                    continue
                if not finding["Match"].startswith('idempotency_key"'):
                    continue
                if finding["Match"].replace("REDACTED", candidate) not in matched_text:
                    continue
                # A second use under an API-key/rationale field is not waived.
                if matched_text.count(candidate) != candidates.count(candidate):
                    continue
                for pointer, node in nodes:
                    if (
                        not isinstance(node, dict)
                        or "catalog_version" not in node
                        or "actions" not in node
                    ):
                        continue
                    try:
                        plan = Plan.model_validate(node)
                    except ValueError:
                        continue
                    if (
                        len(plan.actions) == 1
                        and plan.action_budget == 1
                        and effect_key(plan, 0) == candidate
                    ):
                        matches.append(
                            {
                                "kind": "effect_key",
                                "plan_pointer": pointer,
                                "plan_digest": plan.digest(),
                                "action_index": 0,
                            }
                        )
                        break
            return matches[0] if len(matches) == 1 else None
        if entry["kind"] == "source_digest":
            if len(field) != 1:
                return None
            source_path, candidate = next(iter(field.items()))
            path = Path(source_path)
            if path.is_absolute() or ".." in path.parts:
                return None
            if not isinstance(candidate, str) or not re.fullmatch(r"[a-f0-9]{64}", candidate):
                return None
            if finding["Match"].replace("REDACTED", candidate) not in line:
                return None
            for pointer, manifest in json_nodes(document):
                if (
                    not isinstance(manifest, dict)
                    or manifest.get("tracked_worktree_clean") is not True
                    or manifest.get("untracked_source_files")
                ):
                    continue
                commit = manifest.get("commit", "")
                if (
                    not re.fullmatch(r"[a-f0-9]{40}", commit)
                    or manifest.get("files", {}).get(source_path) != candidate
                ):
                    continue
                original = git(root, "show", f"{commit}:{source_path}", check=False)
                if (
                    original.returncode == 0
                    and hashlib.sha256(original.stdout).hexdigest() == candidate
                ):
                    return {
                        "kind": "source_digest",
                        "manifest_pointer": pointer,
                        "source_commit": commit,
                        "source_path": source_path,
                    }
            return None
    except (KeyError, IndexError, TypeError, ValueError, UnicodeError, AttributeError):
        return None
    return None


def adjudicate(
    root: Path, source: Path, findings: list, review_file: Path, history: bool
) -> tuple[list, list]:
    if not review_file.exists():
        return [], [f.get("Fingerprint", "") for f in findings]
    registry = strict_json(review_file.read_bytes())
    if (
        set(registry) != {"version", "entries"}
        or registry["version"] != 1
        or not isinstance(registry["entries"], list)
    ):
        raise ValueError("unsupported non-secret review registry")
    reviewed, unresolved = [], []
    for finding in findings:
        path = Path(finding["File"])
        if not history:
            path = path.relative_to(source)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("unsafe finding artifact path")
        relative = path.as_posix()
        identity = fingerprint(finding, relative)
        entries = [e for e in registry["entries"] if e.get("fingerprint") == identity]
        proof, matched_entry = None, None
        if entries:
            if history:
                commit = finding.get("Commit", "")
                if not re.fullmatch(r"[a-f0-9]{40}", commit):
                    raise ValueError("invalid finding commit")
                artifact = git(root, "show", f"{commit}:{relative}").stdout
            else:
                artifact = (source / path).read_bytes()
            for entry in entries:
                proof = verify_review(root, artifact, finding, entry)
                if proof:
                    matched_entry = entry
                    break
        if proof:
            reviewed.append(
                {
                    "fingerprint": identity,
                    "native_fingerprint": finding.get("Fingerprint"),
                    "artifact_sha256": matched_entry["artifact_sha256"],
                    "reason": matched_entry.get("reason", ""),
                    "proof": proof,
                }
            )
        else:
            unresolved.append(finding.get("Fingerprint", ""))
    return reviewed, unresolved


def run(
    root: Path,
    output: Path,
    working_tree: bool,
    directory: Path | None = None,
    review_file: Path | None = None,
) -> int:
    history = not working_tree and directory is None
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "wrapper_sha256": digest(Path(__file__)),
        "mode": "expanded_directory"
        if directory
        else ("working_tree" if working_tree else "git_history"),
        "status": "error",
        "history_scanned": False,
        "reviewed_non_secret_candidates": [],
        "unreviewed_findings": [],
        "limitations": [
            "Pattern detection cannot prove the absence of credentials or malicious dependencies.",
            "Upstream built-in rules and allowlists apply; explicit content-bound proofs retain every raw finding.",
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
        if history and (shallow or not report["reachable_commit_count"]):
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
            if not history:
                source = temporary / "snapshot"
                source.mkdir()
                if directory is not None and (working_tree or output.is_relative_to(directory)):
                    raise ValueError(
                        "choose one scan mode and keep the report outside the scanned directory"
                    )
                report["snapshot"] = snapshot(root, source, directory)
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
            if result.returncode != int(bool(findings)):
                raise RuntimeError("scanner exit status disagrees with its finding report")
            report["native_findings"] = findings
            report["raw_finding_count"] = len(findings)
            reviews = review_file or root / "evidence/secret-review.json"
            reviewed, unresolved = adjudicate(root, source, findings, reviews, history)
            report["reviewed_non_secret_candidates"] = reviewed
            report["review_registry_sha256"] = digest(reviews) if reviews.exists() else None
            report["unreviewed_findings"] = unresolved
            report["unreviewed_finding_count"] = len(unresolved)
            report["history_scanned"] = history
            report["status"] = (
                "findings_require_review"
                if unresolved
                else ("reviewed_non_secret_findings" if findings else "no_findings")
            )
            code = 1 if unresolved else 0
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
    parser.add_argument(
        "--directory",
        type=Path,
        help="scan all expanded files in this repository directory, including ignored files",
    )
    parser.add_argument(
        "--reviews",
        type=Path,
        help="explicit semantic review registry; defaults to evidence/secret-review.json",
    )
    args = parser.parse_args()
    raise SystemExit(
        run(
            args.root.resolve(),
            args.output.resolve(),
            args.working_tree,
            args.directory.resolve() if args.directory else None,
            args.reviews.resolve() if args.reviews else None,
        )
    )


if __name__ == "__main__":
    main()
