#!/usr/bin/env python3
"""Verify pinned Terraform and plan isolated local Docker resources without applying.

The copied configuration uses an empty temporary state and the committed provider
lock. Only the local /var/run/docker.sock daemon is permitted. No apply, import,
destroy, service restart or resource lifecycle change is executed.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import tempfile
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.17.2"
ARCHIVE = "terraform_1.17.2_linux_amd64.zip"
ARCHIVE_SHA256 = "e6f16b2f0b137ee5729caa8c4e79a3bae4ee261acd198a1fcfa8584a6296605b"
ARCHIVE_BYTES = 38245299
CHECKSUMS = "terraform_1.17.2_SHA256SUMS"
CHECKSUMS_SHA256 = "6ece9a6cf116bb7b59adb14103140aa197b2d09543457f611c5a7f362302beab"
CHECKSUMS_BYTES = 1592
RELEASE = "https://releases.hashicorp.com/terraform/1.17.2/"
LOCAL_DOCKER = "unix:///var/run/docker.sock"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, default=str) + "\n")


def verified_download(cache: Path, name: str, expected: str, size: int) -> Path:
    path = cache / name
    if not path.exists():
        descriptor, temporary = tempfile.mkstemp(prefix="terraform-download-", dir=cache)
        try:
            with (
                os.fdopen(descriptor, "wb") as output,
                urllib.request.urlopen(RELEASE + name, timeout=60) as response,
            ):
                shutil.copyfileobj(response, output, length=1024 * 1024)
            candidate = Path(temporary)
            if candidate.stat().st_size != size or sha256(candidate) != expected:
                raise RuntimeError(f"Downloaded Terraform asset failed verification: {name}")
            candidate.replace(path)
        finally:
            Path(temporary).unlink(missing_ok=True)
    if path.stat().st_size != size or sha256(path) != expected:
        raise RuntimeError(f"Existing Terraform cache asset failed verification: {name}")
    return path


class Runner:
    def __init__(self, output: Path, workspace: Path):
        self.output, self.workspace = output, workspace
        self.commands = []
        self.env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("TF_") and not key.startswith("DOCKER_")
        }
        config = workspace / "terraform.rc"
        config.write_text("disable_checkpoint = true\nprovider_installation {\n  direct {}\n}\n")
        self.env.update(
            TF_IN_AUTOMATION="1",
            TF_INPUT="0",
            TF_DATA_DIR=str(workspace / "provider-cache"),
            TF_CLI_CONFIG_FILE=str(config),
            CHECKPOINT_DISABLE="1",
        )

    def run(
        self, name: str, argv: list[str], *, allowed=(0,), timeout=180
    ) -> subprocess.CompletedProcess:
        print(json.dumps({"gate": name, "state": "running"}), flush=True)
        process = subprocess.Popen(
            argv,
            cwd=self.workspace,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                stdout, stderr = process.communicate(timeout=10)
        (self.output / f"{name}.stdout.log").write_text(stdout)
        (self.output / f"{name}.stderr.log").write_text(stderr)
        record = {
            "gate": name,
            "argv": argv,
            "exit_code": process.returncode,
            "timed_out": timed_out,
            "stdout": f"{name}.stdout.log",
            "stderr": f"{name}.stderr.log",
        }
        self.commands.append(record)
        write_json(self.output / "commands.json", self.commands)
        if timed_out or process.returncode not in allowed:
            raise RuntimeError(
                f"{name} failed (exit {process.returncode}, timeout={timed_out}); original output retained"
            )
        return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)

    def resource_absence(self, stack: str, phase: str) -> None:
        for kind, names in (
            ("network", [stack + "-private"]),
            ("volume", [stack + "-app-data", stack + "-temporal-data"]),
        ):
            for index, name in enumerate(names):
                response = self.run(
                    f"{phase}-{kind}-{index}",
                    [
                        "docker",
                        "--host",
                        LOCAL_DOCKER,
                        kind,
                        "ls",
                        "--filter",
                        "name=^" + name + "$",
                        "--format",
                        "{{.Name}}",
                    ],
                )
                if name in response.stdout.splitlines():
                    raise RuntimeError(f"Isolated plan name unexpectedly exists: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=ROOT / "var" / "tool-cache")
    parser.add_argument("--source-commit")
    args = parser.parse_args()
    output, cache = args.output.resolve(), args.cache.resolve()
    output.mkdir(parents=True, exist_ok=False)
    cache.mkdir(parents=True, exist_ok=True)
    inputs = sorted((ROOT / "infra/terraform").glob("*.tf"))
    inputs += [ROOT / "infra/terraform/.terraform.lock.hcl", Path(__file__).resolve()]
    hashes = {str(path.relative_to(ROOT)): sha256(path) for path in inputs}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tracked = set(subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines())
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT).returncode == 0
    stack = "gda-plan-" + uuid4().hex[:12]
    metadata = {
        "started_at": datetime.now(UTC).isoformat(),
        "gate": "terraform_local_docker_plan",
        "status": "running",
        "source_commit": commit,
        "source_inputs": hashes,
        "source_tracked_and_clean": set(hashes) <= tracked and clean,
        "stack_name": stack,
        "docker_host": LOCAL_DOCKER,
        "terraform_apply_executed": False,
        "resource_changes_applied": False,
    }
    write_json(output / "run.json", metadata)
    try:
        if platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
            raise RuntimeError("This pinned validation tool supports Linux amd64 only")
        if args.source_commit and (
            args.source_commit != commit or not metadata["source_tracked_and_clean"]
        ):
            raise RuntimeError("Requested commit does not match the clean tracked source")
        sums = verified_download(cache, CHECKSUMS, CHECKSUMS_SHA256, CHECKSUMS_BYTES)
        entries = dict(
            (line.split()[1].lstrip("*"), line.split()[0]) for line in sums.read_text().splitlines()
        )
        if entries.get(ARCHIVE) != ARCHIVE_SHA256:
            raise RuntimeError(
                "Official checksum manifest disagrees with the pinned archive digest"
            )
        archive = verified_download(cache, ARCHIVE, ARCHIVE_SHA256, ARCHIVE_BYTES)
        shutil.copyfile(sums, output / CHECKSUMS)
        write_json(
            output / "tool-provenance.json",
            {
                "version": VERSION,
                "archive": {
                    "url": RELEASE + ARCHIVE,
                    "sha256": ARCHIVE_SHA256,
                    "bytes": ARCHIVE_BYTES,
                },
                "official_checksum_manifest": {
                    "url": RELEASE + CHECKSUMS,
                    "sha256": CHECKSUMS_SHA256,
                    "bytes": CHECKSUMS_BYTES,
                },
            },
        )
        with tempfile.TemporaryDirectory(prefix="dataops-terraform-plan-") as temporary:
            workspace = Path(temporary)
            with zipfile.ZipFile(archive) as release:
                for name in ("terraform", "LICENSE.txt"):
                    with release.open(name) as source, (workspace / name).open("xb") as target:
                        shutil.copyfileobj(source, target)
            binary = workspace / "terraform"
            binary.chmod(0o755)
            shutil.copyfile(workspace / "LICENSE.txt", output / "terraform-LICENSE.txt")
            configuration = workspace / "configuration"
            configuration.mkdir()
            for path in inputs[:-1]:
                shutil.copyfile(path, configuration / path.name)
            runner = Runner(output, workspace)
            version = runner.run("version", [str(binary), "version", "-json"])
            assert json.loads(version.stdout)["terraform_version"] == VERSION
            command = [str(binary), "-chdir=" + str(configuration)]
            runner.run("format", [*command, "fmt", "-check", "-recursive"])
            runner.run(
                "init",
                [
                    *command,
                    "init",
                    "-backend=false",
                    "-input=false",
                    "-lockfile=readonly",
                    "-no-color",
                ],
            )
            validated = runner.run("validate", [*command, "validate", "-json"])
            validation = json.loads(validated.stdout)
            write_json(output / "validation.json", validation)
            if validation.get("valid") is not True:
                raise RuntimeError("Terraform did not report a valid configuration")
            if (
                sha256(configuration / ".terraform.lock.hcl")
                != hashes["infra/terraform/.terraform.lock.hcl"]
            ):
                raise RuntimeError("Provider lock file changed despite readonly initialization")
            if shutil.which("docker") is None:
                raise RuntimeError("Docker CLI/local daemon unavailable; plan was not executed")
            runner.run(
                "docker-local-version",
                [
                    "docker",
                    "--host",
                    LOCAL_DOCKER,
                    "version",
                    "--format",
                    "{{json .Server.Version}}",
                ],
            )
            runner.resource_absence(stack, "before-plan")
            plan = workspace / "verified-plan.tfplan"
            runner.run(
                "plan",
                [
                    *command,
                    "plan",
                    "-input=false",
                    "-refresh=false",
                    "-lock=false",
                    "-no-color",
                    "-detailed-exitcode",
                    "-out=" + str(plan),
                    "-var=stack_name=" + stack,
                    "-var=docker_host=" + LOCAL_DOCKER,
                ],
                allowed=(2,),
            )
            shown = runner.run("plan-json", [*command, "show", "-json", str(plan)])
            document = json.loads(shown.stdout)
            write_json(output / "plan.json", document)
            expected = {
                "docker_network.private": stack + "-private",
                "docker_volume.app_data": stack + "-app-data",
                "docker_volume.temporal_data": stack + "-temporal-data",
            }
            changes = document.get("resource_changes", [])
            if {item["address"] for item in changes} != set(expected):
                raise RuntimeError("Plan includes an unexpected resource set")
            for item in changes:
                change = item["change"]
                if (
                    item["mode"] != "managed"
                    or change["actions"] != ["create"]
                    or change["after"]["name"] != expected[item["address"]]
                ):
                    raise RuntimeError("Plan contains a non-isolated or non-create change")
                if item["address"] == "docker_network.private" and not change["after"]["internal"]:
                    raise RuntimeError("Planned network is not private")
            runner.resource_absence(stack, "after-plan")
            metadata.update(
                status="passed",
                planned_creates=len(changes),
                plan_sha256=sha256(plan),
                isolated_resources_absent_after_plan=True,
            )
    except Exception as exc:
        metadata.update(status="failed", exception_type=type(exc).__name__, reason=str(exc))
    finally:
        metadata["source_unchanged"] = all(
            sha256(ROOT / name) == digest for name, digest in hashes.items()
        )
        if not metadata["source_unchanged"]:
            metadata["status"] = "failed"
        metadata["finished_at"] = datetime.now(UTC).isoformat()
        write_json(output / "run.json", metadata)
    print(
        json.dumps(
            {
                "status": metadata["status"],
                "gate": metadata["gate"],
                "terraform_apply_executed": False,
                "output": str(output),
            }
        ),
        flush=True,
    )
    raise SystemExit(0 if metadata["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
