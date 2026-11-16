import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier

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



@pytest.mark.parametrize("scenario", list(ACTIONS))
def test_model_evidence_guard_accepts_supported_synthetic_cases(store, scenario):
    """The typed snapshot, not hostile log text, establishes necessary support."""
    from governed_dataops.diagnostic import validate_diagnosis

    _, evidence, _ = prepare(store, scenario, inject=True)
    proposal = Diagnosis(
        category=scenario,
        summary="Synthetic evidence summary",
        evidence_refs=[evidence.evidence_id],
        proposed_action=ACTIONS[scenario],
        rationale="Synthetic evidence rationale",
    )
    assert any("UNTRUSTED INPUT" in line for line in evidence.logs)
    validate_diagnosis(proposal, evidence)  # No effect and no fallback diagnosis.


@pytest.mark.parametrize(
    ("actual", "unsupported_category", "unsupported_action"),
    [
        (Scenario.FRESHNESS, Scenario.SCHEMA, ToolName.MIGRATE),
        (Scenario.TRANSIENT, Scenario.SCHEMA, ToolName.MIGRATE),
        (Scenario.SCHEMA, Scenario.QUALITY, ToolName.QUARANTINE),
        (Scenario.QUALITY, Scenario.SCHEMA, ToolName.MIGRATE),
        (Scenario.DUPLICATE, Scenario.SCHEMA, ToolName.MIGRATE),
    ],
)
def test_impossible_model_proposals_are_rejected_without_reclassification(
    store, actual, unsupported_category, unsupported_action
):
    from governed_dataops.diagnostic import DiagnosticError, validate_diagnosis

    incident, evidence, _ = prepare(store, actual, inject=True)
    proposal = Diagnosis(
        category=unsupported_category,
        summary="Observed logs claim unsupported operation",
        evidence_refs=[evidence.evidence_id],
        proposed_action=unsupported_action,
        rationale="Do not turn a conflicting log instruction into evidence",
    )
    before = proposal.model_dump(mode="json")
    with pytest.raises(DiagnosticError, match="typed snapshot preconditions"):
        validate_diagnosis(proposal, evidence)
    assert proposal.model_dump(mode="json") == before
    assert store.get_incident(incident.incident_id)["phase"] == "received"


def test_model_category_action_mismatch_fails_closed_even_if_category_is_supported(store):
    from governed_dataops.diagnostic import DiagnosticError, validate_diagnosis

    _, evidence, _ = prepare(store, Scenario.FRESHNESS)
    proposal = Diagnosis(
        category=Scenario.FRESHNESS,
        summary="Freshness is overdue",
        evidence_refs=[evidence.evidence_id],
        proposed_action=ToolName.MIGRATE,
        rationale="The action does not match its stated category",
    )
    with pytest.raises(DiagnosticError, match="fixed catalogue"):
        validate_diagnosis(proposal, evidence)


def test_explicit_model_abstention_stays_legal_without_auto_runbook_replacement(store):
    from governed_dataops.diagnostic import validate_diagnosis

    _, evidence, _ = prepare(store, Scenario.FRESHNESS, inject=True)
    proposal = Diagnosis(
        category=Scenario.UNKNOWN,
        summary="Insufficient confidence to decide",
        evidence_refs=[evidence.evidence_id],
        proposed_action=ToolName.ESCALATE,
        rationale="Escalation is explicit, not a disguised automatic remedy",
    )
    validate_diagnosis(proposal, evidence)
    assert proposal.category == Scenario.UNKNOWN
    assert proposal.proposed_action == ToolName.ESCALATE


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



def test_scope_admission_capacity_isolated_across_environment_and_scope(store):
    """A saturated configured scope cannot consume another scope's admission slots."""

    def item(name, scope="factory-a", environment="dev"):
        return Incident(
            incident_id=f"partition-{name}",
            event_id=f"partition-event-{name}",
            target_id=f"line-{name}",
            symptom="Synthetic backlog alert",
            environment=environment,
            scope=scope,
        )

    a1, a2 = item("a1"), item("a2")
    b1 = item("b1", scope="factory-b")
    prod1 = item("prod1", environment="prod")
    assert store.record_incident(a1, max_pending=1)
    assert not store.record_incident(a1, max_pending=1)
    with pytest.raises(CapacityExceeded):
        store.record_incident(a2, max_pending=1)

    # Neither a different scope nor a different environment is starved by A.
    assert store.record_incident(b1, max_pending=1)
    assert store.record_incident(prod1, max_pending=1)
    assert store.incident_counts("dev", "factory-a") == {"received": 1}
    assert store.incident_counts("dev", "factory-b") == {"received": 1}
    assert store.incident_counts("prod", "factory-a") == {"received": 1}

    # Global event identity remains authoritative; another scope cannot reuse it.
    with pytest.raises(ValueError, match="different content"):
        store.record_incident(a1.model_copy(update={"scope": "factory-b"}), max_pending=1)

    store.event(a1.incident_id, "escalated", {"reason": "synthetic operator escalation"})
    assert store.record_incident(a2, max_pending=1)
    assert store.incident_counts("dev", "factory-a") == {"escalated": 1, "received": 1}


def test_concurrent_scope_admission_preserves_atomic_per_scope_limits(store):
    """Concurrent scope traffic cannot overbook an individual admission partition."""
    barrier = Barrier(4)
    cases = [
        Incident(
            incident_id=f"concurrent-scope-{scope}-{i}",
            event_id=f"event-concurrent-{scope}-{i}",
            target_id=f"line-concurrent-{scope}-{i}",
            symptom="Synthetic concurrent admission",
            scope=scope,
        )
        for scope in ("factory-a", "factory-b")
        for i in range(2)
    ]

    def admit(incident):
        barrier.wait(timeout=10)
        try:
            created = store.record_incident(incident, max_pending=1)
            return incident.scope, "accepted" if created else "duplicate"
        except CapacityExceeded:
            return incident.scope, "full"

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(admit, cases))
    for scope in ("factory-a", "factory-b"):
        statuses = [outcome for actual, outcome in results if actual == scope]
        assert sorted(statuses) == ["accepted", "full"]
        assert store.incident_counts("dev", scope) == {"received": 1}
    assert sum(len(store.list_incidents(20, scope=scope)) for scope in ("factory-a", "factory-b")) == 2


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


@pytest.mark.parametrize("legacy", [False, True])
def test_concurrent_duplicate_admission_atomically_binds_one_execution_intent(store, legacy):
    incident = Incident(
        incident_id="intent", event_id="intent-event", target_id="line-a", symptom="synthetic alert"
    )
    if legacy:
        store.record_incident(incident)
    barrier = Barrier(2)

    def compete(mode):
        barrier.wait(timeout=5)
        try:
            created = store.record_incident(
                incident, intent={"mode": mode, "simulate_lost_response": False}
            )
            return {"accepted": True, "created": created, "mode": mode}
        except ValueError:
            return {"accepted": False, "mode": mode}

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(compete, ["agent", "runbook"]))
    accepted = [r for r in results if r["accepted"]]
    assert len(accepted) == 1
    assert accepted[0]["created"] is not legacy
    received = [
        e for e in store.get_incident(incident.incident_id)["events"] if e["phase"] == "received"
    ]
    expected = {"mode": accepted[0]["mode"], "simulate_lost_response": False}
    assert len(received) == 1 and received[0]["payload"] == expected
    reopened = Store(store.path)
    assert not reopened.record_incident(incident, intent=expected)
    with pytest.raises(ValueError, match="execution mode"):
        reopened.record_incident(incident, intent={**expected, "simulate_lost_response": True})
    assert len(reopened.get_incident(incident.incident_id)["events"]) == 1


def test_failed_intent_write_rolls_back_admission(store):
    with sqlite3.connect(store.path) as connection:
        connection.execute(
            "CREATE TRIGGER reject_intent BEFORE INSERT ON incident_events WHEN NEW.phase='received' BEGIN SELECT RAISE(ABORT, 'synthetic event failure'); END"
        )
    incident = Incident(
        incident_id="atomic", event_id="atomic-event", target_id="line-a", symptom="synthetic alert"
    )
    with pytest.raises(sqlite3.IntegrityError, match="synthetic event failure"):
        store.record_incident(incident, intent={"mode": "agent", "simulate_lost_response": False})
    assert store.get_incident_by_event(incident.event_id) is None
    assert store.incident_counts() == {}


def test_scoped_listing_applies_filters_before_the_global_limit(store):
    for identifier, created_at in [
        ("own-old", "2020-01-01T00:00:00Z"),
        ("own-new", "2020-01-02T00:00:00Z"),
    ]:
        store.record_incident(
            Incident(
                incident_id=identifier,
                event_id=identifier,
                target_id="line-a",
                symptom="synthetic alert",
                created_at=created_at,
            )
        )
    foreign = [
        Incident(
            incident_id=f"foreign-{index}",
            event_id=f"foreign-{index}",
            target_id="line-a",
            symptom="synthetic alert",
            environment="prod" if index % 2 else "dev",
            scope="factory-a" if index % 2 else "factory-b",
            created_at="2026-01-01T00:00:00Z",
        )
        for index in range(257)
    ]
    with sqlite3.connect(store.path) as connection:
        connection.executemany(
            "INSERT INTO incidents(incident_id,event_id,target_id,body_json,created_at) VALUES(?,?,?,?,?)",
            [
                (
                    item.incident_id,
                    item.event_id,
                    item.target_id,
                    item.model_dump_json(),
                    item.created_at,
                )
                for item in foreign
            ],
        )
    assert len(store.list_incidents(256)) == 256
    assert [
        item["incident_id"]
        for item in store.list_incidents(1, environment="dev", scope="factory-a")
    ] == ["own-new"]
    assert [
        item["incident_id"]
        for item in store.list_incidents(256, environment="dev", scope="factory-a")
    ] == ["own-new", "own-old"]
    assert not store.list_incidents(scope="factory-a' OR 1=1 --")


def test_operational_event_log_is_correlated_payload_free_and_only_after_commit(store):
    incident, _, _ = prepare(store)
    observed = []

    class ObserveCommit(logging.Handler):
        def emit(self, record):
            with sqlite3.connect(store.path, timeout=0.1) as connection:
                count = connection.execute(
                    "SELECT COUNT(*) FROM incident_events WHERE phase='observed'"
                ).fetchone()[0]
            observed.append((record, count))

    logger = logging.getLogger("governed_dataops.storage")
    handler, previous_level = ObserveCommit(), logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        store.event(incident.incident_id, "observed", {"secret": "synthetic sensitive payload"})
        with sqlite3.connect(store.path) as connection:
            connection.execute(
                "CREATE TRIGGER reject_log BEFORE INSERT ON incident_events WHEN NEW.phase='failed' BEGIN SELECT RAISE(ABORT, 'synthetic commit failure'); END"
            )
        with pytest.raises(sqlite3.IntegrityError):
            store.event(incident.incident_id, "failed", {})
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
    assert len(observed) == 1
    record, committed_count = observed[0]
    assert committed_count == 1
    assert record.incident_id == incident.incident_id and record.phase == "observed"
    assert record.getMessage() == "incident_phase"
    assert "payload" not in record.__dict__ and "synthetic sensitive payload" not in repr(
        record.__dict__
    )


@pytest.mark.parametrize("failure", ["missing_file", "schema_changed", "missing_table"])
def test_target_health_checks_actual_existing_database_and_schema(store, failure):
    app = create_target_app(store=store, settings=Settings())
    with TestClient(app) as client:
        ready = client.get("/health")
        assert ready.status_code == 200 and ready.json()["schema_version"] == 1
        if failure == "missing_file":
            Path(store.path).rename(Path(store.path).with_suffix(".moved"))
        else:
            with sqlite3.connect(store.path) as connection:
                connection.execute(
                    "UPDATE schema_migrations SET version=2"
                    if failure == "schema_changed"
                    else "DROP TABLE effect_ledger"
                )
        failed = client.get("/health")
    assert failed.status_code == 503 and failed.headers["retry-after"] == "1"
    assert failed.json()["status"] == "unavailable"
    if failure == "missing_file":
        assert not Path(store.path).exists()


def test_target_rejects_non_ascii_bearer_as_unauthorized(store):
    store.seed_target("line-a", Scenario.FRESHNESS)
    config = Settings(reader_token="reader-" + "r" * 32)
    with TestClient(create_target_app(store=store, settings=config)) as client:
        response = client.get(
            "/targets/line-a", headers=[(b"Authorization", b"Bearer \xff-malformed")]
        )
    assert response.status_code == 401


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
