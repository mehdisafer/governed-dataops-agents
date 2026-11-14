"""Runtime unit tests and one real stdio MCP contract test.

FixtureGateway deliberately bypasses HTTP/MCP for activity decision tests.
Those tests do not establish an integrated Temporal/model deployment.
"""

import pytest
from mcp import Client
from temporalio import workflow as temporal_workflow

from governed_dataops.activities import Activities
from governed_dataops.contracts import (
    Diagnosis,
    EffectResult,
    Incident,
    Scenario,
    ToolName,
    build_plan,
    effect_key,
)
from governed_dataops.diagnostic import (
    DiagnosticError,
    LocalNativeSchema,
    diagnose,
    runbook_diagnose,
    sanitized_evidence,
    validate_diagnosis,
)
from governed_dataops.mcp_client import MCPGateway
from governed_dataops.settings import Settings
from governed_dataops.storage import Store
from governed_dataops.workflow import IncidentWorkflow


@pytest.fixture
def runtime(tmp_path):
    settings = Settings(db_path=str(tmp_path / "runtime.db"), environment="dev", scope="factory-a")
    store = Store(settings.db_path)
    store.migrate()
    store.seed_target("runtime-target", Scenario.FRESHNESS, inject_log=True)
    incident = Incident(
        incident_id="runtime-incident",
        event_id="runtime-event",
        target_id="runtime-target",
        symptom="synthetic stale pipeline",
    )
    store.record_incident(incident)
    evidence = store.observe(incident.target_id, settings.principal("reader"))
    diagnosis, _ = runbook_diagnose(incident, evidence)
    return settings, store, incident, evidence, build_plan(incident, evidence, diagnosis)


class FixtureGateway:
    """Activity unit-test transport: actual transactional Store, no network claim."""

    def __init__(self, settings, store, *, lose_response=False, journal_unknown=False):
        self.settings, self.store = settings, store
        self.lose_response, self.journal_unknown = lose_response, journal_unknown
        self.execute_calls = 0
        self.reconcile_calls = 0

    async def collect(self, target_id):
        return self.store.observe(target_id, self.settings.principal("reader"))

    async def reconcile(self, key, target_id):
        self.reconcile_calls += 1
        if self.journal_unknown:
            return EffectResult(
                idempotency_key=key, status="unknown", message="fixture journal outage"
            )
        return self.store.reconcile(key, target_id, self.settings.principal("executor"))

    async def execute(self, request):
        self.execute_calls += 1
        result = self.store.apply(request)
        if self.lose_response:
            return EffectResult(
                idempotency_key=request.idempotency_key,
                status="unknown",
                message="fixture lost response",
            )
        return result


@pytest.mark.parametrize(
    "scenario,action",
    [
        (Scenario.FRESHNESS, ToolName.REFRESH),
        (Scenario.TRANSIENT, ToolName.RETRY),
        (Scenario.SCHEMA, ToolName.MIGRATE),
        (Scenario.QUALITY, ToolName.QUARANTINE),
        (Scenario.DUPLICATE, ToolName.SUPPRESS),
    ],
)
def test_runbook_uses_structured_state_not_log_instructions(tmp_path, scenario, action):
    settings = Settings(db_path=str(tmp_path / "cases.db"), environment="dev", scope="factory-a")
    store = Store(settings.db_path)
    store.migrate()
    store.seed_target("case", scenario, inject_log=True)
    incident = Incident(
        incident_id="case", event_id="case", target_id="case", symptom="synthetic incident"
    )
    evidence = store.observe("case", settings.principal("reader"))
    result, trace = runbook_diagnose(incident, evidence)
    assert result.proposed_action == action
    assert result.evidence_refs == [evidence.evidence_id]
    assert trace["mode"] == "runbook" and trace["model_used"] is False


def test_incomplete_evidence_abstains_before_any_model(runtime):
    _, _, incident, evidence, _ = runtime
    evidence.complete = False
    with pytest.raises(DiagnosticError, match="incomplete"):
        runbook_diagnose(incident, evidence)


def test_reference_hallucination_cannot_become_a_plan(runtime):
    _, _, incident, evidence, _ = runtime
    diagnosis, _ = runbook_diagnose(incident, evidence)
    diagnosis.evidence_refs.append("invented-evidence")
    with pytest.raises(DiagnosticError, match="not collected"):
        validate_diagnosis(diagnosis, evidence)


def test_trace_redacts_credential_strings(runtime):
    _, _, _, evidence, _ = runtime
    evidence.logs.append("Authorization: Bearer hidden-value password=private-value")
    redacted = sanitized_evidence(evidence)
    assert "hidden-value" not in redacted.logs[-1]
    assert "private-value" not in redacted.logs[-1]
    assert evidence.logs[-1] != redacted.logs[-1]


async def test_local_model_outage_does_not_fall_back(runtime):
    settings, _, incident, evidence, _ = runtime
    settings.model_base_url = "http://127.0.0.1:1/v1"
    settings.model_timeout_seconds = 1
    with pytest.raises(DiagnosticError) as result:
        await diagnose(incident, evidence, settings)
    assert result.value.trace["provider"] == "local"
    assert result.value.trace["tools_available_to_model"] == []
    assert result.value.trace["diagnosis_valid"] is False
    assert result.value.trace["model_used"] is False
    assert result.value.trace["request_attempted"] is True
    assert result.value.trace["response_observed"] is False
    assert result.value.trace["usage_complete"] is False


async def test_actual_stdio_mcp_catalog_has_no_shell_or_database_tool():
    gateway = MCPGateway(Settings())
    async with Client(gateway._parameters(), read_timeout_seconds=10) as client:
        catalog = await client.list_tools()
        assert {tool.name for tool in catalog.tools} == {
            "collect_evidence",
            "execute_action",
            "reconcile_effect",
        }
        result = await client.call_tool(
            "execute_action", {"request": {"shell": "arbitrary command"}}
        )
        assert result.is_error
        assert result.structured_content is None


async def test_lost_response_reconciles_one_committed_effect(runtime):
    settings, store, incident, evidence, plan = runtime
    activities = Activities(settings)
    gateway = FixtureGateway(settings, store, lose_response=True)
    activities.gateway = gateway
    result = await activities.execute({"plan": plan.model_dump(mode="json")})
    assert result["status"] == "applied"
    assert gateway.execute_calls == 1 and gateway.reconcile_calls == 2
    verification = await activities.verify({"plan": plan.model_dump(mode="json"), "effect": result})
    assert verification["resolved"] is True
    current = store.observe(incident.target_id, settings.principal("reader")).snapshot
    assert current.curated_rows == evidence.snapshot.backlog_rows
    assert current.revision == evidence.snapshot.revision + 1


async def test_retried_activity_uses_receipt_before_stale_precondition(runtime):
    settings, store, _, _, plan = runtime
    activities = Activities(settings)
    gateway = FixtureGateway(settings, store)
    activities.gateway = gateway
    first = await activities.execute({"plan": plan.model_dump(mode="json")})
    second = await activities.execute({"plan": plan.model_dump(mode="json")})
    assert first["status"] == second["status"] == "applied"
    assert first["idempotency_key"] == second["idempotency_key"] == effect_key(plan, 0)
    assert gateway.execute_calls == 1


async def test_unknown_journal_blocks_mutation(runtime):
    settings, store, _, _, plan = runtime
    activities = Activities(settings)
    gateway = FixtureGateway(settings, store, journal_unknown=True)
    activities.gateway = gateway
    result = await activities.execute({"plan": plan.model_dump(mode="json")})
    assert result["status"] == "unknown"
    assert gateway.execute_calls == 0


async def test_changed_policy_blocks_dispatch(runtime):
    settings, store, _, _, plan = runtime
    activities = Activities(settings)
    gateway = FixtureGateway(settings, store)
    activities.gateway = gateway
    store.set_policy_version(plan.target_id, "changed-policy")
    result = await activities.execute({"plan": plan.model_dump(mode="json")})
    assert result["status"] == "denied"
    assert gateway.execute_calls == 0


async def test_unknown_after_write_without_receipt_is_not_repeated(runtime):
    settings, store, _, _, plan = runtime
    activities = Activities(settings)

    class MissingReceiptGateway(FixtureGateway):
        async def execute(self, request):
            self.execute_calls += 1
            return EffectResult(
                idempotency_key=request.idempotency_key, status="unknown", message="lost"
            )

    gateway = MissingReceiptGateway(settings, store)
    activities.gateway = gateway
    result = await activities.execute({"plan": plan.model_dump(mode="json")})
    assert result["status"] == "unknown"
    assert gateway.execute_calls == 1 and gateway.reconcile_calls == 2


def test_cross_scope_evidence_rejected_before_diagnostic(runtime):
    _, _, incident, evidence, _ = runtime
    incident.scope = "other-factory"
    with pytest.raises(DiagnosticError, match="scope"):
        runbook_diagnose(incident, evidence)


def test_native_schema_forbids_extra_privilege_fields():
    schema = Diagnosis.model_json_schema()
    assert schema["additionalProperties"] is False
    assert "shell" not in schema["properties"]


def test_compact_local_grammar_preserves_post_validation():
    from pydantic import ValidationError

    schema = LocalNativeSchema(Diagnosis.model_json_schema(), strict=True).walk()
    assert "maxLength" not in schema["properties"]["summary"]
    assert "minItems" not in schema["properties"]["evidence_refs"]
    assert schema["additionalProperties"] is False
    assert list(schema["properties"]) == [
        "summary",
        "evidence_refs",
        "rationale",
        "category",
        "proposed_action",
    ]
    with pytest.raises(ValidationError):
        Diagnosis(
            category="freshness",
            summary="x" * 2001,
            evidence_refs=["ev-ok"],
            proposed_action="refresh_partition",
            rationale="original bounded contract remains active",
        )


def test_duplicate_approval_delivery_does_not_consume_decision_budget():
    workflow = IncidentWorkflow()
    envelope = {"plan_hash": "a" * 64, "signature": "same-signed-approval"}
    for _ in range(20):
        workflow.approve(envelope.copy())
    assert len(workflow._approvals) == len(workflow._seen_approvals) == 1
    assert workflow._overflow is False
    workflow._approvals.pop()
    workflow.approve(envelope.copy())
    assert workflow._approvals == []
    workflow.approve({"plan_hash": "a" * 64, "signature": "second-distinct-decision"})
    workflow.approve({"plan_hash": "a" * 64, "signature": "third-distinct-decision"})
    assert workflow._overflow is False
    workflow.approve({"plan_hash": "a" * 64, "signature": "fourth-distinct-decision"})
    assert workflow._overflow is True


async def test_cancel_observed_during_phase_record_prevents_effect_dispatch(runtime, monkeypatch):
    """Explicit stub-based orchestration test, not a Temporal integration claim."""
    from datetime import UTC, datetime

    _, _, incident, evidence, plan = runtime
    workflow = IncidentWorkflow()
    calls = []
    monkeypatch.setattr(temporal_workflow, "patched", lambda _: True)
    monkeypatch.setattr(temporal_workflow, "now", lambda: datetime(2026, 1, 1, tzinfo=UTC))

    async def activity_stub(name, payload, **_):
        calls.append(name)
        if name == "collect":
            return {"evidence": evidence.model_dump(mode="json")}
        if name == "diagnose":
            return {"plan": plan.model_dump(mode="json")}
        if name == "authorize":
            return {"allowed": True, "approval_required": False, "reasons": []}
        if name == "record":
            if payload["phase"] == "executing":
                workflow.cancel()
            return {}
        pytest.fail(f"effect must not be dispatched after observed cancellation: {name}")

    monkeypatch.setattr(workflow, "_activity", activity_stub)
    result = await workflow.run({"incident": incident.model_dump(mode="json"), "mode": "runbook"})
    assert result["status"] == "cancelled"
    assert "execute" not in calls
