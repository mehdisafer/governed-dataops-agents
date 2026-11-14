"""API unit tests: actual ASGI/SQLite; fake Temporal and target HTTP transport.

These are boundary tests, not evidence of a real Temporal or MCP deployment.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
import pytest
from fastapi.testclient import TestClient
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

import governed_dataops.api as api_module
from governed_dataops.contracts import Approval, Diagnosis, Incident, Scenario, ToolName, build_plan
from governed_dataops.settings import Settings
from governed_dataops.signing import generate_approval_keys, verify_approval_signature
from governed_dataops.storage import Store


@dataclass
class FakeWorkflowHandle:
    signals: list = field(default_factory=list)
    query_calls: int = 0
    fail_next_signal: bool = False
    query_unavailable: bool = False

    async def query(self, _name, **_kwargs):
        self.query_calls += 1
        if self.query_unavailable:
            raise TimeoutError("unit fake: no worker polling")
        return {"phase": "received"}

    async def signal(self, name, payload=None):
        self.signals.append((name, payload))
        if self.fail_next_signal:
            self.fail_next_signal = False
            raise TimeoutError("unit fake: signal acknowledgement unavailable")


class FakeTemporal:
    def __init__(self):
        self.service_client = self
        self.healthy = True
        self.fail_next_start = False
        self.started = set()
        self.start_requests = []
        self.handles = {}

    async def check_health(self):
        return self.healthy

    async def start_workflow(self, workflow, payload, **kwargs):
        self.start_requests.append((workflow, payload, kwargs))
        if self.fail_next_start:
            self.fail_next_start = False
            raise ConnectionError("unit fake: Temporal unavailable")
        identifier = kwargs["id"]
        if identifier in self.started:
            raise WorkflowAlreadyStartedError(identifier, workflow)
        self.started.add(identifier)
        return self.get_workflow_handle(identifier)

    def get_workflow_handle(self, identifier):
        return self.handles.setdefault(identifier, FakeWorkflowHandle())


@pytest.fixture
def app_env(tmp_path, monkeypatch):
    private, public = tmp_path / "signing.pem", tmp_path / "verification.pem"
    generate_approval_keys(private, public)
    settings = Settings(
        db_path=str(tmp_path / "api.db"),
        target_url="http://127.0.0.1:8081",
        operator_token="operator-" + "o" * 32,
        approver_token="approver-" + "a" * 32,
        executor_token="executor-" + "e" * 32,
        reader_token="reader-" + "r" * 32,
        approval_signing_key_file=str(private),
        approval_verify_key_file=str(public),
        max_pending_incidents=2,
    )
    store = Store(settings.db_path, approval_verify_key_file=str(public))
    temporal = FakeTemporal()
    target_responses, target_requests = {}, []

    def target_transport(request):
        target_requests.append(request)
        assert request.headers["authorization"] == "Bearer " + settings.reader_token
        target_id = request.url.path.rsplit("/", 1)[-1]
        data = target_responses.get(target_id)
        if data is None:
            data = store.observe(target_id, settings.principal("reader")).model_dump(mode="json")
        return httpx.Response(200, json=data)

    original_client = httpx.AsyncClient
    transport = httpx.MockTransport(target_transport)
    monkeypatch.setattr(
        api_module.httpx,
        "AsyncClient",
        lambda **kwargs: original_client(transport=transport, **kwargs),
    )
    with TestClient(
        api_module.create_app(settings=settings, store=store, temporal=temporal),
        raise_server_exceptions=False,
    ) as client:
        yield client, settings, store, temporal, target_responses, target_requests


def headers(settings, role):
    return {"Authorization": "Bearer " + getattr(settings, f"{role}_token")}


def incident(identifier="incident-a", **updates):
    body = dict(
        incident_id=identifier,
        event_id=f"event-{identifier}",
        target_id=f"target-{identifier}",
        symptom="Synthetic pipeline alert",
    )
    body.update(updates)
    return Incident(**body)


def waiting_plan(settings, store, identifier="incident-a"):
    item = incident(identifier)
    store.seed_target(item.target_id, Scenario.QUALITY)
    store.record_incident(item)
    evidence = store.observe(item.target_id, settings.principal("reader"))
    diagnosis = Diagnosis(
        category=Scenario.QUALITY,
        summary="Rejected row needs quarantine",
        evidence_refs=[evidence.evidence_id],
        proposed_action=ToolName.QUARANTINE,
        rationale="Keep invalid input outside curated data",
    )
    plan = build_plan(item, evidence, diagnosis)
    store.event(item.incident_id, "awaiting_approval", {"plan": plan.model_dump(mode="json")})
    return item, plan


def test_submission_requires_operator_and_scoped_identity(app_env):
    client, settings, store, temporal, _, _ = app_env
    payload = {"incident": incident().model_dump(mode="json")}
    assert client.post("/api/incidents", json=payload).status_code == 401
    for role in ("reader", "executor", "approver"):
        assert (
            client.post("/api/incidents", headers=headers(settings, role), json=payload).status_code
            == 403
        )
    payload["incident"]["scope"] = "factory-b"
    assert (
        client.post(
            "/api/incidents", headers=headers(settings, "operator"), json=payload
        ).status_code
        == 403
    )
    assert not store.list_incidents() and not temporal.start_requests


def test_executor_cannot_approve_and_body_cannot_forge_approver(app_env):
    client, settings, store, temporal, _, _ = app_env
    item, plan = waiting_plan(settings, store)
    path = f"/api/incidents/{item.incident_id}/approval"
    assert (
        client.post(
            path, headers=headers(settings, "executor"), json={"plan_hash": plan.digest()}
        ).status_code
        == 403
    )
    response = client.post(
        path,
        headers=headers(settings, "approver"),
        json={"plan_hash": plan.digest(), "approver": "pretend-admin"},
    )
    assert response.status_code == 422
    assert store.get_incident(item.incident_id)["phase"] == "awaiting_approval"
    assert not temporal.get_workflow_handle(api_module.workflow_id(item.incident_id)).signals


def test_duplicate_event_has_one_durable_incident_and_stable_workflow_id(app_env):
    client, settings, store, temporal, _, _ = app_env
    payload = {"incident": incident().model_dump(mode="json")}
    first = client.post("/api/incidents", headers=headers(settings, "operator"), json=payload)
    payload["incident"]["created_at"] = datetime.now(UTC).isoformat()
    second = client.post("/api/incidents", headers=headers(settings, "operator"), json=payload)
    assert first.status_code == second.status_code == 202
    assert not first.json()["deduplicated"] and second.json()["deduplicated"]
    assert first.json()["workflow_id"] == second.json()["workflow_id"]
    assert len(store.list_incidents()) == len(temporal.started) == 1
    assert all(
        request[2]["id_reuse_policy"] == WorkflowIDReusePolicy.REJECT_DUPLICATE
        for request in temporal.start_requests
    )
    assert len(store.get_incident(payload["incident"]["incident_id"])["events"]) == 1
    changed_mode = client.post(
        "/api/incidents", headers=headers(settings, "operator"), json={**payload, "mode": "runbook"}
    )
    assert changed_mode.status_code == 409
    assert len(temporal.start_requests) == 2
    payload["incident"]["target_id"] = "a-different-target"
    assert (
        client.post(
            "/api/incidents", headers=headers(settings, "operator"), json=payload
        ).status_code
        == 409
    )


def test_terminal_event_retry_does_not_restart_a_closed_workflow(app_env):
    client, settings, store, temporal, _, _ = app_env
    item = incident()
    payload = {"incident": item.model_dump(mode="json")}
    first = client.post("/api/incidents", headers=headers(settings, "operator"), json=payload)
    assert first.status_code == 202
    store.event(item.incident_id, "resolved", {"reason": "unit synthetic completed workflow"})
    starts = len(temporal.start_requests)
    again = client.post("/api/incidents", headers=headers(settings, "operator"), json=payload)
    assert again.status_code == 202 and again.json()["deduplicated"]
    assert again.json()["workflow_id"] == first.json()["workflow_id"]
    assert len(temporal.start_requests) == starts
    assert store.get_incident(item.incident_id)["status"] == "resolved"


def test_admission_returns_backpressure_and_recovers_after_terminal_outcome(app_env):
    client, settings, store, _, _, _ = app_env
    for identifier in ("one", "two"):
        response = client.post(
            "/api/incidents",
            headers=headers(settings, "operator"),
            json={"incident": incident(identifier).model_dump(mode="json")},
        )
        assert response.status_code == 202
    third = {"incident": incident("three").model_dump(mode="json")}
    rejected = client.post("/api/incidents", headers=headers(settings, "operator"), json=third)
    assert rejected.status_code == 429 and rejected.headers["retry-after"] == "5"
    store.event("one", "resolved", {"reason": "unit synthetic completion"})
    assert (
        client.post("/api/incidents", headers=headers(settings, "operator"), json=third).status_code
        == 202
    )


def test_dispatch_failure_keeps_recoverable_incident_and_same_event_retry(app_env):
    client, settings, store, temporal, _, _ = app_env
    item = incident()
    temporal.fail_next_start = True
    payload = {"incident": item.model_dump(mode="json")}
    first = client.post("/api/incidents", headers=headers(settings, "operator"), json=payload)
    assert first.status_code == 503
    assert store.get_incident(item.incident_id)["phase"] == "dispatch_pending"
    recovered = client.post("/api/incidents", headers=headers(settings, "operator"), json=payload)
    assert recovered.status_code == 202 and recovered.json()["deduplicated"]
    assert len(temporal.started) == 1


@pytest.mark.parametrize("field,value", [("scope", "factory-b"), ("environment", "prod")])
def test_incident_list_and_detail_do_not_expose_another_scope(app_env, field, value):
    client, settings, store, temporal, _, _ = app_env
    store.record_incident(incident("own"))
    store.record_incident(incident("foreign", **{field: value}))
    listing = client.get("/api/incidents", headers=headers(settings, "reader"))
    assert listing.status_code == 200
    assert [item["incident_id"] for item in listing.json()] == ["own"]
    assert (
        client.get("/api/incidents/foreign", headers=headers(settings, "reader")).status_code == 403
    )
    assert not temporal.handles


def test_metrics_do_not_count_another_environment_or_scope(app_env):
    client, settings, store, _, _, _ = app_env
    store.record_incident(incident("own"))
    store.record_incident(incident("foreign", scope="factory-b"))
    store.event("foreign", "denied", {})
    response = client.get("/metrics", headers=headers(settings, "reader"))
    assert response.status_code == 200
    assert 'dataops_incidents{state="received"} 1' in response.text
    assert 'dataops_incidents{state="denied"}' not in response.text


def test_tampered_plan_hash_is_refused_before_target_read_or_signing(app_env):
    client, settings, store, temporal, _, target_requests = app_env
    item, _ = waiting_plan(settings, store)
    response = client.post(
        f"/api/incidents/{item.incident_id}/approval",
        headers=headers(settings, "approver"),
        json={"plan_hash": "0" * 64},
    )
    assert response.status_code == 409
    assert not target_requests and not temporal.handles
    assert "approval" not in store.get_incident(item.incident_id)


def test_approval_is_signed_persisted_and_signalled_without_requiring_a_worker_query(app_env):
    client, settings, store, temporal, _, _ = app_env
    item, plan = waiting_plan(settings, store)
    handle = temporal.get_workflow_handle(api_module.workflow_id(item.incident_id))
    handle.query_unavailable = True
    response = client.post(
        f"/api/incidents/{item.incident_id}/approval",
        headers=headers(settings, "approver"),
        json={"plan_hash": plan.digest()},
    )
    assert response.status_code == 202
    recorded = Approval.model_validate(store.get_incident(item.incident_id)["approval"])
    assert recorded.approver == settings.principal("approver")
    assert recorded.plan_hash == plan.digest() and store.approval_exists(recorded)
    assert verify_approval_signature(recorded, settings.approval_verify_key_file)
    assert handle.query_calls == 0
    assert handle.signals == [("approve", recorded.model_dump(mode="json"))]


@pytest.mark.parametrize(
    "change", ["revision", "policy", "incomplete", "wrong_target", "wrong_scope"]
)
def test_live_approval_preconditions_require_exact_complete_scoped_target(app_env, change):
    client, settings, store, temporal, target_responses, _ = app_env
    item, plan = waiting_plan(settings, store)
    body = store.observe(item.target_id, settings.principal("reader")).model_dump(mode="json")
    if change == "revision":
        body["snapshot"]["revision"] += 1
    elif change == "policy":
        body["snapshot"]["policy_version"] = "2.0"
    elif change == "incomplete":
        body["complete"] = False
    elif change == "wrong_target":
        body["snapshot"]["target_id"] = "different-target"
    else:
        body["snapshot"]["scope"] = "factory-b"
    target_responses[item.target_id] = body
    response = client.post(
        f"/api/incidents/{item.incident_id}/approval",
        headers=headers(settings, "approver"),
        json={"plan_hash": plan.digest()},
    )
    assert response.status_code == 409
    assert "approval" not in store.get_incident(item.incident_id)
    assert not temporal.handles


def test_ambiguous_approval_signal_can_redeliver_same_signed_envelope(app_env):
    client, settings, store, temporal, _, _ = app_env
    item, plan = waiting_plan(settings, store)
    handle = temporal.get_workflow_handle(api_module.workflow_id(item.incident_id))
    handle.fail_next_signal = True
    path, payload = f"/api/incidents/{item.incident_id}/approval", {"plan_hash": plan.digest()}
    first = client.post(path, headers=headers(settings, "approver"), json=payload)
    assert first.status_code == 503
    stored = store.get_incident(item.incident_id)["approval"]
    retry = client.post(path, headers=headers(settings, "approver"), json=payload)
    assert retry.status_code == 202
    assert store.get_incident(item.incident_id)["approval"] == stored
    assert len(handle.signals) == 2 and handle.signals[0] == handle.signals[1]


def test_terminal_incident_rejects_new_approval_and_cancellation(app_env):
    client, settings, store, temporal, _, _ = app_env
    item, plan = waiting_plan(settings, store)
    store.event(item.incident_id, "contained", {"reason": "unit synthetic containment"})
    path = f"/api/incidents/{item.incident_id}"
    assert (
        client.post(
            path + "/approval",
            headers=headers(settings, "approver"),
            json={"plan_hash": plan.digest()},
        ).status_code
        == 409
    )
    assert client.post(path + "/cancel", headers=headers(settings, "operator")).status_code == 409
    assert not temporal.handles and store.get_incident(item.incident_id)["status"] == "contained"


def test_health_false_is_not_reported_as_ready(app_env):
    client, _, _, temporal, _, _ = app_env
    assert client.get("/health").status_code == 200
    temporal.healthy = False
    assert client.get("/health").status_code == 503


def test_console_security_boundary_and_incident_json_are_separate(app_env):
    client, settings, store, _, _, _ = app_env
    item = incident(symptom="<script>window.executed=true</script>")
    store.record_incident(item)
    console = client.get("/")
    assert console.status_code == 200 and "window.executed" not in console.text
    assert "script-src 'self'" in console.headers["content-security-policy"]
    assert console.headers["x-content-type-options"] == "nosniff"
    data = client.get(f"/api/incidents/{item.incident_id}", headers=headers(settings, "reader"))
    assert data.headers["content-type"].startswith("application/json")
    assert data.json()["incident"]["symptom"] == item.symptom
    assert client.get("/assets/unknown.js").status_code == 404
