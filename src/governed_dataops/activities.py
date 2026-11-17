"""Temporal activities own model calls, authorization reads and external effects."""

import asyncio
import time

from temporalio import activity
from temporalio.exceptions import ApplicationError

from governed_dataops.contracts import (
    Approval,
    EffectRequest,
    EffectResult,
    Evidence,
    Incident,
    Plan,
    PolicyDecision,
    Verification,
    build_plan,
    effect_key,
)
from governed_dataops.diagnostic import (
    DiagnosticError,
    diagnose,
    runbook_diagnose,
    sanitized_evidence,
    validate_evidence,
)
from governed_dataops.mcp_client import MCPGateway
from governed_dataops.policy import evaluate_plan, verify_effect
from governed_dataops.routing import queue_for_target, queue_for_worker
from governed_dataops.settings import Settings, get_settings
from governed_dataops.signing import verify_approval_signature
from governed_dataops.storage import Store


class Activities:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.store = Store(self.settings.db_path, self.settings.approval_verify_key_file)
        self.store.migrate()
        self.gateway = MCPGateway(self.settings)
        self.executor = self.settings.principal("executor")
        self.model_slots = asyncio.Semaphore(self.settings.model_concurrency)

    def _assert_owned(self, target_id: str) -> None:
        if self.settings.partition_count == 1:
            return
        expected = queue_for_target(
            self.settings.task_queue, self.settings.partition_count, target_id
        )
        owner = queue_for_worker(
            self.settings.task_queue,
            self.settings.partition_count,
            self.settings.worker_partition,
        )
        if expected != owner or self.store.bound_target_queue(target_id) != owner:
            raise ApplicationError(
                "target partition is not owned by this worker or route was changed",
                type="PartitionOwnershipViolation",
                non_retryable=True,
            )

    @activity.defn(name="dataops.collect")
    async def collect(self, request: dict) -> dict:
        incident = Incident.model_validate(request["incident"])
        self._assert_owned(incident.target_id)
        self.store.record_incident(incident)
        evidence = await self.gateway.collect(incident.target_id)
        self.store.event(
            incident.incident_id,
            "collected",
            {"evidence": sanitized_evidence(evidence).model_dump(mode="json")},
        )
        try:
            validate_evidence(incident, evidence)
        except DiagnosticError as exc:
            raise ApplicationError(
                str(exc), type="InsufficientEvidence", non_retryable=True
            ) from None
        return {"evidence": evidence.model_dump(mode="json")}

    @activity.defn(name="dataops.diagnose")
    async def diagnose(self, request: dict) -> dict:
        incident = Incident.model_validate(request["incident"])
        self._assert_owned(incident.target_id)
        evidence = Evidence.model_validate(request["evidence"])
        mode = request.get("mode", "agent")
        try:
            if mode == "runbook":
                diagnosis, trace = runbook_diagnose(incident, evidence)
            elif mode == "agent":
                slot_wait_started = time.monotonic()
                try:
                    await asyncio.wait_for(self.model_slots.acquire(), timeout=10)
                except TimeoutError:
                    raise DiagnosticError(
                        "model capacity exhausted; no unbounded queue or provider fallback",
                        trace={
                            "client_model_slot_wait_seconds": round(
                                time.monotonic() - slot_wait_started, 6
                            ),
                            "client_model_slot_acquired": False,
                        },
                    ) from None
                slot_wait_seconds = round(time.monotonic() - slot_wait_started, 6)
                try:
                    diagnosis, trace = await diagnose(incident, evidence, self.settings)
                    trace["client_model_slot_wait_seconds"] = slot_wait_seconds
                    trace["client_model_slot_acquired"] = True
                except DiagnosticError as exc:
                    exc.trace["client_model_slot_wait_seconds"] = slot_wait_seconds
                    exc.trace["client_model_slot_acquired"] = True
                    raise
                finally:
                    self.model_slots.release()
            else:
                raise DiagnosticError("unsupported diagnostic mode")
            plan = build_plan(incident, evidence, diagnosis)
        except (DiagnosticError, ValueError) as exc:
            self.store.event(
                incident.incident_id,
                "diagnostic_failed",
                {"reason": str(exc), "model_trace": getattr(exc, "trace", {}), "mode": mode},
            )
            raise ApplicationError(
                str(exc), type="DiagnosticUnavailable", non_retryable=True
            ) from None
        self.store.event(
            incident.incident_id,
            "diagnosed",
            {"diagnosis": diagnosis.model_dump(mode="json"), "model_trace": trace},
        )
        return {
            "diagnosis": diagnosis.model_dump(mode="json"),
            "plan": plan.model_dump(mode="json"),
        }

    @activity.defn(name="dataops.authorize")
    async def authorize(self, request: dict) -> dict:
        plan = Plan.model_validate(request["plan"])
        self._assert_owned(plan.target_id)
        approval = Approval.model_validate(request["approval"]) if request.get("approval") else None
        current = await self.gateway.collect(plan.target_id)
        if not current.complete:
            decision = PolicyDecision(
                allowed=False, reasons=["live authorization evidence is incomplete"]
            )
        elif approval is not None and (
            not self.store.approval_exists(approval)
            or not verify_approval_signature(approval, self.settings.approval_verify_key_file)
        ):
            decision = PolicyDecision(
                allowed=False,
                approval_required=True,
                reasons=["approval has no signed authenticated durable record"],
            )
        else:
            decision = evaluate_plan(plan, current.snapshot, self.executor, approval)
        self.store.event(
            plan.incident_id,
            "policy_checked",
            {
                "policy": decision.model_dump(mode="json"),
                "plan_hash": plan.digest(),
                "observed_revision": current.snapshot.revision,
                "approval": approval.model_dump(mode="json") if approval else None,
            },
        )
        return decision.model_dump(mode="json")

    @activity.defn(name="dataops.execute")
    async def execute(self, request: dict) -> dict:
        plan = Plan.model_validate(request["plan"])
        self._assert_owned(plan.target_id)
        index = int(request.get("action_index", 0))
        approval = Approval.model_validate(request["approval"]) if request.get("approval") else None
        key = effect_key(plan, index)
        # FIRST on every attempt, including worker recovery. A durable receipt
        # takes precedence over a plan revision made stale by its own effect.
        receipt = await self.gateway.reconcile(key, plan.target_id)
        if receipt.status != "not_found":
            self.store.event(
                plan.incident_id, "effect_reconciled", {"effect": receipt.model_dump(mode="json")}
            )
            return receipt.model_dump(mode="json")
        current = await self.gateway.collect(plan.target_id)
        decision = evaluate_plan(plan, current.snapshot, self.executor, approval)
        if not current.complete:
            decision = PolicyDecision(allowed=False, reasons=["execution evidence is incomplete"])
        if approval is not None and (
            not self.store.approval_exists(approval)
            or not verify_approval_signature(approval, self.settings.approval_verify_key_file)
        ):
            decision = PolicyDecision(
                allowed=False, reasons=["approval is not durably authenticated"]
            )
        if not decision.allowed:
            result = EffectResult(
                idempotency_key=key,
                status="denied",
                message="; ".join(decision.reasons),
                snapshot=current.snapshot,
            )
            self.store.event(
                plan.incident_id,
                "execution_denied",
                {
                    "effect": result.model_dump(mode="json"),
                    "policy": decision.model_dump(mode="json"),
                },
            )
            return result.model_dump(mode="json")
        effect_request = EffectRequest(
            idempotency_key=key,
            plan=plan,
            action_index=index,
            executor=self.executor,
            approval=approval,
            simulate_lost_response=bool(request.get("simulate_lost_response", False)),
        )
        self.store.event(
            plan.incident_id, "dispatching", {"plan_hash": plan.digest(), "idempotency_key": key}
        )
        result = await self.gateway.execute(effect_request)
        if result.status == "unknown":
            self.store.event(
                plan.incident_id, "effect_uncertain", {"effect": result.model_dump(mode="json")}
            )
            reconciled = await self.gateway.reconcile(key, plan.target_id)
            if reconciled.status in {"applied", "denied"}:
                result = reconciled
            else:
                result = EffectResult(
                    idempotency_key=key,
                    status="unknown",
                    reconciled=True,
                    message="uncertain remote effect remains unproven after reconciliation; human intervention required",
                )
        phase = "effect_reconciled" if result.reconciled else "executed"
        self.store.event(plan.incident_id, phase, {"effect": result.model_dump(mode="json")})
        return result.model_dump(mode="json")

    @activity.defn(name="dataops.verify")
    async def verify(self, request: dict) -> dict:
        plan = Plan.model_validate(request["plan"])
        self._assert_owned(plan.target_id)
        effect = EffectResult.model_validate(request["effect"])
        if effect.status != "applied":
            verification = Verification(
                resolved=False,
                outcome="denied" if effect.status == "denied" else "escalated",
                reasons=[effect.message],
                snapshot=effect.snapshot,
            )
        else:
            evidence = await self.gateway.collect(plan.target_id)
            verification = verify_effect(plan, evidence)
            if effect.after_revision != evidence.snapshot.revision:
                verification = Verification(
                    resolved=False,
                    outcome="escalated",
                    snapshot=evidence.snapshot,
                    reasons=["effect receipt and current business revision do not agree"],
                )
            self.store.event(
                plan.incident_id,
                "postcondition_observed",
                {"evidence": sanitized_evidence(evidence).model_dump(mode="json")},
            )
        self.store.event(
            plan.incident_id, "verified", {"verification": verification.model_dump(mode="json")}
        )
        return verification.model_dump(mode="json")

    @activity.defn(name="dataops.record")
    async def record(self, request: dict) -> dict:
        self._assert_owned(self.store.get_incident(request["incident_id"])["target_id"])
        self.store.event(request["incident_id"], request["phase"], request.get("payload", {}))
        return {"recorded": True}

    def registered(self) -> list:
        return [self.collect, self.diagnose, self.authorize, self.execute, self.verify, self.record]
