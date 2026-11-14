import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

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
from governed_dataops.policy import verify_effect
from governed_dataops.settings import Settings
from governed_dataops.signing import generate_approval_keys, sign_approval
from governed_dataops.storage import CapacityExceeded, Store
from governed_dataops.target import create_target_app

RUNNER = Principal(subject="dataops-executor", role="executor")
READER = Principal(subject="dataops-reader", role="reader")
ACTIONS = {
    Scenario.FRESHNESS: ToolName.REFRESH,
    Scenario.TRANSIENT: ToolName.RETRY,
    Scenario.SCHEMA: ToolName.MIGRATE,
    Scenario.QUALITY: ToolName.QUARANTINE,
    Scenario.DUPLICATE: ToolName.SUPPRESS,
}


@pytest.fixture
def store(tmp_path):
    generate_approval_keys(tmp_path / "approval-private.pem", tmp_path / "approval-public.pem")
    return Store(
        tmp_path / "test.db", approval_verify_key_file=str(tmp_path / "approval-public.pem")
    )


def prepare(
    store, scenario=Scenario.FRESHNESS, target="line-a", incident_id="incident-a", inject=False
):
    store.seed_target(target, scenario, inject_log=inject)
    incident = Incident(
        incident_id=incident_id,
        event_id=f"event-{incident_id}",
        target_id=target,
        symptom="synthetic alert",
    )
    store.record_incident(incident)
    evidence = store.observe(target, READER)
    diagnosis = Diagnosis(
        category=scenario,
        summary="synthetic test",
        evidence_refs=[evidence.evidence_id],
        proposed_action=ACTIONS[scenario],
        rationale="catalogued test scenario",
    )
    return incident, evidence, build_plan(incident, evidence, diagnosis)


def approved(store, plan):
    now = datetime.now(UTC)
    approval = Approval(
        plan_hash=plan.digest(),
        incident_id=plan.incident_id,
        target_id=plan.target_id,
        environment=plan.environment,
        scope=plan.scope,
        expected_revision=plan.expected_revision,
        policy_version=plan.policy_version,
        approver=Principal(subject="human", role="approver"),
        issued_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=2)).isoformat(),
    )
    return sign_approval(approval, Path(store.path).parent / "approval-private.pem")


def request(plan, approval=None, **updates):
    values = dict(
        idempotency_key=effect_key(plan, 0),
        plan=plan,
        action_index=0,
        executor=RUNNER,
        approval=approval,
    )
    values.update(updates)
    return EffectRequest(**values)


@pytest.mark.parametrize("scenario", list(ACTIONS))
def test_five_real_target_states_and_expected_business_outcomes(store, scenario):
    _, before, plan = prepare(store, scenario)
    approval = approved(store, plan) if scenario == Scenario.QUALITY else None
    if approval:
        store.save_approval(approval)
    result = store.apply(request(plan, approval))
    after = store.observe(plan.target_id, READER)
    if scenario == Scenario.SCHEMA:
        assert result.status == "denied" and after.snapshot == before.snapshot
        return
    assert result.status == "applied" and after.snapshot.revision == before.snapshot.revision + 1
    assert after.snapshot.backlog_rows == 0
    assert verify_effect(plan, after).outcome == (
        "contained" if scenario == Scenario.QUALITY else "resolved"
    )
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM effect_ledger").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM source_rows").fetchone()[0] == 3
        if scenario == Scenario.QUALITY:
            assert connection.execute("SELECT COUNT(*) FROM quarantine_rows").fetchone()[0] == 3
        else:
            assert connection.execute("SELECT SUM(amount) FROM curated_rows").fetchone()[0] == 60


def test_receipt_and_business_write_survive_reopen_and_reconcile(store):
    _, _, plan = prepare(store)
    first = store.apply(request(plan))
    reopened = Store(store.path)
    receipt = reopened.reconcile(effect_key(plan, 0), plan.target_id, RUNNER)
    second = reopened.apply(request(plan))
    assert first.status == receipt.status == second.status == "applied"
    assert receipt.reconciled and second.reconciled
    observed = reopened.observe(plan.target_id, READER).snapshot
    assert observed.curated_rows == 3 and observed.revision == 1


def test_transaction_rolls_back_data_if_receipt_write_fails(store):
    _, _, plan = prepare(store)
    with sqlite3.connect(store.path) as connection:
        connection.execute(
            "CREATE TRIGGER fail_receipt BEFORE INSERT ON effect_ledger "
            "BEGIN SELECT RAISE(ABORT,'injected receipt failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError):
        store.apply(request(plan))
    after = store.observe(plan.target_id, READER).snapshot
    assert after.revision == 0 and after.curated_rows == 0 and after.backlog_rows == 3
    assert store.reconcile(effect_key(plan, 0), plan.target_id, READER).status == "not_found"


def test_concurrent_same_effect_commits_once(store):
    _, _, plan = prepare(store)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: store.apply(request(plan)), range(8)))
    assert all(result.status == "applied" for result in results)
    assert sum(not result.reconciled for result in results) == 1
    assert store.observe(plan.target_id, READER).snapshot.revision == 1


def test_competing_incidents_for_same_target_reject_stale_preconditions(store):
    _, _, first = prepare(store)
    _, _, second = prepare(store, incident_id="incident-b")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda p: store.apply(request(p)), [first, second]))
    assert sorted(r.status for r in results) == ["applied", "denied"]
    assert store.observe(first.target_id, READER).snapshot.curated_rows == 3


def test_different_targets_can_progress_without_mixing_rows(store):
    _, _, first = prepare(store, target="line-a", incident_id="incident-a")
    _, _, second = prepare(store, target="line-b", incident_id="incident-b")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda p: store.apply(request(p)), [first, second]))
    assert all(r.status == "applied" for r in results)
    for target in ("line-a", "line-b"):
        assert store.observe(target, READER).snapshot.curated_rows == 3


def test_forged_approval_is_not_a_registered_human_decision(store):
    _, _, plan = prepare(store, Scenario.QUALITY)
    approval = approved(store, plan)
    assert store.apply(request(plan, approval)).status == "denied"
    store.save_approval(approval)
    tampered = approval.model_copy(
        update={"expires_at": (datetime.now(UTC) + timedelta(minutes=3)).isoformat()}
    )
    assert not store.approval_exists(tampered)
    assert store.apply(request(plan, tampered)).status == "denied"
    assert store.apply(request(plan, approval)).status == "applied"


def test_executor_written_approval_record_cannot_replace_signed_human_decision(store):
    _, _, plan = prepare(store, Scenario.QUALITY)
    legitimate = approved(store, plan)
    forged = legitimate.model_copy(update={"signature": ""})
    store.save_approval(forged)
    assert store.approval_exists(forged)
    rejected = store.apply(request(plan, forged))
    assert rejected.status == "denied" and "signature" in rejected.message
    tampered = legitimate.model_copy(
        update={"expires_at": (datetime.now(UTC) + timedelta(minutes=3)).isoformat()}
    )
    store.save_approval(tampered)
    rejected = store.apply(request(plan, tampered))
    assert rejected.status == "denied" and "signature" in rejected.message
    assert store.observe(plan.target_id, READER).snapshot.batch_status == "rejected"


def test_missing_verification_key_fails_closed_even_with_a_registered_signature(store):
    _, _, plan = prepare(store, Scenario.QUALITY)
    approval = approved(store, plan)
    store.save_approval(approval)
    store.approval_verify_key_file = ""
    assert store.apply(request(plan, approval)).status == "denied"


def test_stale_approval_and_policy_change_prevent_mutation(store):
    _, _, plan = prepare(store, Scenario.QUALITY)
    approval = approved(store, plan)
    store.save_approval(approval)
    store.revise_target(plan.target_id)
    assert store.apply(request(plan, approval)).status == "denied"
    assert store.observe(plan.target_id, READER).snapshot.batch_status == "rejected"
    store.set_policy_version(plan.target_id, "2.0")
    assert store.apply(request(plan, approval)).status == "denied"


def test_untrusted_instructions_do_not_open_migration_or_scope_permissions(store):
    _, evidence, plan = prepare(store, Scenario.SCHEMA, inject=True)
    assert any("Ignore all rules" in log for log in evidence.logs)
    assert store.apply(request(plan)).status == "denied"
    with pytest.raises(PermissionError):
        store.observe(plan.target_id, READER.model_copy(update={"scope": "factory-b"}))
    with pytest.raises(PermissionError):
        store.observe(plan.target_id, READER.model_copy(update={"environment": "prod"}))


def test_missing_incomplete_and_stale_evidence_fail_closed(store):
    _, _, plan = prepare(store)
    assert (
        store.apply(request(plan.model_copy(update={"evidence_id": "does-not-exist"}))).status
        == "denied"
    )
    store.set_evidence_complete(plan.target_id, False)
    _, _, new_plan = prepare(store, incident_id="incident-b")
    assert store.apply(request(new_plan)).status == "denied"


def test_idempotency_identity_cannot_be_rebound_to_different_plan(store):
    _, _, plan = prepare(store)
    key = effect_key(plan, 0)
    assert store.apply(request(plan)).status == "applied"
    changed = plan.model_copy(update={"rationale": "different plan"})
    assert store.apply(request(changed, idempotency_key=key)).status == "denied"
    assert store.observe(plan.target_id, READER).snapshot.revision == 1


def test_ingress_deduplication_and_conflict_detection(store):
    incident, _, _ = prepare(store)
    assert not store.record_incident(incident)
    later = incident.model_copy(update={"created_at": datetime.now(UTC).isoformat()})
    assert not store.record_incident(later)
    with pytest.raises(ValueError):
        store.record_incident(incident.model_copy(update={"target_id": "line-b"}))
    assert store.get_incident_by_event(incident.event_id)["incident_id"] == incident.incident_id


def test_atomic_admission_backpressure_and_recovery(store):
    first = Incident(incident_id="one", event_id="one", target_id="a", symptom="alert")
    second = Incident(incident_id="two", event_id="two", target_id="b", symptom="alert")
    assert store.record_incident(first, max_pending=1)
    assert not store.record_incident(first, max_pending=1)
    with pytest.raises(CapacityExceeded):
        store.record_incident(second, max_pending=1)
    store.event("one", "escalated", {"reason": "operator intervention"})
    assert store.record_incident(second, max_pending=1)
    assert store.incident_counts() == {"escalated": 1, "received": 1}


def test_audit_events_keep_correlated_plan_without_credentials(store):
    incident, _, plan = prepare(store)
    store.event(
        incident.incident_id, "planned", {"plan": plan.model_dump(mode="json"), "token": "hidden"}
    )
    item = store.get_incident(incident.incident_id)
    assert item["plan"]["target_id"] == plan.target_id and item["plan_hash"] == plan.digest()
    assert item["events"][0]["payload"]["token"] == "[REDACTED]"
    assert item["events"][0]["sequence"] > 0


@pytest.mark.parametrize("terminal", ["resolved", "contained", "denied", "escalated", "cancelled"])
def test_late_audit_events_cannot_regress_terminal_state_or_projection(store, terminal):
    incident, _, plan = prepare(store)
    store.event(incident.incident_id, "planned", {"plan": plan.model_dump(mode="json")})
    store.event(incident.incident_id, "finished", {"result": {"status": terminal}})
    store.event(incident.incident_id, "cancellation_requested", {"actor": "operator"})
    changed = plan.model_copy(update={"rationale": "late non-authoritative plan"})
    store.event(
        incident.incident_id, "approval_submitted", {"plan": changed.model_dump(mode="json")}
    )
    item = store.get_incident(incident.incident_id)
    assert item["status"] == item["phase"] == terminal
    assert item["plan"] == plan.model_dump(mode="json") and len(item["events"]) == 4
    next_incident = Incident(incident_id="next", event_id="next", target_id="b", symptom="alert")
    assert store.record_incident(next_incident, max_pending=1)


def test_backup_and_actual_restored_read_mutation_and_reconcile(store, tmp_path):
    _, _, plan = prepare(store)
    store.apply(request(plan))
    assert store.backup(tmp_path / "backup.db")["integrity"] == "ok"
    restored = Store(tmp_path / "backup.db")
    assert restored.observe(plan.target_id, READER).snapshot.curated_rows == 3
    assert restored.reconcile(effect_key(plan, 0), plan.target_id, READER).status == "applied"
    _, _, next_plan = prepare(restored, target="after-restore", incident_id="after-restore")
    assert restored.apply(request(next_plan)).status == "applied"
    assert store.get_incident_by_event("event-after-restore") is None


def test_seed_never_resets_repaired_target(store):
    _, _, plan = prepare(store)
    store.apply(request(plan))
    same = store.seed_target(plan.target_id, Scenario.FRESHNESS)
    assert same.revision == 1 and same.curated_rows == 3
    with pytest.raises(ValueError):
        store.seed_target(plan.target_id, Scenario.QUALITY)


def test_bounded_fixture_variants_change_actual_rows_without_resetting_existing_state(store):
    for variant in range(3):
        state = store.seed_target(f"variant-{variant}", Scenario.FRESHNESS, variant=variant)
        assert (
            state.backlog_rows == 3 + variant
            and state.freshness_lag_seconds == 7200 + variant * 100
        )
    with pytest.raises(ValueError):
        store.seed_target("variant-1", Scenario.FRESHNESS, variant=2)


def test_target_http_authentication_and_ambiguous_effect(store):
    config = Settings(
        demo_mode=True,
        reader_token="r" * 32,
        executor_token="e" * 32,
        operator_token="o" * 32,
        approver_token="a" * 32,
    )
    client = TestClient(create_target_app(store=store, settings=config))
    incident, _, plan = prepare(store)
    assert client.get(f"/targets/{incident.target_id}").status_code == 401
    reader_headers = {"Authorization": "Bearer " + config.reader_token}
    executor_headers = {"Authorization": "Bearer " + config.executor_token}
    payload = request(plan, simulate_lost_response=True).model_dump(mode="json")
    assert client.post("/effects", headers=reader_headers, json=payload).status_code == 403
    assert client.post("/effects", headers=executor_headers, json=payload).status_code == 503
    receipt = client.get(
        f"/effects/{effect_key(plan, 0)}",
        params={"target_id": plan.target_id},
        headers=reader_headers,
    )
    assert receipt.status_code == 200
    assert receipt.json()["status"] == "applied" and receipt.json()["reconciled"]
    repeat = client.post("/effects", headers=executor_headers, json=payload)
    assert repeat.status_code == 200 and repeat.json()["reconciled"]
    assert store.observe(plan.target_id, READER).snapshot.revision == 1


def test_asserted_executor_identity_cannot_replace_authenticated_identity(store):
    config = Settings(executor_token="e" * 32, reader_token="r" * 32)
    client = TestClient(create_target_app(store=store, settings=config))
    _, _, plan = prepare(store)
    forged = RUNNER.model_copy(update={"subject": "pretend-admin"})
    payload = request(plan, executor=forged).model_dump(mode="json")
    response = client.post(
        "/effects", headers={"Authorization": "Bearer " + config.executor_token}, json=payload
    )
    assert response.status_code == 403
    assert store.observe(plan.target_id, READER).snapshot.revision == 0


def test_demo_seed_and_faults_are_disabled_in_normal_mode(store):
    config = Settings(executor_token="e" * 32, operator_token="o" * 32)
    client = TestClient(create_target_app(store=store, settings=config))
    seed = {"target_id": "example", "scenario": "freshness"}
    response = client.post(
        "/seed", headers={"Authorization": "Bearer " + config.operator_token}, json=seed
    )
    assert response.status_code == 403
    _, _, plan = prepare(store)
    response = client.post(
        "/effects",
        headers={"Authorization": "Bearer " + config.executor_token},
        json=request(plan, simulate_lost_response=True).model_dump(mode="json"),
    )
    assert response.status_code == 403
    assert store.observe(plan.target_id, READER).snapshot.revision == 0
