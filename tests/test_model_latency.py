"""Bounded latency provenance tests; no Docker or live model is used here."""

import json
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest
from temporalio.exceptions import ApplicationError

import governed_dataops.activities as activities_module
from governed_dataops.activities import Activities
from governed_dataops.contracts import Incident, Scenario
from governed_dataops.diagnostic import DiagnosticError, runbook_diagnose
from governed_dataops.settings import Settings
from governed_dataops.storage import Store

QUALIFIER = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts" / "qualify_container.py")
)
model_latency_report = QUALIFIER["model_latency_report"]
ContainerQualification = QUALIFIER["ContainerQualification"]


def test_stage_report_records_only_measured_numbers_and_not_raw_model_text():
    trace = {
        "response_observed": True,
        "diagnosis_valid": False,
        "duration_seconds": 86.75,
        "client_model_slot_wait_seconds": 0.035,
        "untrusted_text": "THIS_STRING_MUST_NOT_LEAK_IN_THE_REPORT",
    }
    report = model_latency_report(
        trace,
        gate_wall_seconds=92.125,
        admission_http_seconds=0.125,
        workflow_poll_seconds=91.25,
        stack_startup_seconds=35.5,
        model_cpu_quota=2.0,
        failure_type=None,
    )
    assert report["status"] == "observed"
    assert report["response_observed"] is True
    assert report["diagnosis_valid"] is False
    stages = report["segments_seconds"]
    assert stages["client_model_slot_wait"] == 0.035
    assert stages["diagnostic_call_including_validation"] == 86.75
    assert stages["full_agent_gate"] == 92.125
    assert stages["model_only_startup_readiness"] is None
    assert stages["server_internal_queue_wait"] is None
    assert stages["semantic_validation_only"] is None
    assert "THIS_STRING_MUST_NOT_LEAK" not in json.dumps(report)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), -1, True, "10.0"])
def test_unavailable_or_invalid_durations_are_not_fabricated_as_seconds(bad):
    report = model_latency_report(
        {"duration_seconds": bad, "response_observed": "unverified"},
        gate_wall_seconds=bad,
        admission_http_seconds=None,
        workflow_poll_seconds=None,
        stack_startup_seconds=None,
        model_cpu_quota=None,
        failure_type="TimeoutError",
    )
    assert report["status"] == "incomplete"
    assert report["response_observed"] is None
    assert report["segments_seconds"]["diagnostic_call_including_validation"] is None
    assert report["segments_seconds"]["full_agent_gate"] is None


def test_incomplete_real_container_probe_retains_original_failure_and_partial_report(tmp_path):
    probe = object.__new__(ContainerQualification)
    probe.output = tmp_path
    probe.records = [{"label": "start-stack", "seconds": 11.3}]
    probe.args = SimpleNamespace(model_cpus=2.0)
    probe.submit = lambda *_args, **_kwargs: "synthetic-incident"

    def fail_completion(_incident):
        raise TimeoutError("Synthetic workflow did not close")

    probe.complete = fail_completion
    probe.request = lambda *_args, **_kwargs: {
        "events": [
            {"payload": {
                "model_trace": {
                    "provider": "local",
                    "response_observed": False,
                    "request_attempted": True,
                    "duration_seconds": 90.0,
                    "client_model_slot_wait_seconds": 0.005,
                }
            }}
        ]
    }
    with pytest.raises(TimeoutError, match="did not close"):
        probe.agent_case()
    quality = json.loads((tmp_path / "model-quality.json").read_text())
    latency = json.loads((tmp_path / "model-latency.json").read_text())
    assert quality["quality_passed"] is False and quality["quality_assessed"] is False
    assert quality["failure_type"] == "TimeoutError"
    assert latency["failure_type"] == "TimeoutError"
    assert latency["response_observed"] is False
    assert latency["segments_seconds"]["stack_startup_all_services"] == 11.3
    assert latency["segments_seconds"]["client_model_slot_wait"] == 0.005
    assert latency["segments_seconds"]["full_agent_gate"] >= 0.0


def fixture_incident(tmp_path):
    settings = Settings(db_path=str(tmp_path / "runtime.db"))
    store = Store(settings.db_path)
    store.seed_target("latency-target", Scenario.FRESHNESS)
    incident = Incident(
        incident_id="inc-latency", event_id="evt-latency",
        target_id="latency-target", symptom="Synthetic delayed target",
    )
    store.record_incident(incident)
    evidence = store.observe(incident.target_id, settings.principal("reader"))
    return settings, store, incident, evidence


async def test_activity_records_local_client_slot_wait_on_valid_diagnosis(tmp_path, monkeypatch):
    settings, store, incident, evidence = fixture_incident(tmp_path)

    async def fake_diagnose(item, observed, _settings):
        result, _trace = runbook_diagnose(item, observed)
        return result, {"mode": "agent", "response_observed": True}

    monkeypatch.setattr(activities_module, "diagnose", fake_diagnose)
    activities = Activities(settings)
    result = await activities.diagnose(
        {"incident": incident.model_dump(mode="json"), "evidence": evidence.model_dump(mode="json"), "mode": "agent"}
    )
    assert result["plan"]["target_id"] == incident.target_id
    events = store.get_incident(incident.incident_id)["events"]
    traces = [e["payload"]["model_trace"] for e in events if e["phase"] == "diagnosed"]
    assert len(traces) == 1
    assert traces[0]["client_model_slot_acquired"] is True
    assert traces[0]["client_model_slot_wait_seconds"] >= 0.0


async def test_activity_preserves_slot_measurement_when_model_proposal_fails(tmp_path, monkeypatch):
    settings, store, incident, evidence = fixture_incident(tmp_path)

    async def fake_failure(_incident, _evidence, _settings):
        raise DiagnosticError("synthetic invalid proposal", {"response_observed": True})

    monkeypatch.setattr(activities_module, "diagnose", fake_failure)
    activities = Activities(settings)
    with pytest.raises(ApplicationError, match="synthetic invalid"):
        await activities.diagnose({
            "incident": incident.model_dump(mode="json"),
            "evidence": evidence.model_dump(mode="json"),
            "mode": "agent",
        })
    events = store.get_incident(incident.incident_id)["events"]
    failures = [e["payload"] for e in events if e["phase"] == "diagnostic_failed"]
    assert len(failures) == 1
    trace = failures[0]["model_trace"]
    assert trace["client_model_slot_acquired"] is True
    assert trace["client_model_slot_wait_seconds"] >= 0.0
    assert trace["response_observed"] is True
