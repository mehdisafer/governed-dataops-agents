"""One durable, bounded incident workflow. No external I/O occurs in this module."""

import hashlib
import json
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError, ApplicationError

with workflow.unsafe.imports_passed_through():
    from governed_dataops.contracts import Approval, Incident, Plan, ToolName


@workflow.defn(name="IncidentWorkflow")
class IncidentWorkflow:
    def __init__(self) -> None:
        self.phase = "received"
        self.plan: dict | None = None
        self.plan_hash: str | None = None
        self.incident_id = ""
        self._approvals: list[dict] = []
        self._seen_approvals: set[str] = set()
        self._cancelled = False
        self._overflow = False

    @workflow.query(name="status")
    def status(self) -> dict:
        return {
            "phase": self.phase,
            "plan": self.plan,
            "plan_hash": self.plan_hash,
            "cancel_requested": self._cancelled,
        }

    @workflow.signal(name="approve")
    def approve(self, approval: dict) -> None:
        canonical = json.dumps(approval, sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(canonical.encode()).hexdigest()
        if fingerprint in self._seen_approvals:
            return
        if len(self._seen_approvals) >= 3:
            self._overflow = True
        else:
            self._seen_approvals.add(fingerprint)
            self._approvals.append(approval)

    @workflow.signal(name="cancel")
    def cancel(self) -> None:
        self._cancelled = True

    async def _activity(
        self, name: str, payload: dict, *, seconds: int = 60, attempts: int = 2
    ) -> dict:
        return await workflow.execute_activity(
            f"dataops.{name}",
            payload,
            start_to_close_timeout=timedelta(seconds=seconds),
            schedule_to_close_timeout=timedelta(seconds=seconds * attempts + 15),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=5),
                maximum_attempts=attempts,
            ),
        )

    async def _phase(self, phase: str, payload: dict | None = None) -> None:
        self.phase = phase
        await self._activity(
            "record",
            {"incident_id": self.incident_id, "phase": phase, "payload": payload or {}},
            seconds=15,
        )

    async def _finish(self, status: str, reason: str, verification: dict | None = None) -> dict:
        result = {
            "incident_id": self.incident_id,
            "status": status,
            "reason": reason,
            "plan_hash": self.plan_hash,
            "verification": verification,
        }
        await self._phase(status, {"result": result, "verification": verification})
        return result

    @workflow.run
    async def run(self, request: dict) -> dict:
        workflow.patched("incident-v1")
        try:
            incident_input = request["incident"]
            if not incident_input.get("created_at"):
                raise ValueError("created_at must be supplied by the ingress boundary")
            incident = Incident.model_validate(incident_input)
        except (KeyError, ValueError, TypeError, AttributeError):
            raise ApplicationError(
                "invalid incident workflow contract",
                type="InvalidWorkflowInput",
                non_retryable=True,
            ) from None
        self.incident_id = incident.incident_id
        payload = {"incident": incident.model_dump(mode="json")}
        try:
            collected = await self._activity("collect", payload)
            if self._cancelled:
                return await self._finish(
                    "cancelled", "cancelled before diagnostic or effect dispatch"
                )
            await self._phase("diagnosing", {"mode": request.get("mode", "agent")})
            diagnosed = await self._activity(
                "diagnose",
                {**payload, **collected, "mode": request.get("mode", "agent")},
                seconds=210,
                attempts=1,
            )
            plan = Plan.model_validate(diagnosed["plan"])
            self.plan = plan.model_dump(mode="json")
            self.plan_hash = plan.digest()
            await self._phase("planned", {"plan": self.plan, "plan_hash": self.plan_hash})
            if plan.actions[0].tool == ToolName.ESCALATE:
                return await self._finish(
                    "escalated", "diagnosis abstained from an executable action"
                )
            decision = await self._activity("authorize", {"plan": self.plan})
            approval: dict | None = None
            timeout = max(1, min(3600, int(request.get("approval_timeout_seconds", 300))))
            deadline = workflow.now() + timedelta(seconds=timeout)
            attempts = 0
            while decision.get("approval_required") and not decision["allowed"]:
                if self._cancelled:
                    return await self._finish(
                        "cancelled", "cancelled while awaiting approval; no effect dispatched"
                    )
                if self._overflow or attempts >= 3:
                    return await self._finish(
                        "escalated", "approval attempts exceeded the bounded decision budget"
                    )
                await self._phase(
                    "awaiting_approval",
                    {
                        "plan": self.plan,
                        "plan_hash": self.plan_hash,
                        "policy": decision,
                        "deadline": deadline.isoformat(),
                    },
                )
                remaining = (deadline - workflow.now()).total_seconds()
                if remaining <= 0:
                    return await self._finish(
                        "escalated", "approval deadline expired; no effect dispatched"
                    )
                try:
                    await workflow.wait_condition(
                        lambda: bool(self._approvals) or self._cancelled or self._overflow,
                        timeout=remaining,
                    )
                except TimeoutError:
                    return await self._finish(
                        "escalated", "approval deadline expired; no effect dispatched"
                    )
                if self._cancelled or self._overflow:
                    continue
                attempts += 1
                raw_approval = self._approvals.pop(0)
                try:
                    approval = Approval.model_validate(raw_approval).model_dump(mode="json")
                except ValueError:
                    await self._phase(
                        "approval_invalid", {"reason": "approval envelope violates the contract"}
                    )
                    continue
                decision = await self._activity(
                    "authorize", {"plan": self.plan, "approval": approval}
                )
                if not decision["allowed"]:
                    await self._phase(
                        "approval_invalid", {"policy": decision, "plan_hash": self.plan_hash}
                    )
                    approval = None
            if not decision["allowed"]:
                return await self._finish("denied", "; ".join(decision["reasons"]))
            if self._cancelled:
                return await self._finish("cancelled", "cancelled before effect dispatch")
            await self._phase("executing", {"plan_hash": self.plan_hash})
            # Signals may be processed while the audit activity above awaits.
            if self._cancelled:
                return await self._finish("cancelled", "cancelled before effect dispatch")
            effect = await self._activity(
                "execute",
                {
                    "plan": self.plan,
                    "approval": approval,
                    "action_index": 0,
                    "simulate_lost_response": bool(request.get("simulate_lost_response", False)),
                },
                seconds=120,
            )
            await self._phase("verifying", {"idempotency_key": effect["idempotency_key"]})
            verification = await self._activity("verify", {"plan": self.plan, "effect": effect})
            reason = "; ".join(verification["reasons"])
            if self._cancelled and effect["status"] == "applied":
                reason += "; cancellation arrived after dispatch and did not roll back the observed effect"
            return await self._finish(verification["outcome"], reason, verification)
        except ActivityError as exc:
            reason = (
                str(exc.cause)
                if isinstance(exc.cause, ApplicationError)
                else "required activity failed after bounded attempts"
            )
            return await self._finish("escalated", reason)
        except (KeyError, ValueError, TypeError):
            return await self._finish(
                "escalated", "workflow received an invalid activity or decision contract"
            )
