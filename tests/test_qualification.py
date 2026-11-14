"""Qualifier control-flow regressions with explicit fake Temporal/service boundaries.

These tests prove evidence gates, not a running Temporal or model integration.
"""

import asyncio
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from temporalio.api.enums.v1 import EventType
from temporalio.api.history.v1 import HistoryEvent
from temporalio.client import WorkflowHistory

from governed_dataops.contracts import Incident
from governed_dataops.storage import Store

SPEC = importlib.util.spec_from_file_location(
    "qualification", Path(__file__).resolve().parents[1] / "scripts/qualify.py"
)
qualification = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualification)


@pytest.fixture
def capture_runtime(tmp_path):
    store = Store(str(tmp_path / "application.db"))
    store.migrate()
    incident = Incident(
        incident_id="qualification-incident",
        event_id="qualification-event",
        target_id="qualification-target",
        symptom="Synthetic terminal projection",
    )
    store.record_incident(incident)
    expected_result = {"incident_id": incident.incident_id, "status": "resolved"}
    store.event(incident.incident_id, "resolved", {"result": expected_result})

    class FixtureRuntime(qualification.Runtime):
        @property
        def store(self):
            return store

    runtime = object.__new__(FixtureRuntime)
    runtime.output = tmp_path
    closed = asyncio.Event()

    class FixtureHandle:
        result_value = expected_result
        event_type = EventType.EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED
        history_calls = 0

        async def result(self):
            await closed.wait()
            return self.result_value

        async def fetch_history(self):
            self.history_calls += 1
            return WorkflowHistory(
                "dataops-" + incident.incident_id,
                [HistoryEvent(event_id=1, event_type=self.event_type)],
            )

    handle = FixtureHandle()
    runtime.temporal = SimpleNamespace(get_workflow_handle=lambda _: handle)
    return runtime, incident, closed, handle


async def test_terminal_projection_does_not_qualify_an_open_workflow(capture_runtime):
    runtime, incident, closed, handle = capture_runtime
    task = asyncio.create_task(runtime.capture(incident))
    await asyncio.sleep(0)
    assert not task.done() and handle.history_calls == 0
    assert (runtime.output / f"trace-{incident.incident_id}.json").exists()
    closed.set()
    record = await asyncio.wait_for(task, timeout=1)
    assert record["result"] == handle.result_value
    assert handle.history_calls == 1


@pytest.mark.parametrize("failure", ["result_mismatch", "open_history"])
async def test_closed_result_and_original_history_must_agree(capture_runtime, failure):
    runtime, incident, closed, handle = capture_runtime
    if failure == "result_mismatch":
        handle.result_value = {"incident_id": incident.incident_id, "status": "escalated"}
    else:
        handle.event_type = EventType.EVENT_TYPE_ACTIVITY_TASK_SCHEDULED
    closed.set()
    with pytest.raises(AssertionError, match="workflow"):
        await runtime.capture(incident)
    # Preserve conflicting original evidence instead of hiding it behind the failure.
    assert (runtime.output / f"history-{incident.incident_id}.json").exists()
    assert (
        json.loads((runtime.output / f"workflow-result-{incident.incident_id}.json").read_text())
        == handle.result_value
    )


@pytest.mark.parametrize("cleanup_case", ["clean", "failure", "live_child", "exception"])
async def test_cleanup_is_part_of_overall_qualification(tmp_path, monkeypatch, cleanup_case):
    cleanup = {
        "failures": [{"reason": "fixture stop failed"}] if cleanup_case == "failure" else [],
        "direct_children_stopped": cleanup_case != "live_child",
    }

    class FixtureRuntime:
        def __init__(self, _manifest, output, *, model):
            self.output = output
            self.processes = {}

        async def start(self):
            self.output.mkdir()

        async def close(self):
            if cleanup_case == "exception":
                raise OSError("fixture final cleanup failed")
            return cleanup

    async def selected_check_passes(self, name, _function):
        self.results.append({"name": name, "status": "passed"})

    monkeypatch.setattr(qualification, "Runtime", FixtureRuntime)
    monkeypatch.setattr(qualification, "source_manifest", lambda: {"content_sha256": "same"})
    monkeypatch.setattr(qualification.Qualification, "check", selected_check_passes)
    output = tmp_path / "run"
    args = SimpleNamespace(
        output=output,
        manifest=tmp_path / "unused.json",
        source_commit=None,
        profile="load",
        count=1,
        concurrency=1,
        previous_histories=None,
    )
    code = await qualification.main_async(args)
    final = json.loads((output / "run.json").read_text())
    assert code == (0 if cleanup_case == "clean" else 1)
    assert final["status"] == ("passed" if cleanup_case == "clean" else "failed")
    assert final["cleanup"] == json.loads((output / "cleanup.json").read_text())
