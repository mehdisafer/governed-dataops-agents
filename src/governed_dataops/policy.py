"""Independent deterministic authorization and freshly observed business postconditions."""

from datetime import UTC, datetime

from governed_dataops.contracts import (
    CATALOG_VERSION,
    POLICY_VERSION,
    Approval,
    Evidence,
    Plan,
    PolicyDecision,
    Principal,
    Snapshot,
    ToolName,
    Verification,
)

MAX_APPROVAL_SECONDS = 900
FRESHNESS_OBJECTIVE_SECONDS = 300


def _time(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamp must have a timezone")
    return result.astimezone(UTC)


def evaluate_plan(
    plan: Plan,
    snapshot: Snapshot,
    executor: Principal,
    approval: Approval | None = None,
    now: datetime | str | None = None,
) -> PolicyDecision:
    reasons: list[str] = []
    if executor.role != "executor":
        reasons.append("principal is not an executor")
    if (plan.target_id, plan.environment, plan.scope) != (
        snapshot.target_id,
        snapshot.environment,
        snapshot.scope,
    ):
        reasons.append("plan target or scope does not match live state")
    if (executor.environment, executor.scope) != (plan.environment, plan.scope):
        reasons.append("executor environment or scope is not authorized")
    if plan.expected_revision != snapshot.revision:
        reasons.append("precondition revision changed")
    if plan.catalog_version != CATALOG_VERSION:
        reasons.append("unsupported catalogue version")
    if plan.policy_version != snapshot.policy_version or snapshot.policy_version != POLICY_VERSION:
        reasons.append("policy changed or is unsupported")
    if len(plan.actions) != 1 or plan.action_budget != 1:
        reasons.append("catalogue v1 permits exactly one action per incident")
    if len(plan.actions) > plan.action_budget:
        reasons.append("action budget exceeded")
    if plan.delegation_depth > 1:
        reasons.append("delegation depth exceeded")
    tool = plan.actions[0].tool
    if tool in (ToolName.MIGRATE, ToolName.ESCALATE):
        reasons.append("operation requires human engineering; no executable permission exists")
    elif snapshot.source_schema != snapshot.accepted_schema:
        reasons.append("incompatible schema prevents automated mutation")
    elif tool == ToolName.REFRESH:
        if not (
            snapshot.freshness_lag_seconds > FRESHNESS_OBJECTIVE_SECONDS
            and snapshot.backlog_rows > 0
            and snapshot.batch_status == "pending"
            and snapshot.rejected_rows == 0
            and snapshot.curated_rows == 0
            and snapshot.duplicate_rows == 0
            and not snapshot.transient_failure
        ):
            reasons.append("refresh preconditions are not met")
    elif tool == ToolName.RETRY:
        if not (
            snapshot.transient_failure
            and snapshot.batch_status == "failed"
            and snapshot.backlog_rows > 0
            and snapshot.rejected_rows == 0
            and snapshot.curated_rows == 0
            and snapshot.duplicate_rows == 0
        ):
            reasons.append("transient retry preconditions are not met")
    elif tool == ToolName.QUARANTINE:
        if not (
            snapshot.rejected_rows > 0
            and snapshot.batch_status == "rejected"
            and snapshot.curated_rows == 0
            and snapshot.duplicate_rows == 0
        ):
            reasons.append("quality quarantine preconditions are not met")
    elif tool == ToolName.SUPPRESS:
        if not (
            snapshot.batch_status == "applied"
            and snapshot.curated_rows > 0
            and snapshot.backlog_rows > 0
            and snapshot.duplicate_rows == 0
        ):
            reasons.append("duplicate suppression preconditions are not met")
    else:
        reasons.append("operation is not in the executable catalogue")
    if reasons:
        return PolicyDecision(allowed=False, reasons=reasons)
    required = tool == ToolName.QUARANTINE or plan.environment == "prod"
    if not required and approval is None:
        return PolicyDecision(allowed=True, reasons=["catalogue operation authorized"])
    if approval is None:
        return PolicyDecision(allowed=False, approval_required=True, reasons=["approval required"])
    bindings = (
        (approval.plan_hash, plan.digest(), "plan hash"),
        (approval.incident_id, plan.incident_id, "incident"),
        (approval.target_id, plan.target_id, "target"),
        (approval.environment, plan.environment, "environment"),
        (approval.scope, plan.scope, "scope"),
        (approval.expected_revision, plan.expected_revision, "revision"),
        (approval.policy_version, plan.policy_version, "policy"),
    )
    reasons.extend(
        f"approval {label} mismatch" for actual, expected, label in bindings if actual != expected
    )
    if approval.approver.role != "approver":
        reasons.append("approval identity is not an approver")
    if approval.approver.subject == executor.subject:
        reasons.append("executor cannot approve its own action")
    if (approval.approver.environment, approval.approver.scope) != (plan.environment, plan.scope):
        reasons.append("approver environment or scope is not authorized")
    try:
        instant = _time(now) if isinstance(now, str) else (now or datetime.now(UTC))
        if instant.tzinfo is None:
            raise ValueError("time must have a timezone")
        issued, expires = _time(approval.issued_at), _time(approval.expires_at)
        if issued > instant:
            reasons.append("approval issued in the future")
        if expires <= instant:
            reasons.append("approval expired")
        duration = (expires - issued).total_seconds()
        if duration <= 0 or duration > MAX_APPROVAL_SECONDS:
            reasons.append("approval validity exceeds the permitted duration")
    except (TypeError, ValueError):
        reasons.append("invalid approval timestamps")
    return PolicyDecision(
        allowed=not reasons,
        approval_required=required,
        reasons=reasons or ["bound approval and catalogue operation authorized"],
    )


def verify_effect(plan: Plan, evidence: Evidence) -> Verification:
    state, reasons = evidence.snapshot, []
    if not evidence.complete:
        reasons.append("postcondition evidence is incomplete")
    if (state.target_id, state.environment, state.scope) != (
        plan.target_id,
        plan.environment,
        plan.scope,
    ):
        reasons.append("postcondition evidence target mismatch")
    if state.revision != plan.expected_revision + 1:
        reasons.append("postcondition revision does not identify the expected single effect")
    if state.policy_version != plan.policy_version:
        reasons.append("policy changed before verification")
    tool, outcome = plan.actions[0].tool, "resolved"
    if tool in (ToolName.REFRESH, ToolName.RETRY):
        if not (
            state.batch_status == "applied"
            and state.backlog_rows == 0
            and state.curated_rows > 0
            and state.rejected_rows == 0
            and state.duplicate_rows == 0
            and not state.transient_failure
            and state.source_schema == state.accepted_schema
            and state.freshness_lag_seconds <= FRESHNESS_OBJECTIVE_SECONDS
        ):
            reasons.append("the batch is not successfully loaded within the freshness objective")
    elif tool == ToolName.QUARANTINE:
        outcome = "contained"
        if not (
            state.batch_status == "quarantined"
            and state.backlog_rows == 0
            and state.rejected_rows == 0
            and state.curated_rows == 0
        ):
            reasons.append("the rejected batch is not fully isolated from curated data")
    elif tool == ToolName.SUPPRESS:
        if not (
            state.batch_status == "suppressed"
            and state.backlog_rows == 0
            and state.duplicate_rows == 0
            and state.curated_rows > 0
        ):
            reasons.append("duplicate delivery remains possible or curated rows are missing")
    else:
        reasons.append("no automatic resolution postcondition exists for this operation")
    if reasons:
        return Verification(resolved=False, outcome="escalated", reasons=reasons, snapshot=state)
    return Verification(
        resolved=outcome == "resolved",
        outcome=outcome,
        reasons=["freshly read business postconditions hold"],
        snapshot=state,
    )
