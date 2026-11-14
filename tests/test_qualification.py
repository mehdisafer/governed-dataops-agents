"""Synthetic qualification-harness boundary tests; no services or model are executed.

The runtime below supplies labelled artificial observations to exercise scoring,
identity checks and profile scheduling. A passing test is not native requalification.
"""

import asyncio
import copy
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

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("qualification_harness", ROOT / "scripts/qualify.py")
qualifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualifier)
# Preserve the existing closure/cleanup regression fixtures' module reference.
qualification = qualifier
DEVELOPMENT = json.loads((ROOT / "data/development-v1.json").read_text())["cases"]
HELDOUT = json.loads((ROOT / "data/heldout-v1.json").read_text())["cases"]


class SyntheticRuntime:
    """Artificial completed observations for unit tests, never a Temporal substitute in CI."""

    def __init__(self, output, *, failures=(), incomplete=()):
        self.output = output
        self.failures, self.incomplete = set(failures), set(incomplete)
        self.requests = {}
        self.initial_business = {}
        self.processes = {}

    async def create(self, scenario, *, mode, variant, inject, lost):
        entry = next(
            item
            for item in [*DEVELOPMENT, *HELDOUT]
            if (item["scenario"], item["variant"], item["inject_log"])
            == (scenario, variant, inject)
        )
        identifier = f"synthetic-unit-{mode}-{entry['case_id']}"
        self.requests[identifier] = (entry, mode)
        self.initial_business[identifier] = self.before(entry, identifier + "-target")
        return SimpleNamespace(incident_id=identifier, target_id=identifier + "-target")

    async def complete(self, incident):
        entry, mode = self.requests[incident.incident_id]
        key = (mode, entry["case_id"])
        if key in self.incomplete:
            raise TimeoutError("synthetic unit fixture: workflow completion unavailable")
        correct = key not in self.failures
        events = []
        if correct and entry["scenario"] == "transient":
            events = [{"phase": phase} for phase in ("effect_uncertain", "effect_reconciled")]
        if correct and entry["scenario"] == "quality":
            events = [{"phase": "approval_submitted"}]
        return {
            "status": entry["expected_outcome"] if correct else "escalated",
            "diagnosis": {
                "category": entry["expected_category"],
                "proposed_action": entry["expected_action"],
            }
            if correct
            else {},
            "verification": {"resolved": correct and entry["expected_outcome"] == "resolved"},
            "events": [{**event, "payload": {}} for event in events],
        }

    @staticmethod
    def before(entry, target_id):
        count = 3 + entry["variant"] % 3
        source = [
            [
                index,
                -(index * 10 + entry["variant"])
                if entry["scenario"] == "quality" and index == count
                else index * 10 + entry["variant"],
            ]
            for index in range(1, count + 1)
        ]
        curated = copy.deepcopy(source) if entry["scenario"] == "duplicate" else []
        return {
            "counts": {
                "source_rows": len(source),
                "curated_rows": len(curated),
                "quarantine_rows": 0,
                "effect_ledger": 0,
            },
            "rows": {
                "source_rows": source,
                "curated_rows": curated,
                "quarantine_rows": [],
            },
            "snapshot": {
                "target_id": target_id,
                "environment": "dev",
                "scope": "factory-a",
                "revision": 0,
                "source_schema": 2 if entry["scenario"] == "schema" else 1,
                "accepted_schema": 1,
                "backlog_rows": count,
                "rejected_rows": int(entry["scenario"] == "quality"),
                "curated_rows": len(curated),
                "duplicate_rows": 0,
                "transient_failure": entry["scenario"] == "transient",
                "freshness_lag_seconds": 7200 + entry["variant"] * 100,
                "batch_id": "synthetic-unit-batch",
                "batch_status": {
                    "freshness": "pending",
                    "transient": "failed",
                    "schema": "pending",
                    "quality": "rejected",
                    "duplicate": "applied",
                }[entry["scenario"]],
                "policy_version": "1.0",
            },
        }

    def business(self, target_id):
        identifier = target_id.removesuffix("-target")
        entry, mode = self.requests[identifier]
        final = copy.deepcopy(self.initial_business[identifier])
        if (mode, entry["case_id"]) in self.failures or entry["scenario"] == "schema":
            return final
        final["counts"]["effect_ledger"] = final["snapshot"]["revision"] = 1
        final["snapshot"]["backlog_rows"] = final["snapshot"]["rejected_rows"] = 0
        if entry["scenario"] == "quality":
            final["rows"]["quarantine_rows"] = copy.deepcopy(final["rows"]["source_rows"])
            final["counts"]["quarantine_rows"] = final["counts"]["source_rows"]
            final["snapshot"]["batch_status"] = "quarantined"
        else:
            final["rows"]["curated_rows"] = copy.deepcopy(final["rows"]["source_rows"])
            final["counts"]["curated_rows"] = final["snapshot"]["curated_rows"] = final["counts"][
                "source_rows"
            ]
            final["snapshot"]["batch_status"] = (
                "suppressed" if entry["scenario"] == "duplicate" else "applied"
            )
            if entry["scenario"] != "duplicate":
                final["snapshot"]["freshness_lag_seconds"] = 0
                final["snapshot"]["transient_failure"] = False
        return final

    async def start(self):
        self.output.mkdir(parents=True)

    async def close(self):
        return {"failures": [], "direct_children_stopped": True}


async def synthetic_pair(output, *, reference_failure=False, baseline_failure=True):
    failures = []
    if reference_failure:
        failures.append(("runbook", "development-01"))
    if baseline_failure:
        failures.append(("runbook", "heldout-01"))
    suite = qualifier.Qualification(SyntheticRuntime(output, failures=failures))
    await suite.check("five_runbook_business_cases", suite.cases)
    await suite.check(
        "heldout_runbook_measurement",
        lambda: suite.cases(
            mode="runbook", cases=HELDOUT, partition="heldout", measurement_only=True
        ),
    )
    await suite.check(
        "heldout_agent", lambda: suite.cases(mode="agent", cases=HELDOUT, partition="heldout")
    )
    return suite


def read_json(path):
    return json.loads(path.read_text())


async def test_reference_failure_remains_blocking_despite_synthetic_paired_superiority(tmp_path):
    suite = await synthetic_pair(tmp_path, reference_failure=True)
    assert suite.results[0]["status"] == "failed"
    reference = read_json(tmp_path / "failed-cases-development-runbook.json")
    assert reference["attempted"] == 5 and reference["strict_case_successes"] == 4
    with pytest.raises(AssertionError, match="No measured"):
        await suite.compare_engines()
    result = read_json(tmp_path / "comparison.json")
    assert result["engines"]["agent"]["strict_case_successes"] == 10
    assert result["engines"]["runbook"]["strict_case_successes"] == 9
    assert not result["baseline_reference_competence_passed"]
    assert not result["agent_advantage_established"]


async def test_honest_complete_weaker_baseline_is_measured_and_score_failures_retained(tmp_path):
    suite = await synthetic_pair(tmp_path)
    baseline_gate = suite.results[1]
    assert baseline_gate["name"] == "heldout_runbook_measurement"
    assert baseline_gate["status"] == "passed"
    detail = baseline_gate["detail"]
    assert detail["scoring_requirement"] == "complete_safe_measurement"
    assert detail["attempted"] == detail["completed_with_business_observation"] == 10
    assert detail["strict_case_successes"] == 9 and detail["measurement_errors"] == []
    retained = read_json(tmp_path / "failed-cases-heldout-runbook.json")
    assert retained == detail
    failed = retained["cases"][0]
    assert failed["effect_count"] == 0 and failed["workflow_completed"]
    assert not failed["diagnosis_correct"]


async def test_synthetic_paired_superiority_can_pass_metric_without_native_claim(tmp_path):
    suite = await synthetic_pair(tmp_path)
    result = await suite.compare_engines()
    assert result["version"] == "1.1"
    assert result["baseline_reference_competence_passed"]
    assert result["input_validation"] == {"passed": True, "errors": []}
    assert result["agent_advantage_established"]
    assert result["engines"]["agent"]["strict_case_successes"] == 10
    assert result["engines"]["runbook"]["strict_case_successes"] == 9


async def test_parity_never_establishes_value(tmp_path):
    suite = await synthetic_pair(tmp_path, baseline_failure=False)
    with pytest.raises(AssertionError, match="No measured"):
        await suite.compare_engines()
    result = read_json(tmp_path / "comparison.json")
    assert result["input_validation"]["passed"]
    assert result["engines"]["runbook"]["strict_case_successes"] == 10
    assert result["engines"]["agent"]["strict_case_successes"] == 10
    assert not result["agent_advantage_established"]


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "extra",
        "duplicate",
        "replace",
        "definition",
        "mode",
        "partition",
        "scenario",
        "expected_action",
    ],
)
async def test_comparison_rejects_invalid_scheduled_pairing_and_preserves_originals(
    tmp_path, mutation
):
    suite = await synthetic_pair(tmp_path)
    path = tmp_path / "cases-heldout-agent.json"
    rows = read_json(path)
    if mutation == "missing":
        rows.pop()
    elif mutation == "extra":
        extra = copy.deepcopy(rows[0])
        extra["case_id"] = "synthetic-unscheduled-case"
        rows.append(extra)
    elif mutation == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    elif mutation == "replace":
        rows[-1]["case_id"] = "synthetic-unscheduled-case"
    elif mutation == "definition":
        rows[0]["case_definition_sha256"] = "0" * 64
    else:
        rows[0][mutation] = "synthetic-mismatch"
    qualifier.write_json(path, rows)
    original = path.read_bytes()
    with pytest.raises(AssertionError, match="Comparative inputs"):
        await suite.compare_engines()
    result = read_json(tmp_path / "comparison.json")
    assert result["input_validation"]["errors"]
    assert not result["agent_advantage_established"]
    assert path.read_bytes() == original


@pytest.mark.parametrize("mode", ["runbook", "agent"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("effect_count", None),
        ("unjustified_effect", True),
        ("unjustified_effect", None),
        ("workflow_completed", False),
        ("workflow_result_matches_projection", False),
        ("final_business_observed", False),
        ("business", {}),
        ("action_correct", False),
    ],
)
async def test_unknown_unsafe_or_incomplete_attempts_never_establish_value(
    tmp_path, mode, field, value
):
    suite = await synthetic_pair(tmp_path)
    path = tmp_path / f"cases-heldout-{mode}.json"
    rows = read_json(path)
    # Index 1 is a successful effect in both synthetic engines. A false action
    # flag cannot be hidden by leaving unjustified_effect falsely set to False.
    rows[1][field] = value
    qualifier.write_json(path, rows)
    with pytest.raises(AssertionError, match="Comparative inputs"):
        await suite.compare_engines()
    result = read_json(tmp_path / "comparison.json")
    assert not result["input_validation"]["passed"]
    assert not result["agent_advantage_established"]


@pytest.mark.parametrize(
    "corruption",
    [
        "double_effect",
        "wrong_curated_values",
        "changed_source_and_curated",
        "zero_effect_data_change",
        "malformed_row",
        "missing_observed_values",
        "contradictory_observed_values",
        "forged_business_score",
        "forged_reconciliation",
        "missing_initial_state",
        "duplicate_row_identity",
        "nonterminal_outcome",
    ],
)
async def test_complete_but_corrupt_observations_cannot_be_called_safe_measurements(
    tmp_path, corruption
):
    suite = await synthetic_pair(tmp_path)
    path = tmp_path / "cases-heldout-runbook.json"
    rows = read_json(path)
    row = rows[0] if corruption == "zero_effect_data_change" else rows[1]
    business = row["business"]
    if corruption == "double_effect":
        row["effect_count"] = business["counts"]["effect_ledger"] = business["snapshot"][
            "revision"
        ] = 2
        row["business_invariants_hold"] = False
    elif corruption == "wrong_curated_values":
        business["rows"]["curated_rows"][0][1] += 1
        row["business_invariants_hold"] = False
    elif corruption == "changed_source_and_curated":
        business["rows"]["source_rows"][0][1] += 1
        business["rows"]["curated_rows"][0][1] += 1
    elif corruption == "zero_effect_data_change":
        business["rows"]["source_rows"][0][1] += 1
    elif corruption == "malformed_row":
        business["rows"]["source_rows"][0] = None
    elif corruption == "missing_observed_values":
        for key in ("observed_category", "observed_action", "observed_outcome"):
            row.pop(key)
    elif corruption == "contradictory_observed_values":
        row.update(
            observed_category="unknown", observed_action="escalate", observed_outcome="escalated"
        )
    elif corruption == "forged_business_score":
        business["snapshot"]["revision"] = 2
        assert row["business_invariants_hold"]
    elif corruption == "forged_reconciliation":
        row["observed_event_phases"] = []
        assert row["ambiguous_effect_reconciled"]
    elif corruption == "missing_initial_state":
        row.pop("initial_business")
    elif corruption == "duplicate_row_identity":
        business["rows"]["source_rows"][1][0] = business["rows"]["source_rows"][0][0]
    else:
        row.update(observed_outcome="running", outcome_correct=False)
    qualifier.write_json(path, rows)
    original = path.read_bytes()
    with pytest.raises(AssertionError, match="Comparative inputs"):
        await suite.compare_engines()
    result = read_json(tmp_path / "comparison.json")
    assert result["input_validation"]["errors"] and not result["agent_advantage_established"]
    assert path.read_bytes() == original


async def test_safe_unresolved_duplicate_preserves_preexisting_curated_rows(tmp_path):
    suite = qualifier.Qualification(
        SyntheticRuntime(tmp_path, failures=[("runbook", "heldout-05")])
    )
    result = await suite.cases(
        mode="runbook", cases=HELDOUT, partition="heldout", measurement_only=True
    )
    failed = result["cases"][4]
    assert result["strict_case_successes"] == 9
    assert failed["business"] == failed["initial_business"]
    assert failed["effect_count"] == 0
    assert failed["business"]["rows"]["curated_rows"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("observed_category", {"unexpected": "object"}),
        ("observed_action", []),
        ("observed_category", "not-a-scenario"),
        ("observed_action", "not-a-tool"),
    ],
)
async def test_malformed_diagnostic_values_cannot_be_measured_as_safe_abstentions(
    tmp_path, field, value
):
    suite = await synthetic_pair(tmp_path)
    path = tmp_path / "cases-heldout-runbook.json"
    rows = read_json(path)
    assert rows[0]["effect_count"] == 0
    assert rows[0]["diagnosis_correct"] is rows[0]["action_correct"] is False
    rows[0][field] = value
    qualifier.write_json(path, rows)
    original = path.read_bytes()
    with pytest.raises(AssertionError, match="Comparative inputs"):
        await suite.compare_engines()
    result = read_json(tmp_path / "comparison.json")
    assert not result["agent_advantage_established"]
    assert any("valid enum" in error for error in result["input_validation"]["errors"])
    assert path.read_bytes() == original


async def test_equally_truncated_denominators_cannot_manufacture_superiority(tmp_path):
    suite = await synthetic_pair(tmp_path)
    for mode in ("runbook", "agent"):
        path = tmp_path / f"cases-heldout-{mode}.json"
        qualifier.write_json(path, read_json(path)[:-1])
    with pytest.raises(AssertionError, match="Comparative inputs"):
        await suite.compare_engines()
    assert not read_json(tmp_path / "comparison.json")["agent_advantage_established"]


async def test_missing_engine_records_produce_retained_failure_report(tmp_path):
    suite = await synthetic_pair(tmp_path)
    (tmp_path / "cases-heldout-agent.json").unlink()
    with pytest.raises(AssertionError, match="Comparative inputs"):
        await suite.compare_engines()
    result = read_json(tmp_path / "comparison.json")
    assert not result["agent_advantage_established"]
    assert "original case records unavailable" in result["input_validation"]["errors"][0]
    assert (tmp_path / "cases-heldout-runbook.json").is_file()


async def test_open_workflow_attempt_is_retained_but_cannot_pass_baseline_measurement(tmp_path):
    runtime = SyntheticRuntime(tmp_path, incomplete=[("runbook", "heldout-01")])
    suite = qualifier.Qualification(runtime)
    with pytest.raises(AssertionError, match="workflow closure"):
        await suite.cases(mode="runbook", cases=HELDOUT, partition="heldout", measurement_only=True)
    rows = read_json(tmp_path / "cases-heldout-runbook.json")
    assert len(rows) == 10
    assert rows[0]["case_id"] == "heldout-01"
    assert rows[0]["exception_type"] == "TimeoutError"
    assert rows[0]["effect_count"] is None and not rows[0]["workflow_completed"]
    assert (tmp_path / "failed-cases-heldout-runbook.json").is_file()


async def test_agent_quality_is_still_strict_and_cannot_select_measurement_only(tmp_path):
    suite = qualifier.Qualification(SyntheticRuntime(tmp_path, failures=[("agent", "heldout-01")]))
    with pytest.raises(ValueError, match="restricted to the heldout baseline"):
        await suite.cases(mode="agent", cases=HELDOUT, partition="heldout", measurement_only=True)
    with pytest.raises(AssertionError, match="strict diagnosis"):
        await suite.cases(mode="agent", cases=HELDOUT, partition="heldout")
    retained = read_json(tmp_path / "failed-cases-heldout-agent.json")
    assert retained["strict_case_successes"] == 9 and retained["attempted"] == 10


@pytest.mark.parametrize("entries", [[], [HELDOUT[0], HELDOUT[0]]])
async def test_empty_or_duplicate_scheduled_corpus_cannot_pass_measurement(tmp_path, entries):
    suite = qualifier.Qualification(SyntheticRuntime(tmp_path))
    with pytest.raises(AssertionError):
        await suite.cases(mode="runbook", cases=entries, partition="heldout", measurement_only=True)
    assert read_json(tmp_path / "cases-heldout-runbook.json") is not None
    assert (tmp_path / "failed-cases-heldout-runbook.json").is_file()


@pytest.mark.parametrize("reference_failure", [False, True])
async def test_evaluation_profile_requires_reference_competence_before_acceptance(
    tmp_path, monkeypatch, reference_failure
):
    """Exercise actual profile scheduling with synthetic runtime observations only."""

    def runtime_factory(_manifest, output, *, model):
        assert model is True
        failures = [("runbook", "heldout-01")]
        if reference_failure:
            failures.append(("runbook", "development-01"))
        return SyntheticRuntime(output, failures=failures)

    async def synthetic_replay(_self):
        return {"synthetic_unit_fixture": True, "services_executed": False}

    source = {
        "commit": "synthetic-unit-source",
        "tracked_worktree_clean": True,
        "untracked_source_files": [],
        "files": {},
        "content_sha256": "synthetic-unit-digest",
    }
    monkeypatch.setattr(qualifier, "Runtime", runtime_factory)
    monkeypatch.setattr(qualifier, "source_manifest", lambda: copy.deepcopy(source))
    monkeypatch.setattr(qualifier.Qualification, "replay", synthetic_replay)
    output = tmp_path / "synthetic-profile-output"
    args = SimpleNamespace(
        output=output,
        manifest=tmp_path / "unused-synthetic-manifest",
        profile="evaluation",
        source_commit=None,
        previous_histories=None,
        count=12,
        concurrency=4,
    )
    code = await qualifier.main_async(args)
    result = read_json(output / "run.json")
    checks = {item["name"]: item["status"] for item in result["checks"]}
    assert code == (1 if reference_failure else 0)
    assert checks["five_runbook_business_cases"] == ("failed" if reference_failure else "passed")
    assert checks["heldout_runbook_measurement"] == "passed"
    assert checks["heldout_agent"] == "passed"
    assert result["comparison_semantics_version"] == "1.1"
    assert len(read_json(output / "cases-development-runbook.json")) == 5


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
