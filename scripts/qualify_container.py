#!/usr/bin/env python3
"""Build and exercise the real private Compose stack on the local Docker daemon.

Every invocation creates its own named synthetic volumes, networks and credentials.
Cleanup removes only those resources. No mock service or external inference is used.
The platform gate and the one-case diagnostic result are reported separately.
"""

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DOCKER = "unix:///var/run/docker.sock"
TERMINAL = {"resolved", "contained", "denied", "escalated", "cancelled"}
EXPECTED = {
    "freshness": ("resolved", "refresh_partition"),
    "transient": ("resolved", "retry_batch"),
    "schema": ("denied", "apply_schema_migration"),
    "quality": ("contained", "quarantine_batch"),
    "duplicate": ("resolved", "suppress_duplicate"),
}

TARGET_AUDIT = """
import json, os, sqlite3, sys
with sqlite3.connect('file:' + os.environ['DATAOPS_DB_PATH'] + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    target = sys.argv[1]
    state = dict(db.execute('SELECT * FROM targets WHERE target_id=?', (target,)).fetchone())
    rows = {name: [dict(row) for row in db.execute(
        f'SELECT row_id,amount FROM {name} WHERE target_id=? ORDER BY row_id', (target,))]
        for name in ('source_rows', 'curated_rows', 'quarantine_rows')}
    receipts = [dict(row) for row in db.execute(
        'SELECT idempotency_key,incident_id,plan_hash,result_json FROM effect_ledger WHERE target_id=?',
        (target,))]
    print(json.dumps({'target': state, 'rows': rows, 'receipts': receipts}))
"""

HISTORY_AUDIT = """
import asyncio, json, os, sys
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
async def main():
    client = await Client.connect(os.environ['DATAOPS_TEMPORAL_ADDRESS'],
                                  data_converter=pydantic_data_converter)
    handle = client.get_workflow_handle(sys.argv[1])
    result = await asyncio.wait_for(handle.result(), timeout=30)
    history = await asyncio.wait_for(handle.fetch_history(), timeout=20)
    print(json.dumps({'result': result, 'history': json.loads(history.to_json())}))
asyncio.run(main())
"""

BACKUP_PAIR = """
import hashlib, json, pathlib, sqlite3
from contextlib import closing
out = pathlib.Path('/backup')
manifest = {'scope': 'stopped application and Temporal pair', 'files': {}}
for name, source in [('dataops.db', '/data/dataops.db'), ('temporal.db', '/temporal/temporal.db')]:
    destination = out / name
    if destination.exists():
        raise RuntimeError('backup destination already exists')
    with closing(sqlite3.connect('file:' + source + '?mode=ro', uri=True)) as src:
        with closing(sqlite3.connect(destination)) as dst:
            src.backup(dst)
            if dst.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                raise RuntimeError('backup integrity check failed')
    destination.chmod(0o600)
    with destination.open('rb') as stream:
        manifest['files'][name] = hashlib.file_digest(stream, 'sha256').hexdigest()
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest))
"""

RESTORE_PAIR = """
import hashlib, json, pathlib, shutil, sqlite3
root = pathlib.Path('/backup')
manifest = json.loads((root / 'manifest.json').read_text())
for name, target in [('dataops.db', '/data/dataops.db'), ('temporal.db', '/temporal/temporal.db')]:
    source, destination = root / name, pathlib.Path(target)
    if destination.exists():
        raise RuntimeError('restore destination is not empty')
    with source.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != manifest['files'][name]:
            raise RuntimeError('backup digest mismatch')
    with source.open('rb') as src, destination.open('xb') as dst:
        shutil.copyfileobj(src, dst)
    destination.chmod(0o600)
    with sqlite3.connect('file:' + str(destination) + '?mode=ro', uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise RuntimeError('restored integrity check failed')
print(json.dumps({'restored_pair': True, 'integrity': 'ok'}))
"""


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, default=str) + "\n")


def model_latency_report(
    trace: dict | None,
    *,
    gate_wall_seconds: float,
    admission_http_seconds: float | None,
    workflow_poll_seconds: float | None,
    stack_startup_seconds: float | None,
    model_cpu_quota: float | None,
    failure_type: str | None,
) -> dict:
    """Bounded observability: missing segments remain null, never inferred.

    The diagnostic trace covers the entire PydanticAI call including response
    validation; the Docker stack startup covers *all* services, not the model
    alone. Neither can be silently re-labelled as isolated inference latency.
    """
    def duration(value):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            return None
        return round(float(value), 6)

    data = trace if isinstance(trace, dict) else {}
    observed = data.get("response_observed")
    valid = data.get("diagnosis_valid")
    return {
        "status": "incomplete" if failure_type else "observed",
        "failure_type": failure_type,
        "response_observed": observed if isinstance(observed, bool) else None,
        "diagnosis_valid": valid if isinstance(valid, bool) else None,
        "model_cpu_quota": model_cpu_quota,
        "segments_seconds": {
            "stack_startup_all_services": duration(stack_startup_seconds),
            "model_only_startup_readiness": None,
            "client_model_slot_wait": duration(data.get("client_model_slot_wait_seconds")),
            "server_internal_queue_wait": None,
            "api_admission_http": duration(admission_http_seconds),
            "workflow_poll_until_terminal_or_failure": duration(workflow_poll_seconds),
            "diagnostic_call_including_validation": duration(data.get("duration_seconds")),
            "agent_run_including_native_output_validation": duration(
                data.get("agent_run_seconds")
            ),
            "typed_business_validation": duration(
                data.get("typed_business_validation_seconds")
            ),
            "inference_only": None,
            "semantic_validation_only": None,
            "full_agent_gate": duration(gate_wall_seconds),
        },
        "limits": [
            "Null stages were not observed and must not be treated as zero latency.",
            "Stack startup includes Temporal, target, API, workers and model.",
            "Client slot wait excludes model-server internal queuing.",
            "Diagnostic call duration includes transport, generation and validation.",
            "No deadline, retry, model, prompt or outcome policy is altered.",
        ],
    }


def source_manifest() -> dict:
    paths = [
        ROOT / name
        for name in (
            "Dockerfile",
            "Dockerfile.model",
            "Dockerfile.temporal",
            "compose.yaml",
            ".dockerignore",
            "README.md",
            "pyproject.toml",
            "uv.lock",
        )
    ]
    for folder in ("src", "scripts"):
        paths.extend(
            p
            for p in (ROOT / folder).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        )
    contents = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)
    }
    tracked = set(subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines())
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT).returncode == 0
    return {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "tracked_and_clean": set(contents) <= tracked and clean,
        "files": contents,
    }


class ContainerQualification:
    def __init__(self, output: Path, workspace: Path, args):
        self.output, self.workspace, self.args = output, workspace, args
        self.prefix = "gda-qualification-" + uuid4().hex[:12]
        self.stack = self.prefix
        self.stacks = []
        self.images = []
        self.tokens = {}
        self.records = []
        self.checks = []
        self.command_index = 0
        self.client = httpx.Client(
            base_url="http://127.0.0.1:8080", timeout=20, trust_env=False, follow_redirects=False
        )
        self.env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("DATAOPS_", "COMPOSE_", "DOCKER_"))
        }
        self.env.update(DATAOPS_UID=str(os.getuid()), DATAOPS_GID=str(os.getgid()))
        self.override = workspace / "secrets-override.json"

    def execute(
        self, argv: list[str], label: str, *, timeout=120, check=True
    ) -> subprocess.CompletedProcess:
        command_started = time.monotonic()
        if argv[0] == "docker":
            argv = ["docker", "--host", LOCAL_DOCKER, *argv[1:]]
        self.command_index += 1
        log = self.output / f"{self.command_index:03d}-{label}.log"
        print(json.dumps({"command": label, "stack": self.stack, "state": "running"}), flush=True)
        environment = {**self.env, "DATAOPS_STACK": self.stack}
        process = subprocess.Popen(
            argv,
            cwd=ROOT,
            env=environment,
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
        result = subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
        log.write_text(stdout)
        error_log = log.with_suffix(".stderr.log")
        error_log.write_text(result.stderr)
        self.records.append(
            {
                "label": label,
                "argv": argv,
                "exit_code": result.returncode,
                "stdout_log": log.name,
                "stderr_log": error_log.name,
                "stack": self.stack,
                "timed_out": timed_out,
                "seconds": round(time.monotonic() - command_started, 6),
            }
        )
        write_json(self.output / "commands.json", self.records)
        if timed_out:
            raise TimeoutError(f"{label} exceeded {timeout}s; original stdout/stderr retained")
        if check and result.returncode:
            raise RuntimeError(f"{label} failed with exit {result.returncode}; see {log.name}")
        return result

    def compose(self, args: list[str], label: str, **kwargs) -> subprocess.CompletedProcess:
        return self.execute(
            [
                "docker",
                "compose",
                "--project-name",
                self.stack,
                "--env-file",
                "/dev/null",
                "-f",
                str(ROOT / "compose.yaml"),
                "-f",
                str(self.override),
                *args,
            ],
            label,
            **kwargs,
        )

    def check(self, name: str, function) -> dict:
        started = time.monotonic()
        try:
            detail = function()
            result = {"name": name, "passed": True, "detail": detail}
        except Exception as exc:
            result = {
                "name": name,
                "passed": False,
                "exception_type": type(exc).__name__,
                "reason": str(exc),
            }
        result["seconds"] = round(time.monotonic() - started, 3)
        self.checks.append(result)
        write_json(self.output / "checks.json", self.checks)
        print(json.dumps({k: v for k, v in result.items() if k != "detail"}), flush=True)
        return result

    def initialize(self) -> None:
        if os.getuid() == 0:
            raise RuntimeError(
                "Use a non-root deployment account; file-backed secret ownership is required"
            )
        if shutil.which("docker") is None:
            raise RuntimeError(
                "Docker CLI/daemon is unavailable; container execution is unverified"
            )
        fields = (
            "ServerVersion",
            "OperatingSystem",
            "Architecture",
            "NCPU",
            "MemTotal",
            "SecurityOptions",
        )
        template = "{" + ",".join('"' + key + '":{{json .' + key + "}}" for key in fields) + "}"
        info = json.loads(
            self.execute(["docker", "info", "--format", template], "docker-info").stdout
        )
        write_json(
            self.output / "docker-host.json",
            {
                key: info.get(key)
                for key in (
                    "ServerVersion",
                    "OperatingSystem",
                    "Architecture",
                    "NCPU",
                    "MemTotal",
                    "SecurityOptions",
                )
            },
        )
        self.execute(
            [
                sys.executable,
                "-m",
                "governed_dataops.cli",
                "init",
                "--directory",
                str(self.workspace),
            ],
            "initialize-private-credentials",
        )
        secret_dir = self.workspace / ".secrets"
        names = [f"{role}-token" for role in ("reader", "executor", "operator", "approver")]
        names += ["approval-private.pem", "approval-public.pem"]
        self.images = [
            self.prefix + suffix for suffix in ("-app:test", "-model:test", "-temporal:test")
        ]
        override = {
            "secrets": {name: {"file": str(secret_dir / name)} for name in names},
            "services": {
                **{
                    service: {"image": self.images[0]}
                    for service in ("api", "worker", "target", "init-state")
                },
                "model": {"image": self.images[1]},
                "temporal": {"image": self.images[2]},
            },
        }
        if self.args.model_cpus is not None:
            override["services"]["model"]["cpus"] = self.args.model_cpus
        write_json(self.override, override)
        self.tokens = {
            role: (secret_dir / f"{role}-token").read_text().strip()
            for role in ("reader", "executor", "operator", "approver")
        }
        self.compose(["config", "--format", "json"], "resolved-compose")
        self.compose(["build"], "build-images", timeout=1800)
        self.stacks.append(self.stack)
        self.compose(["up", "-d", "--wait", "--wait-timeout", "240"], "start-stack", timeout=300)

    def request(self, method: str, path: str, *, role="operator", body=None):
        response = self.client.request(
            method, path, headers={"Authorization": "Bearer " + self.tokens[role]}, json=body
        )
        response.raise_for_status()
        return response.json()

    def inspect_isolation(self) -> dict:
        ids = self.compose(["ps", "-q"], "container-identifiers").stdout.split()
        details = json.loads(self.execute(["docker", "inspect", *ids], "inspect-containers").stdout)
        inventory = []
        expected = {
            "api": {
                "operator-token",
                "approver-token",
                "reader-token",
                "approval-private.pem",
                "approval-public.pem",
            },
            "worker": {"reader-token", "executor-token", "approval-public.pem"},
            "target": {"operator-token", "reader-token", "executor-token", "approval-public.pem"},
            "temporal": set(),
            "model": set(),
        }
        api_id = None
        for item in details:
            service = item["Config"]["Labels"]["com.docker.compose.service"]
            if service not in expected:
                continue
            config, host = item["Config"], item["HostConfig"]
            assert config["User"] == f"{os.getuid()}:{os.getgid()}"
            assert host["ReadonlyRootfs"]
            assert host["Memory"] > 0 and host["NanoCpus"] > 0 and host["PidsLimit"] > 0
            secrets_mounted = {
                Path(m["Destination"]).name
                for m in item["Mounts"]
                if m["Destination"].startswith("/run/secrets/")
            }
            assert secrets_mounted == expected[service], (service, secrets_mounted)
            assert all(
                not m["RW"] for m in item["Mounts"] if m["Destination"].startswith("/run/secrets/")
            )
            environment_keys = {value.split("=", 1)[0] for value in config["Env"]}
            assert not any(
                key.startswith("DATAOPS_") and key.endswith("_TOKEN") for key in environment_keys
            )
            if service != "api":
                assert "DATAOPS_APPROVAL_SIGNING_KEY_FILE" not in environment_keys
            bindings = host["PortBindings"] or {}
            actual_ports = item["NetworkSettings"]["Ports"] or {}
            networks = set(item["NetworkSettings"]["Networks"])
            if service == "api":
                expected_bindings = {"8080/tcp": [{"HostIp": "127.0.0.1", "HostPort": "8080"}]}
                assert bindings == expected_bindings
                # Configured bindings alone did not establish an actual listener
                # on an internal-only Docker network. Check realized mappings too.
                assert {key: value for key, value in actual_ports.items() if value} == expected_bindings
                assert networks == {self.stack + "-private", self.stack + "-ingress"}
                api_id = item["Id"]
            else:
                assert not bindings
                assert not any(actual_ports.values())
                assert networks == {self.stack + "-private"}
            inventory.append(
                {
                    "service": service,
                    "image_id": item["Image"],
                    "user": config["User"],
                    "read_only_root": True,
                    "secret_mounts": sorted(secrets_mounted),
                    "port_bindings": bindings,
                    "actual_published_ports": actual_ports,
                    "networks": sorted(networks),
                    "memory_limit_bytes": host["Memory"],
                    "cpu_limit": host["NanoCpus"] / 1e9,
                }
            )
        assert {item["service"] for item in inventory} == set(expected)
        network = json.loads(
            self.execute(
                ["docker", "network", "inspect", self.stack + "-private"], "inspect-private-network"
            ).stdout
        )[0]
        assert network["Internal"] is True
        ingress = json.loads(
            self.execute(
                ["docker", "network", "inspect", self.stack + "-ingress"], "inspect-ingress-network"
            ).stdout
        )[0]
        assert ingress["Internal"] is False
        assert ingress["Options"]["com.docker.network.bridge.host_binding_ipv4"] == "127.0.0.1"
        assert set(ingress["Containers"]) == {api_id}
        health = self.client.get("/health")
        health.raise_for_status()
        probe = self.compose(
            [
                "exec",
                "-T",
                "worker",
                "python",
                "-c",
                "from pathlib import Path; assert not Path('/run/secrets/approval-private.pem').exists(); print('private signing key absent')",
            ],
            "worker-signing-key-absence",
        )
        write_json(self.output / "container-inventory.json", inventory)
        return {
            "containers": inventory,
            "internal_network": True,
            "ingress_attached_only_to_api": True,
            "host_loopback_health_status": health.status_code,
            "api_egress_blocked": False,
            "worker_key_probe": probe.stdout.strip(),
        }

    def asset_identity(self) -> dict:
        code = (
            "import hashlib,json; from pathlib import Path; "
            "manifest=json.loads(Path('/models/provenance.json').read_text()); "
            "asset=manifest['assets'][-1]; "
            "stream=Path('/models/model.gguf').open('rb'); "
            "observed=hashlib.file_digest(stream,'sha256').hexdigest(); stream.close(); "
            "assert observed==asset['sha256']; "
            "assert Path('/models/model.gguf').stat().st_size==asset['bytes']; "
            "print(json.dumps({'selected_asset':asset,'actual_sha256':observed}))"
        )
        model = json.loads(
            self.compose(
                ["exec", "-T", "model", "python", "-c", code],
                "installed-weight-identity",
                timeout=120,
            ).stdout
        )
        self.compose(
            ["exec", "-T", "model", "/opt/llama/llama-server", "--version"], "llama-version"
        )
        self.compose(
            ["exec", "-T", "temporal", "/opt/temporal/temporal", "--version"], "temporal-version"
        )
        inventory = self.compose(
            [
                "exec",
                "-T",
                "api",
                "python",
                "-c",
                "import importlib.metadata,json; print(json.dumps({n:importlib.metadata.version(n) for n in ['governed-dataops-agents','mcp','pydantic-ai-slim','temporalio','pydantic']}))",
            ],
            "installed-python-versions",
        )
        return {"model": model, "packages": json.loads(inventory.stdout)}

    def audit(self, target_id: str) -> dict:
        observed = self.compose(
            ["exec", "-T", "target", "python", "-c", TARGET_AUDIT, target_id],
            "target-business-audit",
        )
        return json.loads(observed.stdout)

    def history(self, incident_id: str) -> dict:
        observed = self.compose(
            ["exec", "-T", "worker", "python", "-c", HISTORY_AUDIT, "dataops-" + incident_id],
            "temporal-history",
            timeout=75,
        )
        result = json.loads(observed.stdout)
        write_json(self.output / f"history-{incident_id}-{self.stack}.json", result)
        return result

    def submit(self, scenario: str, *, mode="runbook", lost=False) -> str:
        return self.request(
            "POST",
            "/api/demo/incidents",
            body={
                "scenario": scenario,
                "mode": mode,
                "simulate_lost_response": lost,
                "inject_log": True,
            },
        )["incident_id"]

    def complete(self, incident_id: str) -> dict:
        deadline, approved = time.monotonic() + 300, False
        while time.monotonic() < deadline:
            record = self.request("GET", "/api/incidents/" + incident_id, role="reader")
            write_json(self.output / f"trace-{incident_id}.json", record)
            if record["status"] in TERMINAL:
                self.history(incident_id)
                return record
            if (
                record["status"] in {"awaiting_approval", "approval_delivery_pending"}
                and not approved
            ):
                self.request(
                    "POST",
                    f"/api/incidents/{incident_id}/approval",
                    role="approver",
                    body={"plan_hash": record["plan_hash"], "ttl_seconds": 120},
                )
                approved = True
            time.sleep(0.5)
        raise TimeoutError(f"Incident {incident_id} did not complete within 300 seconds")

    @staticmethod
    def assert_business(scenario: str, record: dict, business: dict) -> None:
        outcome, action = EXPECTED[scenario]
        assert record["status"] == outcome
        assert record["diagnosis"]["category"] == scenario
        assert record["diagnosis"]["proposed_action"] == action
        target, rows, receipts = business["target"], business["rows"], business["receipts"]
        if scenario == "schema":
            assert not receipts and target["revision"] == 0
            assert not rows["curated_rows"] and not rows["quarantine_rows"]
            return
        assert len(receipts) == 1 and target["revision"] == 1
        assert record["verification"]["outcome"] == outcome
        if scenario == "quality":
            assert target["batch_status"] == "quarantined" and not rows["curated_rows"]
            assert rows["source_rows"] == rows["quarantine_rows"]
            assert any(e["phase"] == "approval_submitted" for e in record["events"])
        else:
            assert rows["source_rows"] == rows["curated_rows"] and not rows["quarantine_rows"]
            assert record["verification"]["resolved"]
            assert target["pending_delivery"] == 0

    def run_case(self, scenario: str) -> dict:
        incident = self.submit(scenario, lost=scenario == "transient")
        record = self.complete(incident)
        business = self.audit(record["target_id"])
        write_json(self.output / f"business-{incident}.json", business)
        self.assert_business(scenario, record, business)
        if scenario == "transient":
            phases = {event["phase"] for event in record["events"]}
            assert {"effect_uncertain", "effect_reconciled"} <= phases
        return {
            "incident_id": incident,
            "target_id": record["target_id"],
            "outcome": record["status"],
            "effect_count": len(business["receipts"]),
            "mode": "runbook",
        }

    def worker_restart(self) -> dict:
        self.compose(["stop", "-t", "45", "worker"], "stop-worker", timeout=65)
        try:
            incident = self.submit("freshness")
            waiting = self.request("GET", "/api/incidents/" + incident, role="reader")
            assert waiting["status"] not in TERMINAL
        finally:
            self.compose(["start", "worker"], "restart-worker")
        result = self.complete(incident)
        business = self.audit(result["target_id"])
        self.assert_business("freshness", result, business)
        return {"incident_id": incident, "queued_during_worker_stop": True, "effect_count": 1}

    def paired_restore(self, reference: str) -> dict:
        record = self.request("GET", "/api/incidents/" + reference, role="reader")
        before = self.audit(record["target_id"])
        historical = self.history(reference)
        self.compose(
            ["stop", "-t", "45", "api", "worker", "target"], "stop-application-writers", timeout=90
        )
        self.compose(["stop", "-t", "45", "temporal"], "stop-temporal-writer", timeout=65)
        backup = self.workspace / "backup"
        backup.mkdir(mode=0o700)
        user = f"{os.getuid()}:{os.getgid()}"
        receipt = self.compose(
            [
                "run",
                "--rm",
                "--no-deps",
                "-T",
                "--user",
                user,
                "-v",
                f"{backup}:/backup",
                "--entrypoint",
                "python",
                "init-state",
                "-c",
                BACKUP_PAIR,
            ],
            "backup-pair",
        )
        backup_manifest = json.loads(receipt.stdout)
        self.compose(["stop", "-t", "45"], "stop-original-stack", timeout=90)
        self.stack = self.prefix + "-restore"
        self.stacks.append(self.stack)
        self.compose(["run", "--rm", "init-state"], "initialize-fresh-restore-volumes")
        self.compose(
            [
                "run",
                "--rm",
                "--no-deps",
                "-T",
                "--user",
                user,
                "-v",
                f"{backup}:/backup:ro",
                "--entrypoint",
                "python",
                "init-state",
                "-c",
                RESTORE_PAIR,
            ],
            "restore-pair",
        )
        self.compose(
            ["up", "-d", "--wait", "--wait-timeout", "240"], "start-restored-stack", timeout=300
        )
        self.client.close()
        self.client = httpx.Client(
            base_url="http://127.0.0.1:8080", timeout=20, trust_env=False, follow_redirects=False
        )
        after = self.audit(record["target_id"])
        restored_history = self.history(reference)
        assert before == after
        assert historical == restored_history
        repeated = self.request(
            "POST", "/api/incidents", body={"incident": record["incident"], "mode": "runbook"}
        )
        assert repeated["deduplicated"]
        assert self.audit(record["target_id"]) == after
        fresh = self.run_case("freshness")
        return {
            "backup_manifest": backup_manifest,
            "historical_incident": reference,
            "history_and_rows_equal": True,
            "duplicate_effect_count": 1,
            "new_incident_after_restore": fresh["incident_id"],
            "secrets_restored_from_database": False,
        }

    def agent_case(self) -> dict:
        # Record partial stages on both success and failure. The real diagnostic
        # timeout and all business-effect assertions remain unchanged.
        started = time.monotonic()
        incident = None
        record = None
        trace = None
        admission_seconds = None
        poll_started = None
        poll_seconds = None
        failure_type = None
        try:
            sent_at = time.monotonic()
            incident = self.submit("freshness", mode="agent")
            admission_seconds = time.monotonic() - sent_at
            poll_started = time.monotonic()
            record = self.complete(incident)
            poll_seconds = time.monotonic() - poll_started
            traces = [
                event["payload"]["model_trace"]
                for event in record["events"]
                if "model_trace" in event["payload"]
            ]
            if not traces:
                raise AssertionError("No model trace was recorded for the container agent call")
            trace = traces[-1]
            observed = trace.get("response_observed", False)
            result = {
                "incident_id": incident,
                "mode": "agent",
                "outcome": record["status"],
                "response_observed": observed,
                "quality_passed": False,
                "trace": trace,
            }
            business = self.audit(record["target_id"])
            write_json(self.output / f"business-{incident}.json", business)
            try:
                self.assert_business("freshness", record, business)
                result["quality_passed"] = True
            except (AssertionError, KeyError) as exc:
                result["quality_failure"] = type(exc).__name__
            # Semantic model disagreement never relaxes target-effect correctness.
            assert len(business["receipts"]) <= 1
            if business["receipts"]:
                assert record["plan"]["actions"][0]["tool"] == "refresh_partition"
                assert business["target"]["revision"] == 1
                assert business["rows"]["source_rows"] == business["rows"]["curated_rows"]
                assert not business["rows"]["quarantine_rows"]
            else:
                assert business["target"]["revision"] == 0
                assert not business["rows"]["curated_rows"] and not business["rows"]["quarantine_rows"]
            assert trace.get("provider") == "local" and trace.get("request_attempted") and observed
            # Only publish a positive semantic report after all effect assertions.
            write_json(self.output / "model-quality.json", result)
            return result
        except Exception as exc:
            failure_type = type(exc).__name__
            if poll_started is not None and poll_seconds is None:
                poll_seconds = time.monotonic() - poll_started
            if incident is not None and record is None:
                # Best-effort durable projection; the original exception still
                # propagates and the gate cannot be marked as passed.
                try:
                    record = self.request("GET", "/api/incidents/" + incident, role="reader")
                except Exception:
                    pass
            if isinstance(record, dict) and trace is None:
                traces = [
                    event.get("payload", {}).get("model_trace")
                    for event in record.get("events", [])
                    if isinstance(event.get("payload", {}).get("model_trace"), dict)
                ]
                trace = traces[-1] if traces else None
            if not (self.output / "model-quality.json").exists():
                write_json(
                    self.output / "model-quality.json",
                    {
                        "incident_id": incident,
                        "mode": "agent",
                        "status": "incomplete",
                        "quality_assessed": False,
                        "quality_passed": False,
                        "failure_type": failure_type,
                        "trace": trace,
                    },
                )
            raise
        finally:
            startup = next(
                (item.get("seconds") for item in reversed(self.records)
                 if item["label"] == "start-stack"),
                None,
            )
            write_json(
                self.output / "model-latency.json",
                model_latency_report(
                    trace,
                    gate_wall_seconds=time.monotonic() - started,
                    admission_http_seconds=admission_seconds,
                    workflow_poll_seconds=poll_seconds,
                    stack_startup_seconds=startup,
                    model_cpu_quota=self.args.model_cpus,
                    failure_type=failure_type,
                ),
            )

    def cleanup(self) -> list[dict]:
        results = []
        for stack in reversed(self.stacks):
            self.stack = stack
            inspection_errors = []
            for command, name in [
                (["logs", "--no-color"], "service-logs"),
                (["ps", "--format", "json"], "final-service-state"),
            ]:
                try:
                    self.compose(command, name, check=False)
                except Exception as exc:
                    inspection_errors.append(type(exc).__name__)
            try:
                stopped = self.compose(
                    ["down", "--volumes", "--remove-orphans", "--timeout", "45"],
                    "remove-owned-synthetic-stack",
                    timeout=180,
                    check=False,
                )
                containers = self.execute(
                    [
                        "docker",
                        "ps",
                        "-aq",
                        "--filter",
                        "label=com.docker.compose.project=" + stack,
                    ],
                    "verify-no-owned-containers",
                )
                networks = self.execute(
                    [
                        "docker",
                        "network",
                        "ls",
                        "--filter",
                        "label=com.docker.compose.project=" + stack,
                        "--format",
                        "{{.Name}}",
                    ],
                    "verify-owned-network-removal",
                )
                volumes = self.execute(
                    [
                        "docker",
                        "volume",
                        "ls",
                        "--filter",
                        "label=com.docker.compose.project=" + stack,
                        "--format",
                        "{{.Name}}",
                    ],
                    "verify-owned-volume-removal",
                )
                removed = (
                    stopped.returncode == 0
                    and not containers.stdout.strip()
                    and not networks.stdout.strip()
                    and not {stack + "-app-data", stack + "-temporal-data"}
                    & set(volumes.stdout.splitlines())
                )
                results.append(
                    {"stack": stack, "removed": removed, "inspection_errors": inspection_errors}
                )
            except Exception as exc:
                results.append({"stack": stack, "removed": False, "reason": type(exc).__name__})
        if self.images:
            try:
                self.execute(
                    ["docker", "image", "rm", *self.images], "remove-owned-image-tags", check=False
                )
            except Exception:
                # Shared build-cache layers are deliberately not pruned.
                pass
        self.client.close()
        return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument(
        "--model-cpus", type=float, help="Explicit CI CPU quota override; recorded in the proof"
    )
    parser.add_argument("--require-model-quality", action="store_true")
    args = parser.parse_args()
    if args.model_cpus is not None and not 0.5 <= args.model_cpus <= 4:
        parser.error("--model-cpus must be between 0.5 and 4")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    initial = source_manifest()
    metadata = {
        "started_at": datetime.now(UTC).isoformat(),
        "gate": "container_execution",
        "source": initial,
        "platform": platform.platform(),
        "docker_host": LOCAL_DOCKER,
        "status": "running",
        "model_cpu_override": args.model_cpus,
        "full_acceptance_claimed": False,
        "require_model_quality": args.require_model_quality,
    }
    write_json(output / "run.json", metadata)
    with tempfile.TemporaryDirectory(prefix="dataops-container-") as temporary:
        suite = ContainerQualification(output, Path(temporary), args)
        try:
            if args.source_commit and (
                initial["commit"] != args.source_commit or not initial["tracked_and_clean"]
            ):
                raise RuntimeError(
                    "Requested source commit does not match clean tracked source files"
                )
            suite.initialize()
            suite.check("container_network_credentials_and_limits", suite.inspect_isolation)
            suite.check("installed_runtime_asset_identity", suite.asset_identity)
            cases = [
                suite.check("runbook_" + scenario, lambda s=scenario: suite.run_case(s))
                for scenario in EXPECTED
            ]
            suite.check("durable_work_after_worker_restart", suite.worker_restart)
            first = cases[0]
            if first["passed"]:
                suite.check(
                    "paired_container_database_restore",
                    lambda: suite.paired_restore(first["detail"]["incident_id"]),
                )
            else:
                suite.checks.append(
                    {
                        "name": "paired_container_database_restore",
                        "passed": False,
                        "execution_status": "not_executed",
                        "reason": "Freshness reference case failed",
                    }
                )
                write_json(output / "checks.json", suite.checks)
            model = suite.check("real_local_model_response", suite.agent_case)
            quality = model.get("detail", {}).get("quality_passed", False)
            metadata["diagnostic_quality_passed"] = quality
            metadata["status"] = (
                "passed"
                if all(c["passed"] for c in suite.checks)
                and (quality or not args.require_model_quality)
                else "failed"
            )
        except Exception as exc:
            metadata.update(status="failed", exception_type=type(exc).__name__, reason=str(exc))
        finally:
            cleanup = suite.cleanup()
            write_json(output / "cleanup.json", cleanup)
            if not all(item["removed"] for item in cleanup):
                metadata["status"] = "failed"
            final = source_manifest()
            metadata["source_unchanged"] = initial["files"] == final["files"]
            if not metadata["source_unchanged"]:
                metadata["status"] = "failed"
            # Check only generated evidence; secrets remain in the private temporary workspace.
            leaked = []
            for path in output.iterdir():
                if path.is_file():
                    content = path.read_bytes()
                    if (
                        any(token.encode() in content for token in suite.tokens.values())
                        or b"-----BEGIN PRIVATE KEY-----" in content
                    ):
                        leaked.append(path.name)
            metadata["credential_scan"] = {"passed": not leaked, "blocked_artifacts": leaked}
            if leaked:
                # Do not leave a secret-bearing artifact available to an unconditional CI upload.
                for name in leaked:
                    (output / name).unlink()
                metadata["status"] = "failed"
            metadata["checks"] = [{"name": c["name"], "passed": c["passed"]} for c in suite.checks]
            metadata["finished_at"] = datetime.now(UTC).isoformat()
            write_json(output / "run.json", metadata)
    print(
        json.dumps(
            {
                "status": metadata["status"],
                "gate": metadata["gate"],
                "diagnostic_quality_passed": metadata.get("diagnostic_quality_passed"),
                "output": str(output),
            }
        ),
        flush=True,
    )
    raise SystemExit(0 if metadata["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
