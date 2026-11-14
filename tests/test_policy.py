from datetime import UTC, datetime, timedelta

import pytest

from governed_dataops.contracts import (
    Action,
    Approval,
    Evidence,
    Plan,
    Principal,
    Snapshot,
    ToolName,
)
from governed_dataops.policy import evaluate_plan, verify_effect

NOW = datetime(2026, 11, 13, 12, 0, tzinfo=UTC)


def state(**updates):
    values = dict(
        target_id="line-a",
        environment="dev",
        scope="factory-a",
        revision=0,
        source_schema=1,
        accepted_schema=1,
        backlog_rows=3,
        rejected_rows=0,
        curated_rows=0,
        duplicate_rows=0,
        transient_failure=False,
        freshness_lag_seconds=7200,
        batch_id="batch-a",
        batch_status="pending",
    )
    values.update(updates)
    return Snapshot(**values)


def plan(snapshot=None, tool=ToolName.REFRESH, **updates):
    snapshot = snapshot or state()
    values = dict(
        incident_id="incident-a",
        target_id=snapshot.target_id,
        environment=snapshot.environment,
        scope=snapshot.scope,
        evidence_id="evidence-a",
        expected_revision=snapshot.revision,
        policy_version=snapshot.policy_version,
        actions=[Action(tool=tool)],
        rationale="test evidence",
    )
    values.update(updates)
    return Plan(**values)


def executor(**updates):
    values = dict(subject="dataops-executor", role="executor", environment="dev", scope="factory-a")
    values.update(updates)
    return Principal(**values)


def approval(proposal, **updates):
    values = dict(
        plan_hash=proposal.digest(),
        incident_id=proposal.incident_id,
        target_id=proposal.target_id,
        environment=proposal.environment,
        scope=proposal.scope,
        expected_revision=proposal.expected_revision,
        policy_version=proposal.policy_version,
        approver=Principal(
            subject="operator-jane", role="approver", environment=proposal.environment
        ),
        issued_at=NOW.isoformat(),
        expires_at=(NOW + timedelta(minutes=2)).isoformat(),
    )
    values.update(updates)
    return Approval(**values)


def test_refresh_is_authorized_only_for_scoped_executor():
    assert evaluate_plan(plan(), state(), executor()).allowed
    assert not evaluate_plan(plan(), state(), executor(role="reader")).allowed


@pytest.mark.parametrize(
    "changes",
    [
        {"environment": "prod"},
        {"scope": "factory-b"},
        {"expected_revision": 1},
        {"catalog_version": "2.0"},
        {"policy_version": "2.0"},
        {"delegation_depth": 2},
        {"actions": [Action(tool=ToolName.REFRESH), Action(tool=ToolName.RETRY)]},
        {"action_budget": 2},
    ],
)
def test_authorization_rejects_mutated_plan(changes):
    decision = evaluate_plan(plan(**changes), state(), executor())
    assert not decision.allowed and not decision.approval_required


@pytest.mark.parametrize(
    "changes",
    [
        {"source_schema": 2},
        {"rejected_rows": 1},
        {"duplicate_rows": 1},
        {"curated_rows": 1},
        {"backlog_rows": 0},
        {"transient_failure": True},
        {"freshness_lag_seconds": 10},
    ],
)
def test_cross_condition_diagnosis_cannot_authorize_refresh(changes):
    snapshot = state(**changes)
    assert not evaluate_plan(plan(snapshot), snapshot, executor()).allowed


def test_schema_migration_cannot_be_authorized_by_human_approval():
    snapshot = state(source_schema=2)
    proposal = plan(snapshot, ToolName.MIGRATE)
    decision = evaluate_plan(proposal, snapshot, executor(), approval(proposal), now=NOW)
    assert not decision.allowed and not decision.approval_required


def test_quality_requires_approval_and_is_containment():
    snapshot = state(rejected_rows=1, batch_status="rejected")
    proposal = plan(snapshot, ToolName.QUARANTINE)
    decision = evaluate_plan(proposal, snapshot, executor())
    assert not decision.allowed and decision.approval_required
    assert evaluate_plan(proposal, snapshot, executor(), approval(proposal), now=NOW).allowed
    after = snapshot.model_copy(
        update={"revision": 1, "batch_status": "quarantined", "rejected_rows": 0, "backlog_rows": 0}
    )
    evidence = Evidence(evidence_id="fresh", snapshot=after, complete=True, logs=[])
    verification = verify_effect(proposal, evidence)
    assert verification.outcome == "contained" and not verification.resolved


def test_production_requires_a_distinct_scoped_approver():
    snapshot = state(environment="prod")
    proposal, runner = plan(snapshot), executor(environment="prod")
    assert evaluate_plan(proposal, snapshot, runner).approval_required
    assert evaluate_plan(proposal, snapshot, runner, approval(proposal), now=NOW).allowed


@pytest.mark.parametrize(
    "changes",
    [
        {"plan_hash": "0" * 64},
        {"target_id": "line-b"},
        {"incident_id": "incident-b"},
        {"expected_revision": 1},
        {"policy_version": "2.0"},
        {"scope": "factory-b"},
        {"expires_at": NOW.isoformat()},
        {"expires_at": (NOW + timedelta(hours=1)).isoformat()},
        {"issued_at": (NOW + timedelta(seconds=30)).isoformat()},
        {"issued_at": "2026-11-13T12:00:00"},
        {"approver": Principal(subject="dataops-executor", role="approver")},
        {"approver": Principal(subject="other", role="executor")},
        {"approver": Principal(subject="other", role="approver", scope="factory-b")},
    ],
)
def test_approval_binding_identity_expiry_and_validity(changes):
    snapshot = state(rejected_rows=1, batch_status="rejected")
    proposal = plan(snapshot, ToolName.QUARANTINE)
    decision = evaluate_plan(proposal, snapshot, executor(), approval(proposal, **changes), now=NOW)
    assert not decision.allowed and decision.approval_required


def test_every_plan_change_invalidates_existing_approval():
    snapshot = state(rejected_rows=1, batch_status="rejected")
    proposal = plan(snapshot, ToolName.QUARANTINE)
    approved = approval(proposal)
    proposal.rationale = "a new proposal cannot reuse the previous approval"
    assert not evaluate_plan(proposal, snapshot, executor(), approved, now=NOW).allowed


def test_incomplete_or_wrong_target_postconditions_never_close():
    proposal = plan()
    after = state(
        revision=1, batch_status="applied", backlog_rows=0, curated_rows=3, freshness_lag_seconds=0
    )
    evidence = Evidence(evidence_id="fresh", snapshot=after, complete=False, logs=["success"])
    assert verify_effect(proposal, evidence).outcome == "escalated"
    evidence.complete = True
    evidence.snapshot.target_id = "different"
    assert verify_effect(proposal, evidence).outcome == "escalated"


def test_fresh_postcondition_read_checks_actual_business_state():
    proposal = plan()
    unchanged = Evidence(evidence_id="before", snapshot=state(), complete=True, logs=["SUCCESS"])
    assert not verify_effect(proposal, unchanged).resolved
    after = state(
        revision=1, batch_status="applied", backlog_rows=0, curated_rows=3, freshness_lag_seconds=0
    )
    fresh = Evidence(evidence_id="after", snapshot=after, complete=True, logs=[])
    assert verify_effect(proposal, fresh).resolved
