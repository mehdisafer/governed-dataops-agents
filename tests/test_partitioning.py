"""Real SQLite/ASGI boundary tests for opt-in fixed partition routing.

The Temporal client is simulated; live two-queue recovery remains unqualified.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from temporalio.exceptions import ApplicationError, WorkflowAlreadyStartedError

from governed_dataops.activities import Activities
from governed_dataops.api import create_app
from governed_dataops.contracts import Incident
from governed_dataops.routing import queue_for_target, queue_for_worker
from governed_dataops.settings import Settings
from governed_dataops.storage import CapacityExceeded, Store


def target_on(slot: int, prefix: str = "target") -> str:
    expected = f"governed-dataops-v1.p{slot:02d}"
    return next(
        f"{prefix}-{i}" for i in range(200)
        if queue_for_target("governed-dataops-v1", 2, f"{prefix}-{i}") == expected
    )


def incident(name: str, target: str) -> Incident:
    return Incident(
        incident_id=f"incident-{name}", event_id=f"event-{name}", target_id=target,
        symptom="Synthetic partition incident",
    )


def intent(queue: str) -> dict:
    return {"mode": "runbook", "simulate_lost_response": False, "task_queue": queue}


def test_partition_queues_and_failing_closed_configuration():
    assert queue_for_worker("governed-dataops-v1", 1, None) == "governed-dataops-v1"
    assert queue_for_target("governed-dataops-v1", 1, "anything") == "governed-dataops-v1"
    assert queue_for_worker("governed-dataops-v1", 2, 0) == "governed-dataops-v1.p00"
    with pytest.raises(ValueError, match="worker_partition"):
        queue_for_worker("governed-dataops-v1", 2, None)
    with pytest.raises(ValidationError, match="partition_admission_limit"):
        Settings(partition_count=2)
    with pytest.raises(ValidationError, match="reserve a full quota"):
        Settings(partition_count=2, partition_admission_limit=2, max_pending_incidents=3)
    with pytest.raises(ValidationError, match="worker_partition"):
        Settings(partition_count=2, partition_admission_limit=1, max_pending_incidents=2, worker_partition=2)
    with pytest.raises(ValidationError, match="requires multiple partitions"):
        Settings(partition_admission_limit=1)


def test_partition_admission_prevents_one_queue_from_exhausting_another(tmp_path):
    store = Store(tmp_path / "partition.db")
    a = target_on(0, "alpha")
    b = target_on(1, "bravo")
    qa, qb = "governed-dataops-v1.p00", "governed-dataops-v1.p01"
    first = incident("a1", a)
    assert store.record_incident(first, 2, intent=intent(qa), partition_capacity=1)
    assert not store.record_incident(first, 2, intent=intent(qa), partition_capacity=1)
    with pytest.raises(CapacityExceeded, match="partition admission"):
        store.record_incident(incident("a2", a), 2, intent=intent(qa), partition_capacity=1)
    assert store.record_incident(incident("b1", b), 2, intent=intent(qb), partition_capacity=1)
    assert store.bound_target_queue(a) == qa and store.bound_target_queue(b) == qb
    assert len(store.list_incidents()) == 2
    store.event(first.incident_id, "resolved", {"reason": "test completion"})
    assert store.record_incident(incident("a2", a), 2, intent=intent(qa), partition_capacity=1)


def test_target_route_is_immutable_when_topology_changes(tmp_path):
    store = Store(tmp_path / "sticky.db")
    target = next(
        f"target-{i}" for i in range(100)
        if queue_for_target("governed-dataops-v1", 2, f"target-{i}")
        != queue_for_target("governed-dataops-v1", 3, f"target-{i}")
    )
    before = queue_for_target("governed-dataops-v1", 2, target)
    after = queue_for_target("governed-dataops-v1", 3, target)
    old = incident("old", target)
    assert store.record_incident(old, 6, intent=intent(before), partition_capacity=2)
    with pytest.raises(ValueError, match="execution mode"):
        store.record_incident(old, 6, intent=intent(after), partition_capacity=2)
    with pytest.raises(ValueError, match="target queue binding changed"):
        store.record_incident(incident("new", target), 6, intent=intent(after), partition_capacity=2)
    assert store.bound_target_queue(target) == before
    assert len(store.list_incidents()) == 1


def test_pending_legacy_incidents_block_partition_activation(tmp_path):
    store = Store(tmp_path / "legacy.db")
    old = incident("old", "old-target")
    store.record_incident(old, 3, intent={"mode": "runbook", "simulate_lost_response": False})
    new = incident("new", target_on(0))
    queue = "governed-dataops-v1.p00"
    with pytest.raises(ValueError, match="drain active unpartitioned"):
        store.record_incident(new, 3, intent=intent(queue), partition_capacity=1)
    store.event(old.incident_id, "resolved", {"reason": "drained"})
    assert store.record_incident(new, 3, intent=intent(queue), partition_capacity=1)


def test_worker_rejects_cross_partition_and_unregistered_target(tmp_path):
    store = Store(tmp_path / "authority.db")
    target = target_on(0)
    store.record_incident(
        incident("approved", target), 2,
        intent=intent("governed-dataops-v1.p00"), partition_capacity=1
    )
    wrong = Settings(
        db_path=store.path, partition_count=2,
        partition_admission_limit=1, max_pending_incidents=2, worker_partition=1,
    )
    with pytest.raises(ApplicationError, match="not owned"):
        Activities(wrong)._assert_owned(target)
    correct = wrong.model_copy(update={"worker_partition": 0})
    Activities(correct)._assert_owned(target)
    with pytest.raises(ApplicationError, match="route was changed"):
        Activities(correct)._assert_owned("unregistered-target")


def test_partition_quota_respects_independent_environment_and_scope(tmp_path):
    store = Store(tmp_path / "scoped-queue.db")
    queue = "governed-dataops-v1.p00"
    first = incident("scope-a", target_on(0, "scope-a"))
    foreign = incident("scope-b", target_on(0, "scope-b")).model_copy(
        update={"scope": "factory-b"}
    )
    assert store.record_incident(first, 1, intent=intent(queue), partition_capacity=1)
    assert store.record_incident(foreign, 1, intent=intent(queue), partition_capacity=1)
    assert len(store.list_incidents()) == 2
    with pytest.raises(CapacityExceeded):
        store.record_incident(
            incident("scope-a-overflow", target_on(0, "scope-a-overflow")),
            1, intent=intent(queue), partition_capacity=1
        )
    # A pending legacy event in a third scope cannot block partition activation
    # for either independently authenticated scope.
    old = incident("scope-c-legacy", "legacy-target").model_copy(
        update={"scope": "factory-c"}
    )
    store.record_incident(old, 1, intent={"mode": "runbook", "simulate_lost_response": False})
    store.event(first.incident_id, "resolved", {"reason": "quota released"})
    assert store.record_incident(
        incident("scope-a-next", target_on(0, "scope-a-next")),
        1, intent=intent(queue), partition_capacity=1
    )


class FakeTemporal:
    def __init__(self):
        self.service_client = self
        self.started = {}

    async def check_health(self):
        return True

    async def start_workflow(self, kind, payload, **kwargs):
        identifier = kwargs["id"]
        if identifier in self.started:
            raise WorkflowAlreadyStartedError(identifier, kind)
        self.started[identifier] = kwargs["task_queue"]


def test_asgi_dispatch_routes_two_partitions_and_deduplicates(tmp_path):
    settings = Settings(
        db_path=str(tmp_path / "api.db"), operator_token="operator-" + "o" * 32,
        partition_count=2, partition_admission_limit=1, max_pending_incidents=2
    )
    store, temporal = Store(settings.db_path), FakeTemporal()
    a, b = target_on(0, "api-a"), target_on(1, "api-b")
    headers = {"Authorization": "Bearer " + settings.operator_token}
    with TestClient(create_app(settings=settings, store=store, temporal=temporal)) as client:
        first = incident("a1", a)
        body = {"incident": first.model_dump(mode="json"), "mode": "runbook"}
        r = client.post("/api/incidents", headers=headers, json=body)
        assert r.status_code == 202 and r.json()["task_queue"].endswith(".p00")
        retry = client.post("/api/incidents", headers=headers, json=body)
        assert retry.status_code == 202 and retry.json()["deduplicated"] is True
        blocked = client.post("/api/incidents", headers=headers, json={
            "incident": incident("a2", a).model_dump(mode="json"), "mode": "runbook"
        })
        assert blocked.status_code == 429
        independent = client.post("/api/incidents", headers=headers, json={
            "incident": incident("b1", b).model_dump(mode="json"), "mode": "runbook"
        })
        assert independent.status_code == 202 and independent.json()["task_queue"].endswith(".p01")
    assert len(temporal.started) == 2
    assert set(temporal.started.values()) == {"governed-dataops-v1.p00", "governed-dataops-v1.p01"}
    assert store.get_incident(first.incident_id)["events"][0]["payload"]["task_queue"] == (
        "governed-dataops-v1.p00"
    )
