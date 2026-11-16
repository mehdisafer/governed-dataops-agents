"""Negative authority checks for two fixed Temporal target partitions.

Uses a real transactional Store and real Ed25519 signatures; it does not
replace the separately executed multi-queue Temporal recovery profile.
"""

from datetime import UTC, datetime, timedelta

import pytest
from temporalio.exceptions import ApplicationError

from governed_dataops.activities import Activities
from governed_dataops.contracts import (
    Approval,
    Diagnosis,
    EffectRequest,
    Incident,
    Principal,
    Scenario,
    ToolName,
    build_plan,
    effect_key,
)
from governed_dataops.routing import queue_for_target
from governed_dataops.settings import Settings
from governed_dataops.signing import generate_approval_keys, sign_approval
from governed_dataops.storage import Store


BASE_QUEUE = "governed-dataops-v1"


def route_target(slot: int, prefix: str) -> str:
    """Select a deterministic fixture without dependence on Python hash seeds."""
    return next(
        f"{prefix}-{number}"
        for number in range(200)
        if queue_for_target(BASE_QUEUE, 2, f"{prefix}-{number}")
        == f"{BASE_QUEUE}.p{slot:02d}"
    )


def quality_plan(store: Store, name: str, slot: int):
    """Create a real rejected-batch target with first-admission routing bound."""
    target = route_target(slot, f"authority-{name}")
    store.seed_target(target, Scenario.QUALITY)
    event = Incident(
        incident_id=f"incident-{name}",
        event_id=f"event-{name}",
        target_id=target,
        symptom="Synthetic rejected batch requiring human decision",
    )
    queue = queue_for_target(BASE_QUEUE, 2, target)
    assert store.record_incident(
        event,
        4,
        intent={
            "mode": "runbook",
            "simulate_lost_response": False,
            "task_queue": queue,
        },
        partition_capacity=2,
    )
    reader = Principal(subject="qualified-reader", role="reader")
    evidence = store.observe(target, reader)
    proposal = Diagnosis(
        category=Scenario.QUALITY,
        summary="Synthetic rejected rows",
        evidence_refs=[evidence.evidence_id],
        proposed_action=ToolName.QUARANTINE,
        rationale="Contain rejected rows after a signed approval",
    )
    return event, build_plan(event, evidence, proposal), evidence.snapshot


def signed_approval(plan, private_file):
    now = datetime.now(UTC)
    approval = Approval(
        plan_hash=plan.digest(),
        incident_id=plan.incident_id,
        target_id=plan.target_id,
        environment=plan.environment,
        scope=plan.scope,
        expected_revision=plan.expected_revision,
        policy_version=plan.policy_version,
        approver=Principal(subject="qualified-human", role="approver"),
        issued_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=2)).isoformat(),
    )
    return sign_approval(approval, private_file)


def submit_effect(store, plan, approval):
    return store.apply(
        EffectRequest(
            idempotency_key=effect_key(plan, 0),
            plan=plan,
            action_index=0,
            executor=Principal(subject="qualified-executor", role="executor"),
            approval=approval,
        )
    )


def test_signed_approval_cannot_be_replayed_on_another_partition(tmp_path):
    private, public = tmp_path / "private.pem", tmp_path / "public.pem"
    generate_approval_keys(private, public)
    store = Store(tmp_path / "partition-approvals.db", str(public))
    _, plan_a, before_a = quality_plan(store, "partition-a", 0)
    _, plan_b, before_b = quality_plan(store, "partition-b", 1)

    signed_a = signed_approval(plan_a, private)
    store.save_approval(signed_a)
    mismatch = submit_effect(store, plan_b, signed_a)
    assert mismatch.status == "denied"
    assert "approval" in mismatch.message

    # Even if a caller rewrites all binding fields to those of partition B,
    # the original Ed25519 signature and durable identity no longer match.
    forged_b = signed_a.model_copy(
        update={
            "plan_hash": plan_b.digest(),
            "incident_id": plan_b.incident_id,
            "target_id": plan_b.target_id,
            "expected_revision": plan_b.expected_revision,
        }
    )
    tampered = submit_effect(store, plan_b, forged_b)
    assert tampered.status == "denied"
    assert "signature" in tampered.message
    reader = Principal(subject="qualified-reader", role="reader")
    assert store.observe(plan_a.target_id, reader).snapshot == before_a
    assert store.observe(plan_b.target_id, reader).snapshot == before_b
    with store._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM effect_ledger").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM quarantine_rows").fetchone()[0] == 0

    # A genuinely separate signed and registered B approval must still work.
    signed_b = signed_approval(plan_b, private)
    store.save_approval(signed_b)
    applied_b = submit_effect(store, plan_b, signed_b)
    assert applied_b.status == "applied"
    assert store.observe(plan_b.target_id, reader).snapshot.revision == before_b.revision + 1
    assert store.observe(plan_a.target_id, reader).snapshot == before_a
    assert store.reconcile(effect_key(plan_a, 0), plan_a.target_id, reader).status == "not_found"
    assert store.reconcile(effect_key(plan_b, 0), plan_b.target_id, reader).status == "applied"


async def test_wrong_partition_worker_cannot_dispatch_an_effect(tmp_path):
    private, public = tmp_path / "private.pem", tmp_path / "public.pem"
    generate_approval_keys(private, public)
    store = Store(tmp_path / "partition-workers.db", str(public))
    _, plan, before = quality_plan(store, "wrong-worker", 0)
    other_worker = Settings(
        db_path=store.path,
        approval_verify_key_file=str(public),
        partition_count=2,
        partition_admission_limit=2,
        max_pending_incidents=4,
        worker_partition=1,
    )
    with pytest.raises(ApplicationError, match="not owned"):
        await Activities(other_worker).execute({"plan": plan.model_dump(mode="json")})
    after = store.observe(
        plan.target_id, Principal(subject="qualified-reader", role="reader")
    ).snapshot
    assert after == before
    with store._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM effect_ledger").fetchone()[0] == 0


def test_completed_target_route_cannot_be_silently_reassigned(tmp_path):
    store = Store(tmp_path / "route-history.db")
    event, plan, before = quality_plan(store, "historical", 0)
    original_queue = store.bound_target_queue(plan.target_id)
    store.event(event.incident_id, "resolved", {"reason": "synthetic fixture completion"})
    next_event = Incident(
        incident_id="incident-later",
        event_id="event-later",
        target_id=plan.target_id,
        symptom="Same target after a topology change",
    )
    with pytest.raises(ValueError, match="target queue binding changed"):
        store.record_incident(
            next_event,
            4,
            intent={
                "mode": "runbook",
                "simulate_lost_response": False,
                "task_queue": f"{BASE_QUEUE}.p01",
            },
            partition_capacity=2,
        )
    assert store.bound_target_queue(plan.target_id) == original_queue
    assert store.observe(
        plan.target_id, Principal(subject="qualified-reader", role="reader")
    ).snapshot == before
    with store._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM effect_ledger").fetchone()[0] == 0
