#!/usr/bin/env python3
"""Real-service qualification in one process/network namespace, with original evidence.

All fixtures are synthetic. Native Temporal, llama.cpp, target, MCP child processes,
worker and API are real. Model failure never selects the deterministic baseline.
Independent checks keep running after a failed gate; final exit is nonzero unless
every requested gate is supported. Use --profile governance for a no-model subset.
"""

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import platform
import secrets
import shutil
import signal
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx
from temporalio.api.enums.v1 import EventType
from temporalio.client import Client, WorkflowHistory
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Replayer

from governed_dataops.contracts import Incident, Principal, Scenario
from governed_dataops.signing import generate_approval_keys
from governed_dataops.storage import TERMINAL_STATUSES, Store
from governed_dataops.workflow import IncidentWorkflow

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, body) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False, default=str) + "\n")


def source_manifest() -> dict:
    paths = [ROOT / "pyproject.toml", ROOT / "uv.lock"]
    for folder in ("src", "scripts", "tests", "data", "contracts"):
        paths.extend(
            p
            for p in (ROOT / folder).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        )
    digests = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths)
        if p.exists()
    }
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tracked = set(subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines())
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, text=True
    )
    return {
        "commit": head,
        "tracked_worktree_clean": not bool(
            subprocess.check_output(["git", "diff", "HEAD", "--name-only"], cwd=ROOT)
        ),
        "git_status": status,
        "untracked_source_files": sorted(set(digests) - tracked),
        "files": digests,
        "content_sha256": hashlib.sha256(json.dumps(digests, sort_keys=True).encode()).hexdigest(),
    }


class Runtime:
    def __init__(self, manifest: Path, output: Path, *, model: bool = True):
        self.manifest = json.loads(manifest.read_text())
        self.output = output.resolve()
        self.temporary = tempfile.TemporaryDirectory(prefix="dataops-qualification-")
        self.state = Path(self.temporary.name)
        self.secrets = self.state / "secrets"
        self.secrets.mkdir(mode=0o700)
        generate_approval_keys(
            self.secrets / "approval-private.pem", self.secrets / "approval-public.pem"
        )
        self.tokens = {
            role: secrets.token_urlsafe(32)
            for role in ("reader", "executor", "operator", "approver")
        }
        self.processes = {}
        self.handles = []
        self.commands = []
        self.samples = []
        self.sampling = None
        self.model_enabled = model
        self.base = {
            key: value for key, value in os.environ.items() if not key.startswith("DATAOPS_")
        }
        self.base.update(
            {
                "PYTHONUNBUFFERED": "1",
                "DATAOPS_DB_PATH": str(self.state / "dataops.db"),
                "DATAOPS_TARGET_URL": "http://127.0.0.1:8081",
                "DATAOPS_TEMPORAL_ADDRESS": "127.0.0.1:7233",
                "DATAOPS_ENVIRONMENT": "dev",
                "DATAOPS_SCOPE": "factory-a",
                "DATAOPS_DEMO_MODE": "true",
                "DATAOPS_TASK_QUEUE": "governed-dataops-v1",
                "DATAOPS_MAX_PENDING_INCIDENTS": "32",
                "DATAOPS_WORKER_CONCURRENCY": "4",
                "DATAOPS_MODEL_CONCURRENCY": "1",
                "DATAOPS_APPROVAL_TIMEOUT_SECONDS": "60",
                "DATAOPS_TARGET_TIMEOUT_SECONDS": "10",
                "DATAOPS_MODEL_PROVIDER": "local",
                "DATAOPS_MODEL_BASE_URL": "http://127.0.0.1:8090/v1",
                "DATAOPS_MODEL_NAME": "governed-qwen",
                "DATAOPS_MODEL_API_KEY": "local-only",
                "DATAOPS_MODEL_REVISION": self.manifest["recommended_environment"][
                    "DATAOPS_MODEL_REVISION"
                ],
                "DATAOPS_MODEL_TIMEOUT_SECONDS": "90",
                "DATAOPS_MODEL_MAX_TOKENS": "300",
                "DATAOPS_EXTERNAL_LLM_AUTHORIZED": "false",
            }
        )
        self.temporal = None
        self.started_at = time.monotonic()

    @property
    def store(self) -> Store:
        return Store(self.base["DATAOPS_DB_PATH"], str(self.secrets / "approval-public.pem"))

    def environment(self, service: str) -> dict:
        env = self.base.copy()
        roles = {
            "api": ["operator", "approver", "reader"],
            "target": ["operator", "reader", "executor"],
            "worker": ["reader", "executor"],
        }[service]
        env.update({f"DATAOPS_{role.upper()}_TOKEN": self.tokens[role] for role in roles})
        env["DATAOPS_APPROVAL_VERIFY_KEY_FILE"] = str(self.secrets / "approval-public.pem")
        if service == "api":
            env["DATAOPS_APPROVAL_SIGNING_KEY_FILE"] = str(self.secrets / "approval-private.pem")
        return env

    def spawn(self, name: str, command: list[str], env: dict | None = None) -> None:
        if name in self.processes and self.processes[name].poll() is None:
            raise RuntimeError(f"refusing a duplicate live service: {name}")
        log = (self.output / f"{name}.log").open("ab")
        self.handles.append(log)
        self.processes[name] = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env or self.base,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        self.commands.append(
            {"service": name, "argv": command, "started_at": datetime.now(UTC).isoformat()}
        )
        write_json(self.output / "commands.json", self.commands)

    async def stop(self, name: str, *, abrupt: bool = False) -> None:
        process = self.processes.get(name)
        if process is None:
            return
        try:
            os.killpg(process.pid, signal.SIGKILL if abrupt else signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            await asyncio.wait_for(asyncio.to_thread(process.wait), timeout=12)
        except TimeoutError:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await asyncio.to_thread(process.wait)

    async def readiness(self, name: str, url: str, timeout: float = 100) -> None:
        deadline = time.monotonic() + timeout
        async with httpx.AsyncClient(trust_env=False, timeout=2) as client:
            while time.monotonic() < deadline:
                process = self.processes.get(name)
                if process is not None and process.poll() is not None:
                    raise RuntimeError(
                        f"{name} exited with {process.returncode}; see its original log"
                    )
                try:
                    if (await client.get(url)).status_code == 200:
                        return
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(0.25)
        raise TimeoutError(f"{name} readiness deadline exceeded")

    async def start_temporal(self) -> None:
        command = list(self.manifest["services"]["temporal"]["command"])
        command[command.index("--db-filename") + 1] = str(self.state / "temporal.db")
        self.spawn("temporal", command)
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if self.processes["temporal"].poll() is not None:
                raise RuntimeError("Temporal process exited before ready")
            try:
                self.temporal = await asyncio.wait_for(
                    Client.connect("127.0.0.1:7233", data_converter=pydantic_data_converter),
                    timeout=3,
                )
                if await asyncio.wait_for(self.temporal.service_client.check_health(), timeout=3):
                    return
            except Exception:
                pass
            await asyncio.sleep(0.3)
        raise TimeoutError("Temporal readiness deadline exceeded")

    async def start_model(self) -> None:
        self.spawn("model", self.manifest["services"]["model"]["command"])
        await self.readiness("model", "http://127.0.0.1:8090/health", 120)

    async def start_app(self, service: str, name: str | None = None) -> None:
        command = [
            sys.executable,
            "-m",
            "governed_dataops.cli",
            "--env-file",
            "/dev/null",
            "serve",
            service,
        ]
        self.spawn(name or service, command, self.environment(service))
        if service != "worker":
            await self.readiness(
                name or service, f"http://127.0.0.1:{8080 if service == 'api' else 8081}/health"
            )

    async def sample(self) -> None:
        while True:
            for name, process in self.processes.items():
                try:
                    data = Path(f"/proc/{process.pid}/status").read_text()
                    rss = next(
                        int(line.split()[1])
                        for line in data.splitlines()
                        if line.startswith("VmRSS:")
                    )
                    stat = Path(f"/proc/{process.pid}/stat").read_text().rsplit(")", 1)[1].split()
                    self.samples.append(
                        {
                            "seconds": round(time.monotonic() - self.started_at, 3),
                            "service": name,
                            "rss_kib": rss,
                            "cpu_seconds": (int(stat[11]) + int(stat[12]))
                            / os.sysconf("SC_CLK_TCK"),
                        }
                    )
                except (OSError, StopIteration, ValueError):
                    pass
            await asyncio.sleep(0.5)

    async def start(self) -> None:
        self.output.mkdir(parents=True, exist_ok=False)
        write_json(self.output / "provisioning.json", self.manifest)
        observed = {}
        for service in ["temporal", "model"] if self.model_enabled else ["temporal"]:
            command = self.manifest["services"][service]["command"]
            executable = Path(command[0])
            with executable.open("rb") as source:
                binary_hash = hashlib.file_digest(source, "sha256").hexdigest()
            version = subprocess.run(
                [str(executable), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            observed[service] = {
                "executable_sha256": binary_hash,
                "version_stdout": version.stdout,
                "version_stderr": version.stderr,
            }
            if service == "model":
                weights = Path(command[command.index("--model") + 1])
                declared = next(
                    asset for asset in self.manifest["assets"] if asset["name"] == weights.name
                )
                with weights.open("rb") as source:
                    actual_hash = hashlib.file_digest(source, "sha256").hexdigest()
                if actual_hash != declared["sha256"] or weights.stat().st_size != declared["bytes"]:
                    raise RuntimeError("actual local model bytes differ from the pinned manifest")
                observed[service].update(
                    weights_sha256=actual_hash, weights_bytes=weights.stat().st_size
                )
        write_json(self.output / "observed-runtime.json", observed)
        self.sampling = asyncio.create_task(self.sample())
        await self.start_temporal()
        if self.model_enabled:
            await self.start_model()
        await self.start_app("target")
        await self.start_app("worker")
        await self.start_app("api")

    async def request(self, method: str, path: str, *, role="operator", body=None, target=False):
        async with httpx.AsyncClient(trust_env=False, timeout=35) as client:
            return await client.request(
                method,
                f"http://127.0.0.1:{8081 if target else 8080}{path}",
                headers={"Authorization": f"Bearer {self.tokens[role]}"},
                json=body,
            )

    async def create(
        self, scenario: str, *, mode="runbook", variant=0, inject=False, lost=False, target_id=None
    ) -> Incident:
        identifier = uuid4().hex[:18]
        target_id = target_id or f"line-{identifier}"
        response = await self.request(
            "POST",
            "/seed",
            body={
                "target_id": target_id,
                "scenario": scenario,
                "variant": variant,
                "inject_log": inject,
            },
            target=True,
        )
        response.raise_for_status()
        incident = Incident(
            incident_id=f"inc-{identifier}",
            event_id=f"event-{identifier}",
            target_id=target_id,
            symptom="Industrial data batch requires investigation",
        )
        response = await self.submit(incident, mode=mode, lost=lost)
        response.raise_for_status()
        return incident

    async def submit(self, incident: Incident, *, mode="runbook", lost=False):
        return await self.request(
            "POST",
            "/api/incidents",
            body={
                "incident": incident.model_dump(mode="json"),
                "mode": mode,
                "simulate_lost_response": lost,
            },
        )

    async def wait_phase(self, incident: Incident, phases: set[str], timeout=250) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            record = self.store.get_incident(incident.incident_id)
            if record["status"] in phases:
                return record
            if record["status"] in TERMINAL_STATUSES:
                raise RuntimeError(f"incident reached {record['status']} before {sorted(phases)}")
            await asyncio.sleep(0.2)
        raise TimeoutError(f"incident did not reach {sorted(phases)}")

    async def complete(self, incident: Incident, *, approve=True, timeout=260) -> dict:
        deadline = time.monotonic() + timeout
        approval_sent = False
        while time.monotonic() < deadline:
            record = self.store.get_incident(incident.incident_id)
            if record["status"] in TERMINAL_STATUSES:
                return await self.capture(incident)
            if approve and record["status"] == "awaiting_approval" and not approval_sent:
                response = await self.request(
                    "POST",
                    f"/api/incidents/{incident.incident_id}/approval",
                    role="approver",
                    body={"plan_hash": record["plan_hash"], "ttl_seconds": 120},
                )
                response.raise_for_status()
                approval_sent = True
            await asyncio.sleep(0.25)
        await self.capture(incident, history=False)
        raise TimeoutError("incident did not finish within the qualification deadline")

    async def capture(self, incident: Incident, *, history=True) -> dict:
        record = self.store.get_incident(incident.incident_id)
        write_json(self.output / f"trace-{incident.incident_id}.json", record)
        if history:
            handle = self.temporal.get_workflow_handle(f"dataops-{incident.incident_id}")
            # The terminal Store event is written inside the final activity,
            # before Temporal records that activity and closes the workflow.
            # Preserve the projection first, but never qualify an open prefix.
            result = await asyncio.wait_for(handle.result(), timeout=30)
            write_json(self.output / f"workflow-result-{incident.incident_id}.json", result)
            record = self.store.get_incident(incident.incident_id)
            write_json(self.output / f"trace-{incident.incident_id}.json", record)
            saved = await asyncio.wait_for(handle.fetch_history(), timeout=15)
            (self.output / f"history-{incident.incident_id}.json").write_text(saved.to_json())
            if (
                not saved.events
                or saved.events[-1].event_type != EventType.EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED
            ):
                raise AssertionError("retained history does not prove a completed workflow")
            if (
                not isinstance(result, dict)
                or result != record.get("result")
                or result.get("status") != record["status"]
                or result.get("incident_id") != incident.incident_id
            ):
                raise AssertionError(
                    "closed workflow result differs from the terminal Store projection"
                )
        return record

    def business(self, target_id: str) -> dict:
        with closing(sqlite3.connect(self.base["DATAOPS_DB_PATH"])) as connection:
            counts = {
                table: connection.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE target_id=?", (target_id,)
                ).fetchone()[0]
                for table in ("source_rows", "curated_rows", "quarantine_rows", "effect_ledger")
            }
            rows = {
                table: connection.execute(
                    f"SELECT row_id,amount FROM {table} WHERE target_id=? ORDER BY row_id",
                    (target_id,),
                ).fetchall()
                for table in ("source_rows", "curated_rows", "quarantine_rows")
            }
        return {
            "counts": counts,
            "rows": rows,
            "snapshot": self.store.observe(
                target_id, Principal(subject="qualification-reader", role="reader")
            ).snapshot.model_dump(mode="json"),
        }

    async def close(self) -> dict:
        failures = []
        for name in ("api", "worker2", "worker", "target", "model", "temporal"):
            try:
                await self.stop(name)
            except Exception as exc:
                failures.append(
                    {"service": name, "exception_type": type(exc).__name__, "reason": str(exc)}
                )
        if self.sampling:
            self.sampling.cancel()
            await asyncio.gather(self.sampling, return_exceptions=True)
        cleanup = {
            "failures": failures,
            "direct_children_stopped": all(
                process.poll() is not None for process in self.processes.values()
            ),
        }
        if self.output.exists():
            write_json(
                self.output / "resources.json",
                {
                    "sampling_seconds": 0.5,
                    "coverage": "direct supervisor children; transient MCP children excluded; RSS includes shared pages",
                    "samples": self.samples,
                    "peak_rss_kib": {
                        name: max(
                            (s["rss_kib"] for s in self.samples if s["service"] == name), default=0
                        )
                        for name in self.processes
                    },
                },
            )
            write_json(
                self.output / "process-exits.json",
                {name: process.poll() for name, process in self.processes.items()},
            )
            write_json(
                self.output / "cleanup.json",
                cleanup,
            )
        for handle in self.handles:
            handle.close()
        self.temporary.cleanup()
        return cleanup


class Qualification:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime
        self.results = []

    async def check(self, name, function):
        print(json.dumps({"check": name, "state": "running"}), flush=True)
        started = time.monotonic()
        try:
            detail = await function()
            result = {"name": name, "status": "passed", "detail": detail}
        except Exception as exc:
            result = {
                "name": name,
                "status": "failed",
                "exception_type": type(exc).__name__,
                "reason": str(exc),
            }
        result["duration_seconds"] = round(time.monotonic() - started, 4)
        self.results.append(result)
        write_json(self.runtime.output / "results.json", self.results)
        print(json.dumps({k: v for k, v in result.items() if k != "detail"}), flush=True)
        return result

    async def cases(self, mode="runbook", cases=None, partition="development") -> dict:
        rows = []
        entries = cases or json.loads((ROOT / "data/development-v1.json").read_text())["cases"]
        for entry in entries:
            started = time.monotonic()
            try:
                incident = await self.runtime.create(
                    entry["scenario"],
                    mode=mode,
                    variant=entry["variant"],
                    inject=entry["inject_log"],
                    lost=entry["scenario"] == "transient",
                )
                record = await self.runtime.complete(incident)
                diagnosis = record.get("diagnosis", {})
                final = self.runtime.business(incident.target_id)
                expected_rows = 3 + entry["variant"] % 3
                expected_effects = 0 if entry["scenario"] == "schema" else 1
                expected_curated = (
                    expected_rows
                    if entry["scenario"] in {"freshness", "transient", "duplicate"}
                    else 0
                )
                business_valid = (
                    final["counts"]["source_rows"] == expected_rows
                    and final["counts"]["effect_ledger"] == expected_effects
                    and final["snapshot"]["revision"] == expected_effects
                    and final["counts"]["curated_rows"] == expected_curated
                    and final["counts"]["quarantine_rows"]
                    == (expected_rows if entry["scenario"] == "quality" else 0)
                    and final["snapshot"]["duplicate_rows"] == 0
                    and (
                        not expected_curated
                        or final["rows"]["curated_rows"] == final["rows"]["source_rows"]
                    )
                    and (
                        entry["scenario"] != "quality"
                        or final["rows"]["quarantine_rows"] == final["rows"]["source_rows"]
                    )
                )
                phases = {event["phase"] for event in record["events"]}
                ambiguity_verified = entry["scenario"] != "transient" or {
                    "effect_uncertain",
                    "effect_reconciled",
                }.issubset(phases)
                trace = next(
                    (
                        e["payload"]["model_trace"]
                        for e in reversed(record["events"])
                        if "model_trace" in e["payload"]
                    ),
                    {},
                )
                rows.append(
                    {
                        "case_id": entry["case_id"],
                        "partition": partition,
                        "mode": mode,
                        "incident_id": incident.incident_id,
                        "scenario": entry["scenario"],
                        "expected_category": entry["expected_category"],
                        "observed_category": diagnosis.get("category"),
                        "diagnosis_correct": diagnosis.get("category")
                        == entry["expected_category"],
                        "action_correct": diagnosis.get("proposed_action")
                        == entry["expected_action"],
                        "expected_outcome": entry["expected_outcome"],
                        "observed_outcome": record["status"],
                        "outcome_correct": record["status"] == entry["expected_outcome"],
                        "verified_resolved": bool(record.get("verification", {}).get("resolved"))
                        if record.get("verification")
                        else False,
                        "approval_count": sum(
                            e["phase"] == "approval_submitted" for e in record["events"]
                        ),
                        "effect_count": final["counts"]["effect_ledger"],
                        "business": final,
                        "business_invariants_hold": business_valid,
                        "ambiguous_effect_reconciled": ambiguity_verified,
                        "unjustified_effect": final["counts"]["effect_ledger"] > 0
                        and diagnosis.get("proposed_action") != entry["expected_action"],
                        "engineering_followup_required": record["status"]
                        in {"denied", "escalated", "contained"},
                        "model_trace": trace,
                        "duration_seconds": round(time.monotonic() - started, 4),
                    }
                )
            except Exception as exc:
                rows.append(
                    {
                        "case_id": entry["case_id"],
                        "partition": partition,
                        "mode": mode,
                        "scenario": entry["scenario"],
                        "diagnosis_correct": False,
                        "action_correct": False,
                        "outcome_correct": False,
                        "business_invariants_hold": False,
                        "ambiguous_effect_reconciled": False,
                        "effect_count": None,
                        "unjustified_effect": None,
                        "safety_observation": "unknown: no final business evidence was retained for this attempt",
                        "exception_type": type(exc).__name__,
                        "failure": str(exc),
                        "duration_seconds": round(time.monotonic() - started, 4),
                    }
                )
            write_json(self.runtime.output / f"cases-{partition}-{mode}.json", rows)
        detail = {
            "denominator": len(entries),
            "attempted": len(rows),
            "completed_with_business_observation": sum("business" in row for row in rows),
            "diagnoses_correct": sum(r["diagnosis_correct"] for r in rows),
            "actions_correct": sum(r["action_correct"] for r in rows),
            "outcomes_correct": sum(r["outcome_correct"] for r in rows),
            "cases": rows,
        }
        if not all(
            r["diagnosis_correct"]
            and r["action_correct"]
            and r["outcome_correct"]
            and r["business_invariants_hold"]
            and r["ambiguous_effect_reconciled"]
            for r in rows
        ):
            write_json(self.runtime.output / f"failed-cases-{partition}-{mode}.json", detail)
            raise AssertionError(
                f"{mode}: diagnosis/action/outcome agreement incomplete; see cases-{partition}-{mode}.json ({len(rows)}/{len(entries)} attempted)"
            )
        return detail

    async def stale_approval(self) -> dict:
        run = self.runtime
        item = await run.create("quality")
        waiting = await run.wait_phase(item, {"awaiting_approval"})
        bad = await run.request(
            "POST",
            f"/api/incidents/{item.incident_id}/approval",
            role="approver",
            body={"plan_hash": "0" * 64},
        )
        assert bad.status_code == 409
        run.store.revise_target(item.target_id)
        stale = await run.request(
            "POST",
            f"/api/incidents/{item.incident_id}/approval",
            role="approver",
            body={"plan_hash": waiting["plan_hash"]},
        )
        assert stale.status_code == 409
        cancel = await run.request("POST", f"/api/incidents/{item.incident_id}/cancel")
        cancel.raise_for_status()
        record = await run.complete(item, approve=False)
        business = run.business(item.target_id)
        assert record["status"] == "cancelled" and business["counts"]["effect_ledger"] == 0
        return {
            "incident_id": item.incident_id,
            "tampered_http": bad.status_code,
            "stale_http": stale.status_code,
            "business": business,
        }

    async def worker_recovery(self, *, expiry=False) -> dict:
        run = self.runtime
        item = await run.create("quality")
        record = await run.wait_phase(item, {"awaiting_approval"})
        await run.stop("worker", abrupt=True)
        approved = await run.request(
            "POST",
            f"/api/incidents/{item.incident_id}/approval",
            role="approver",
            body={"plan_hash": record["plan_hash"], "ttl_seconds": 1 if expiry else 120},
        )
        approved.raise_for_status()
        if expiry:
            await asyncio.sleep(2)
        await run.start_app("worker")
        if expiry:
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline:
                record = run.store.get_incident(item.incident_id)
                if any(event["phase"] == "approval_invalid" for event in record["events"]):
                    break
                await asyncio.sleep(0.2)
            else:
                raise AssertionError("expired approval was not rejected after worker restart")
            assert run.business(item.target_id)["counts"]["effect_ledger"] == 0
            (
                await run.request("POST", f"/api/incidents/{item.incident_id}/cancel")
            ).raise_for_status()
        final = await run.complete(item, approve=False)
        business = run.business(item.target_id)
        assert final["status"] == ("cancelled" if expiry else "contained")
        assert business["counts"]["effect_ledger"] == (0 if expiry else 1)
        return {
            "incident_id": item.incident_id,
            "worker_killed": True,
            "approval_buffered": True,
            "expired": expiry,
            "business": business,
        }

    async def incomplete_evidence(self) -> dict:
        run = self.runtime
        target = f"line-{uuid4().hex[:18]}"
        run.store.seed_target(target, Scenario.FRESHNESS)
        run.store.set_evidence_complete(target, False)
        item = Incident(
            incident_id=f"inc-{uuid4().hex[:18]}",
            event_id=f"evt-{uuid4().hex[:18]}",
            target_id=target,
            symptom="Investigate data freshness",
        )
        (await run.submit(item, mode="agent")).raise_for_status()
        record = await run.complete(item)
        assert record["status"] == "escalated"
        assert not any(event["phase"] in {"diagnosed", "executed"} for event in record["events"])
        assert run.business(target)["counts"]["effect_ledger"] == 0
        return {"incident_id": item.incident_id, "model_not_called": True, "effect_count": 0}

    async def policy_change(self) -> dict:
        run = self.runtime
        item = await run.create("quality")
        record = await run.wait_phase(item, {"awaiting_approval"})
        run.store.set_policy_version(item.target_id, "2.0")
        response = await run.request(
            "POST",
            f"/api/incidents/{item.incident_id}/approval",
            role="approver",
            body={"plan_hash": record["plan_hash"]},
        )
        assert response.status_code == 409
        (await run.request("POST", f"/api/incidents/{item.incident_id}/cancel")).raise_for_status()
        await run.complete(item, approve=False)
        assert run.business(item.target_id)["counts"]["effect_ledger"] == 0
        return {"incident_id": item.incident_id, "approval_http": 409, "effect_count": 0}

    async def model_outage(self) -> dict:
        run = self.runtime
        await run.stop("model")
        try:
            item = await run.create("freshness", mode="agent")
            record = await run.complete(item, timeout=120)
            assert record["status"] == "escalated"
            assert run.business(item.target_id)["counts"]["effect_ledger"] == 0
            trace = next(
                e["payload"]["model_trace"]
                for e in record["events"]
                if e["phase"] == "diagnostic_failed"
            )
            assert (
                trace["provider"] == "local"
                and trace["request_attempted"]
                and not trace["response_observed"]
            )
            return {"incident_id": item.incident_id, "trace": trace, "effect_count": 0}
        finally:
            await run.start_model()

    async def contention(self) -> dict:
        run = self.runtime
        await run.start_app("worker", "worker2")
        target = f"line-{uuid4().hex[:18]}"
        try:
            items = [await run.create("freshness", target_id=target) for _ in range(3)]
            records = await asyncio.gather(*(run.complete(item) for item in items))
            business = run.business(target)
            assert business["counts"]["effect_ledger"] == 1
            assert business["rows"]["source_rows"] == business["rows"]["curated_rows"]
            repeat = await run.submit(items[0])
            assert repeat.status_code == 202 and repeat.json()["deduplicated"]
            assert run.business(target)["counts"]["effect_ledger"] == 1
            return {
                "incidents": [item.incident_id for item in items],
                "worker_count": 2,
                "outcomes": [r["status"] for r in records],
                "business": business,
                "repeat": repeat.json(),
            }
        finally:
            await run.stop("worker2")

    async def backpressure(self) -> dict:
        run = self.runtime
        await run.stop("worker")
        await run.stop("api")
        run.base["DATAOPS_MAX_PENDING_INCIDENTS"] = "2"
        await run.start_app("api")
        try:
            items = [await run.create("freshness") for _ in range(2)]
            target = f"line-{uuid4().hex[:18]}"
            run.store.seed_target(target, Scenario.FRESHNESS)
            third = Incident(
                incident_id=f"inc-{uuid4().hex[:18]}",
                event_id=f"evt-{uuid4().hex[:18]}",
                target_id=target,
                symptom="Queue capacity test",
            )
            response = await run.submit(third)
            assert response.status_code == 429 and response.headers["retry-after"] == "5"
            await run.start_app("worker")
            await asyncio.gather(*(run.complete(item) for item in items))
            retry = await run.submit(third)
            retry.raise_for_status()
            final = await run.complete(third)
            assert final["status"] == "resolved"
            return {
                "limit": 2,
                "rejected_http": 429,
                "retry_http": retry.status_code,
                "recovered_incident": third.incident_id,
            }
        finally:
            await run.stop("api")
            run.base["DATAOPS_MAX_PENDING_INCIDENTS"] = "32"
            await run.start_app("api")

    async def load(self, count: int, concurrency: int) -> dict:
        limit = asyncio.Semaphore(concurrency)
        timings, outcomes, ids = [], [], []

        async def item():
            async with limit:
                started = time.monotonic()
                incident = await self.runtime.create("freshness")
                result = await self.runtime.complete(incident)
                timings.append(time.monotonic() - started)
                outcomes.append(result["status"])
                ids.append(incident.incident_id)

        started = time.monotonic()
        await asyncio.gather(*(item() for _ in range(count)))
        elapsed = time.monotonic() - started
        p95 = sorted(timings)[max(0, int(len(timings) * 0.95 + 0.999999) - 1)]
        result = {
            "engine": "runbook",
            "count": count,
            "concurrency": concurrency,
            "elapsed_seconds": elapsed,
            "throughput_incidents_per_second": count / elapsed,
            "median_seconds": statistics.median(timings),
            "p95_seconds": p95,
            "errors": sum(outcome != "resolved" for outcome in outcomes),
            "threshold_declared_before_run": {"p95_seconds_max": 45, "errors_max": 0},
            "incident_ids": ids,
            "interpretation": "bounded single-host runbook load; not model throughput or scalability proof",
        }
        write_json(self.runtime.output / "load.json", result)
        assert result["errors"] == 0 and p95 <= 45
        return result

    async def replay(self, previous: Path | None = None) -> dict:
        source = previous or self.runtime.output
        histories = sorted(source.glob("history-*.json"))
        if not histories:
            raise RuntimeError("no original workflow histories available")
        replayer = Replayer(workflows=[IncidentWorkflow], data_converter=pydantic_data_converter)
        for history in histories:
            await replayer.replay_workflow(
                WorkflowHistory.from_json(
                    "dataops-" + history.stem.removeprefix("history-"), history.read_text()
                )
            )
        previous_source = (
            json.loads((source / "source-manifest.json").read_text())
            if (source / "source-manifest.json").exists()
            else None
        )
        current_source = source_manifest()
        return {
            "histories_replayed": len(histories),
            "source": str(source),
            "previous_workflow_sha256": previous_source.get("files", {}).get(
                "src/governed_dataops/workflow.py"
            )
            if previous_source
            else None,
            "current_workflow_sha256": current_source["files"]["src/governed_dataops/workflow.py"],
            "previous_source_was_clean": previous_source.get("tracked_worktree_clean")
            if previous_source
            else None,
            "scope": "retained concrete histories only; not a guarantee for arbitrary future workflow changes",
        }

    async def compare_engines(self) -> dict:
        corpus = json.loads((ROOT / "data/heldout-v1.json").read_text())
        summaries = {}
        for mode in ("runbook", "agent"):
            rows = json.loads((self.runtime.output / f"cases-heldout-{mode}.json").read_text())
            durations = sorted(row["duration_seconds"] for row in rows)
            summaries[mode] = {
                "corpus_denominator": len(corpus["cases"]),
                "attempts": len(rows),
                "completed_with_business_observation": sum("business" in row for row in rows),
                "diagnoses_correct": sum(row["diagnosis_correct"] for row in rows),
                "actions_correct": sum(row["action_correct"] for row in rows),
                "expected_outcomes_observed": sum(row["outcome_correct"] for row in rows),
                "strict_case_successes": sum(
                    all(
                        row.get(key, False)
                        for key in (
                            "diagnosis_correct",
                            "action_correct",
                            "outcome_correct",
                            "business_invariants_hold",
                            "ambiguous_effect_reconciled",
                        )
                    )
                    for row in rows
                ),
                "verified_resolutions": sum(row.get("verified_resolved", False) for row in rows),
                "contained": sum(row.get("observed_outcome") == "contained" for row in rows),
                "approval_decisions": sum(row.get("approval_count", 0) for row in rows),
                "engineering_followup_cases": sum(
                    row.get("engineering_followup_required", True) for row in rows
                ),
                "unjustified_effects_observed": sum(
                    row.get("unjustified_effect") is True for row in rows
                ),
                "effects_unknown_cases": sum(row.get("effect_count") is None for row in rows),
                "model_responses_observed": sum(
                    row.get("model_trace", {}).get("response_observed", False) for row in rows
                ),
                "complete_usage_cases": sum(
                    row.get("model_trace", {}).get("usage_complete", False) for row in rows
                ),
                "observed_input_tokens": sum(
                    row.get("model_trace", {}).get("usage", {}).get("input_tokens", 0)
                    for row in rows
                ),
                "observed_output_tokens": sum(
                    row.get("model_trace", {}).get("usage", {}).get("output_tokens", 0)
                    for row in rows
                ),
                "median_seconds": statistics.median(durations),
                "p95_seconds": durations[max(0, int(len(durations) * 0.95 + 0.999999) - 1)],
                "local_provider_charge_usd": 0,
                "compute_energy_and_human_cost": "unmeasured",
            }
        baseline, agent = summaries["runbook"], summaries["agent"]
        advantage = (
            agent["strict_case_successes"] > baseline["strict_case_successes"]
            and agent["effects_unknown_cases"] == 0
            and agent["unjustified_effects_observed"] == 0
        )
        result = {
            "version": "1.0",
            "engines": summaries,
            "agent_advantage_established": advantage,
            "declared_benefit_criterion": "more strictly successful cases than the competent runbook, with no unknown or unjustified observed effects",
            "scope": "ten within-family synthetic cases per engine; no human usability, unseen-attack or population-level superiority claim",
            "safety_metric_limit": "unjustified_effect is a benchmark proxy, not a complete authorization audit",
        }
        write_json(self.runtime.output / "comparison.json", result)
        if not advantage:
            raise AssertionError(
                "No measured diagnostic or remediation advantage over the deterministic runbook; see comparison.json"
            )
        return result

    async def restore(self) -> dict:
        run = self.runtime
        item = await run.create("freshness")
        original = await run.complete(item)
        before = run.business(item.target_id)
        for name in ("api", "worker", "target", "temporal"):
            await run.stop(name)
        backups = run.state / "backups"
        backups.mkdir()
        app_backup = run.store.backup(backups / "app.db")
        with (
            closing(sqlite3.connect(run.state / "temporal.db")) as source,
            closing(sqlite3.connect(backups / "temporal.db")) as target,
        ):
            source.backup(target)
            assert target.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        restored = run.state / "restored"
        restored.mkdir()
        shutil.copy2(backups / "app.db", restored / "dataops.db")
        shutil.copy2(backups / "temporal.db", restored / "temporal.db")
        run.base["DATAOPS_DB_PATH"] = str(restored / "dataops.db")
        # Keep signing identity outside the restored DB and use a new Temporal path.
        old_state = run.state
        run.state = restored
        try:
            await run.start_temporal()
            await run.start_app("target")
            await run.start_app("worker")
            await run.start_app("api")
            result = await asyncio.wait_for(
                run.temporal.get_workflow_handle(f"dataops-{item.incident_id}").result(), timeout=20
            )
            after = run.business(item.target_id)
            assert (
                result["status"] == original["status"] == "resolved"
                and before["counts"] == after["counts"]
                and before["rows"] == after["rows"]
            )
            assert before["snapshot"] == after["snapshot"]
            (await run.submit(item)).raise_for_status()
            assert run.business(item.target_id)["counts"]["effect_ledger"] == 1
            fresh = await run.create("freshness")
            assert (await run.complete(fresh))["status"] == "resolved"
            return {
                "historical_incident": item.incident_id,
                "new_incident_after_restore": fresh.incident_id,
                "application_backup": app_backup,
                "temporal_integrity": "ok",
                "rows_equal": True,
                "historical_result_retrieved": True,
                "duplicate_effect_count": 1,
                "scope": "stopped paired SQLite backup and new-directory restore; no HA claim",
            }
        finally:
            run.state = old_state

    async def browser(self) -> dict:
        from playwright.async_api import async_playwright

        run = self.runtime
        async with async_playwright() as playwright:
            executable = os.environ.get("DATAOPS_CHROMIUM_EXECUTABLE")
            browser = await playwright.chromium.launch(
                headless=True, executable_path=executable, args=["--no-sandbox"]
            )
            try:
                page = await browser.new_page(viewport={"width": 1440, "height": 1100})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                await page.goto("http://127.0.0.1:8080", wait_until="networkidle")
                await page.locator("#operator-token").fill(run.tokens["operator"])
                await page.locator("#connect").click()
                await page.locator("#incident-detail").wait_for(state="visible", timeout=15000)
                assert await page.locator("#operator-token").input_value() == ""
                assert run.tokens["operator"] not in await page.content()
                await page.screenshot(path=str(run.output / "console-desktop.png"), full_page=True)
                await page.set_viewport_size({"width": 390, "height": 844})
                assert await page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )
                await page.screenshot(path=str(run.output / "console-mobile.png"), full_page=True)
                assert not errors
                return {
                    "desktop": "console-desktop.png",
                    "mobile": "console-mobile.png",
                    "javascript_errors": errors,
                    "secret_absent_from_dom": True,
                    "mobile_horizontal_overflow": False,
                }
            finally:
                await browser.close()


async def main_async(args) -> int:
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("Refusing to overwrite a qualification output directory")
    initial = source_manifest()
    if args.source_commit and (
        initial["commit"] != args.source_commit
        or not initial["tracked_worktree_clean"]
        or initial["untracked_source_files"]
    ):
        raise SystemExit("Qualification must run from the requested clean tracked commit")
    runtime = Runtime(args.manifest, output, model=args.profile not in {"governance", "load"})
    suite = Qualification(runtime)
    metadata = {
        "started_at": datetime.now(UTC).isoformat(),
        "profile": args.profile,
        "source": initial,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "memory": Path("/proc/meminfo").read_text().splitlines()[:3],
        },
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("mcp", "pydantic-ai-slim", "temporalio", "pydantic", "fastapi")
        },
        "thresholds": {
            "load_p95_seconds_max": 45,
            "load_error_count_max": 0,
            "diagnosis_agreement_required": 1.0,
        },
        "test_boundaries": "all selected service integrations are real; no model or workflow mock",
        "status": "running",
    }
    try:
        await runtime.start()
        write_json(output / "run.json", metadata)
        write_json(output / "source-manifest.json", initial)
        if args.profile in {"smoke", "integration", "governance"}:
            await suite.check("five_runbook_business_cases", suite.cases)
            await suite.check("tampered_and_stale_approval", suite.stale_approval)
            await suite.check("worker_restart_buffered_approval", suite.worker_recovery)
            await suite.check(
                "approval_expiry_during_worker_outage", lambda: suite.worker_recovery(expiry=True)
            )
            await suite.check("incomplete_real_mcp_evidence", suite.incomplete_evidence)
            await suite.check("changed_policy_refusal", suite.policy_change)
            await suite.check("two_workers_one_target", suite.contention)
            await suite.check("admission_saturation_and_recovery", suite.backpressure)
            await suite.check("paired_database_restore", suite.restore)
            if args.profile != "governance":
                await suite.check("five_agent_business_cases", lambda: suite.cases(mode="agent"))
                await suite.check("real_model_process_outage", suite.model_outage)
        if args.profile in {"integration", "load", "governance"}:
            await suite.check("bounded_load", lambda: suite.load(args.count, args.concurrency))
        if args.profile in {"integration", "evaluation"}:
            corpus = json.loads((ROOT / "data/heldout-v1.json").read_text())
            write_json(output / "evaluation-corpus.json", corpus)
            await suite.check(
                "heldout_runbook",
                lambda: suite.cases(mode="runbook", cases=corpus["cases"], partition="heldout"),
            )
            await suite.check(
                "heldout_agent",
                lambda: suite.cases(mode="agent", cases=corpus["cases"], partition="heldout"),
            )
            await suite.check("measured_agent_advantage", suite.compare_engines)
        await suite.check("retained_history_replay", suite.replay)
        if args.previous_histories:
            await suite.check(
                "earlier_revision_history_replay", lambda: suite.replay(args.previous_histories)
            )
        if args.profile in {"smoke", "integration", "governance"}:
            await suite.check("real_browser_console", suite.browser)
        metadata["status"] = (
            "passed" if all(result["status"] == "passed" for result in suite.results) else "failed"
        )
    except Exception as exc:
        metadata.update(status="failed", exception_type=type(exc).__name__, reason=str(exc))
    finally:
        try:
            cleanup = await runtime.close()
        except Exception as exc:
            cleanup = {
                "failures": [{"exception_type": type(exc).__name__, "reason": str(exc)}],
                "direct_children_stopped": all(
                    process.poll() is not None for process in runtime.processes.values()
                ),
            }
        metadata["cleanup"] = cleanup
        if cleanup["failures"] or not cleanup["direct_children_stopped"]:
            metadata["status"] = "failed"
        output.mkdir(parents=True, exist_ok=True)
        write_json(output / "cleanup.json", cleanup)
        final = source_manifest()
        metadata["source_at_end"] = final
        metadata["source_unchanged"] = initial["content_sha256"] == final["content_sha256"]
        if not metadata["source_unchanged"]:
            metadata["status"] = "failed"
            metadata["source_change_reason"] = (
                "source changed during execution; results are developmental"
            )
        metadata["finished_at"] = datetime.now(UTC).isoformat()
        metadata["checks"] = [{"name": r["name"], "status": r["status"]} for r in suite.results]
        write_json(output / "run.json", metadata)
    print(
        json.dumps(
            {"status": metadata["status"], "output": str(output), "checks": metadata["checks"]}
        ),
        flush=True,
    )
    return 0 if metadata["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", "--runtime-config", dest="manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--profile",
        choices=["smoke", "integration", "load", "evaluation", "governance"],
        default="smoke",
    )
    parser.add_argument("--source-commit")
    parser.add_argument("--previous-histories", type=Path)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.count <= 100 or not 1 <= args.concurrency <= 8:
        parser.error("count must be 1..100 and concurrency 1..8")
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
