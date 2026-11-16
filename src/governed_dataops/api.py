"""Authenticated operator API. Temporal owns execution; the API signs human decisions."""

import asyncio
import json
import secrets
import sqlite3
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from importlib.resources import files
from typing import Annotated, Literal
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.exceptions import WorkflowAlreadyStartedError

from governed_dataops.contracts import (
    Approval,
    Contract,
    Evidence,
    Incident,
    Plan,
    Principal,
    Scenario,
)
from governed_dataops.policy import evaluate_plan
from governed_dataops.routing import queue_for_target
from governed_dataops.settings import Settings, get_settings
from governed_dataops.signing import sign_approval
from governed_dataops.storage import TERMINAL_STATUSES, CapacityExceeded, Store


def workflow_id(incident_id: str) -> str:
    return f"dataops-{incident_id}"


class Submission(Contract):
    incident: Incident
    mode: Literal["agent", "runbook"] = "agent"
    simulate_lost_response: bool = False


class ApprovalRequest(Contract):
    plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    ttl_seconds: int = Field(default=300, ge=1, le=900)


class DemoRequest(Contract):
    scenario: Scenario
    mode: Literal["agent", "runbook"] = "agent"
    simulate_lost_response: bool = False
    inject_log: bool = False
    variant: int = Field(default=0, ge=0, le=9)


def create_app(
    settings: Settings | None = None, store: Store | None = None, temporal=None
) -> FastAPI:
    config = settings or get_settings()
    database = store or Store(config.db_path, config.approval_verify_key_file)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.temporal = temporal or await asyncio.wait_for(
            Client.connect(
                config.temporal_address,
                namespace=config.temporal_namespace,
                data_converter=pydantic_data_converter,
            ),
            timeout=10,
        )
        yield

    app = FastAPI(title="Governed DataOps", version="0.1.0a1", lifespan=lifespan)
    app.state.store = database
    app.state.settings = config

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self'; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    def authenticate(authorization: Annotated[str | None, Header()] = None) -> Principal:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "A role token is required")
        value = authorization[7:]
        for role in ("operator", "approver", "reader", "executor"):
            token = getattr(config, f"{role}_token")
            if token and secrets.compare_digest(value.encode("utf-8"), token.encode("utf-8")):
                return config.principal(role)
        raise HTTPException(401, "Invalid role token")

    def scoped_record(identifier: str, principal: Principal) -> dict:
        try:
            record = database.get_incident(identifier)
        except KeyError:
            raise HTTPException(404, "Incident not found") from None
        if (record["environment"], record["scope"]) != (principal.environment, principal.scope):
            raise HTTPException(403, "Incident scope is not authorized")
        return record

    def role_is(principal: Principal, role: str) -> None:
        if principal.role != role:
            raise HTTPException(403, f"This operation requires the {role} role")

    @app.exception_handler(sqlite3.OperationalError)
    async def storage_unavailable(_request, _exception):
        return JSONResponse(
            status_code=503,
            content={"detail": "Persistence unavailable; retry the same event"},
            headers={"Retry-After": "5"},
        )

    @app.get("/health")
    async def health():
        try:
            healthy = await asyncio.wait_for(
                app.state.temporal.service_client.check_health(), timeout=2
            )
            if not healthy:
                raise RuntimeError("Temporal is not serving")
            return {"status": "ok", "workflow": "temporal", "persistence": "sqlite-wal"}
        except Exception:
            return JSONResponse(
                status_code=503, content={"status": "unavailable", "workflow": "temporal"}
            )

    @app.get("/api/catalogue")
    def catalogue(_principal: Annotated[Principal, Depends(authenticate)]):
        return json.loads(files("governed_dataops").joinpath("catalogue-v1.json").read_text())

    async def submit(body: Submission, principal: Principal) -> dict:
        role_is(principal, "operator")
        incident = body.incident
        if (incident.environment, incident.scope) != (principal.environment, principal.scope):
            raise HTTPException(403, "Incident is outside the operator scope")
        if body.simulate_lost_response and not config.demo_mode:
            raise HTTPException(403, "Response-loss injection requires demo mode")
        intent = {"mode": body.mode, "simulate_lost_response": body.simulate_lost_response}
        assigned_queue = queue_for_target(
            config.task_queue, config.partition_count, incident.target_id
        )
        if config.partition_count > 1:
            # Durable immutable route is claimed in the same admission transaction.
            intent["task_queue"] = assigned_queue
        try:
            created = database.record_incident(
                incident,
                config.max_pending_incidents,
                intent=intent,
                partition_capacity=config.partition_admission_limit,
            )
        except CapacityExceeded:
            raise HTTPException(
                429, "Incident admission capacity reached", headers={"Retry-After": "5"}
            ) from None
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None
        record = database.get_incident(incident.incident_id)
        identifier = workflow_id(incident.incident_id)
        if record["status"] not in TERMINAL_STATUSES:
            try:
                await app.state.temporal.start_workflow(
                    "IncidentWorkflow",
                    {
                        "incident": record["incident"],
                        **intent,
                        "approval_timeout_seconds": config.approval_timeout_seconds,
                    },
                    id=identifier,
                    task_queue=assigned_queue,
                    id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                    execution_timeout=timedelta(seconds=config.approval_timeout_seconds + 900),
                    rpc_timeout=timedelta(seconds=10),
                )
            except WorkflowAlreadyStartedError:
                pass
            except Exception:
                database.event(
                    incident.incident_id,
                    "dispatch_pending",
                    {"reason": "Temporal start acknowledgement unavailable; retry the same event"},
                )
                raise HTTPException(
                    503,
                    "Workflow dispatch is pending; retry the same event",
                    headers={"Retry-After": "5"},
                ) from None
        return {
            "incident_id": incident.incident_id,
            "workflow_id": identifier,
            "deduplicated": not created,
            "task_queue": assigned_queue,
        }

    @app.post("/api/incidents", status_code=202)
    async def create_incident(
        body: Submission, principal: Annotated[Principal, Depends(authenticate)]
    ):
        return await submit(body, principal)

    @app.post("/api/demo/incidents", status_code=202)
    async def create_demo(
        body: DemoRequest, principal: Annotated[Principal, Depends(authenticate)]
    ):
        role_is(principal, "operator")
        if not config.demo_mode or config.environment != "dev" or body.scenario == Scenario.UNKNOWN:
            raise HTTPException(403, "Synthetic fixture generation requires the dev demo profile")
        identifier = uuid4().hex[:20]
        target_id = f"line-{identifier}"
        database.seed_target(
            target_id,
            body.scenario,
            principal.environment,
            principal.scope,
            body.inject_log,
            body.variant,
        )
        incident = Incident(
            incident_id=f"inc-{identifier}",
            event_id=f"evt-{identifier}",
            target_id=target_id,
            environment=principal.environment,
            scope=principal.scope,
            symptom="Industrial data batch requires investigation",
        )
        return await submit(
            Submission(
                incident=incident,
                mode=body.mode,
                simulate_lost_response=body.simulate_lost_response,
            ),
            principal,
        )

    @app.get("/api/incidents")
    def list_incidents(principal: Annotated[Principal, Depends(authenticate)]):
        return database.list_incidents(
            256, environment=principal.environment, scope=principal.scope
        )

    @app.get("/api/incidents/{incident_id}")
    async def get_incident(
        incident_id: str, principal: Annotated[Principal, Depends(authenticate)]
    ):
        record = scoped_record(incident_id, principal)
        if record["status"] not in TERMINAL_STATUSES:
            try:
                status = await app.state.temporal.get_workflow_handle(
                    workflow_id(incident_id)
                ).query("status", rpc_timeout=timedelta(seconds=2))
                record["workflow_status"] = status
            except Exception:
                record["workflow_status"] = {"available": False, "source": "durable projection"}
        return record

    @app.post("/api/incidents/{incident_id}/approval", status_code=202)
    async def approve(
        incident_id: str,
        body: ApprovalRequest,
        principal: Annotated[Principal, Depends(authenticate)],
    ):
        role_is(principal, "approver")
        record = scoped_record(incident_id, principal)
        if record["status"] in TERMINAL_STATUSES or not record.get("plan"):
            raise HTTPException(409, "Incident does not have an approvable pending plan")
        if record["status"] not in {
            "awaiting_approval",
            "approval_invalid",
            "approval_delivery_pending",
            "approval_submitted",
        }:
            raise HTTPException(409, "The workflow has not requested approval")
        plan = Plan.model_validate(record["plan"])
        if body.plan_hash != plan.digest():
            raise HTTPException(409, "Displayed plan no longer matches the approval request")
        # No worker query is needed: the persisted awaiting projection identifies
        # the reviewed plan. Fresh target state remains mandatory.
        try:
            async with httpx.AsyncClient(
                trust_env=False, follow_redirects=False, timeout=config.target_timeout_seconds
            ) as client:
                response = await client.get(
                    f"{config.target_url}/targets/{plan.target_id}",
                    headers={"Authorization": f"Bearer {config.reader_token}"},
                )
                response.raise_for_status()
                evidence = Evidence.model_validate(response.json())
        except Exception:
            raise HTTPException(
                503, "Fresh target evidence is unavailable; approval was not issued"
            ) from None
        decision = evaluate_plan(plan, evidence.snapshot, config.principal("executor"))
        if (
            not evidence.complete
            or evidence.snapshot.target_id != plan.target_id
            or not decision.approval_required
        ):
            raise HTTPException(409, "Approval preconditions changed or evidence is incomplete")
        now = datetime.now(UTC)
        existing = record.get("approval")
        reusable = None
        if existing and record["status"] in {"approval_delivery_pending", "approval_submitted"}:
            candidate = Approval.model_validate(existing)
            if (
                candidate.plan_hash == plan.digest()
                and candidate.approver == principal
                and datetime.fromisoformat(candidate.expires_at) > now
            ):
                reusable = candidate
        if reusable:
            approval = reusable
        else:
            if not config.approval_signing_key_file:
                raise HTTPException(503, "Approval signing identity is not configured")
            approval = Approval(
                plan_hash=plan.digest(),
                incident_id=incident_id,
                target_id=plan.target_id,
                environment=plan.environment,
                scope=plan.scope,
                expected_revision=plan.expected_revision,
                policy_version=plan.policy_version,
                approver=principal,
                issued_at=now.isoformat(),
                expires_at=(now + timedelta(seconds=body.ttl_seconds)).isoformat(),
            )
            approval = sign_approval(approval, config.approval_signing_key_file)
            database.save_approval(approval)
        envelope = approval.model_dump(mode="json")
        database.event(
            incident_id,
            "approval_delivery_pending",
            {"approval": envelope, "plan_hash": plan.digest()},
        )
        try:
            await asyncio.wait_for(
                app.state.temporal.get_workflow_handle(workflow_id(incident_id)).signal(
                    "approve", envelope
                ),
                timeout=10,
            )
        except Exception:
            raise HTTPException(
                503,
                "Approval delivery acknowledgement unavailable; retry the same plan",
                headers={"Retry-After": "5"},
            ) from None
        database.event(
            incident_id, "approval_submitted", {"approval": envelope, "plan_hash": plan.digest()}
        )
        return {
            "incident_id": incident_id,
            "plan_hash": plan.digest(),
            "expires_at": approval.expires_at,
            "delivery": "submitted",
        }

    @app.post("/api/incidents/{incident_id}/cancel", status_code=202)
    async def cancel(incident_id: str, principal: Annotated[Principal, Depends(authenticate)]):
        role_is(principal, "operator")
        record = scoped_record(incident_id, principal)
        if record["status"] in TERMINAL_STATUSES:
            raise HTTPException(409, "The incident is already terminal")
        try:
            await asyncio.wait_for(
                app.state.temporal.get_workflow_handle(workflow_id(incident_id)).signal("cancel"),
                timeout=10,
            )
        except Exception:
            raise HTTPException(503, "Cancellation acknowledgement unavailable; retry") from None
        database.event(incident_id, "cancellation_requested", {"requested_by": principal.subject})
        return {"incident_id": incident_id, "cancellation_requested": True}

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics(principal: Annotated[Principal, Depends(authenticate)]):
        counts = database.incident_counts(principal.environment, principal.scope)
        lines = ["# TYPE dataops_incidents gauge"]
        lines.extend(
            f'dataops_incidents{{state="{state}"}} {count}'
            for state, count in sorted(counts.items())
        )
        lines.extend(
            [
                f"dataops_admission_limit {config.max_pending_incidents}",
                f"dataops_worker_configured_slots {config.worker_concurrency}",
                f"dataops_model_configured_slots {config.model_concurrency}",
            ]
        )
        return "\n".join(lines) + "\n"

    static = files("governed_dataops").joinpath("static")
    app.mount("/static", StaticFiles(directory=str(static)), name="static")

    @app.get("/", include_in_schema=False)
    def console():
        return FileResponse(str(static.joinpath("index.html")))

    return app
