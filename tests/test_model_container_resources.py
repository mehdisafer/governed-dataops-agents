"""Cgroup-v2 evidence remains read-only, bounded and nonfatal without Docker."""

import runpy
import subprocess
from pathlib import Path

from governed_dataops.model_container_resources import (
    ALLOWED,
    MODEL_CGROUP_PROBE_SCRIPT,
    model_container_resource_delta,
    parse_container_resource_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]


def test_model_cgroup_parser_is_allowlisted_and_does_not_echo_untrusted_data():
    samples = parse_container_resource_snapshot(
        "gda:cgroup_cpu_usage_usec 1000\n"
        "gda:cgroup_cpu_nr_periods 10\n"
        "gda:cgroup_memory_current_bytes 500\n"
        "gda:cgroup_unknown_metric 9000\n"
        "gda:cgroup_cpu_nr_throttled{scope=\"other\"} 8\n"
        "gda:cgroup_cpu_throttled_usec NaN\n"
        "gda:cgroup_memory_oom_total -1\n"
        "secret_token EXPOSED\n"
    )
    assert samples == {
        "gda:cgroup_cpu_usage_usec": 1000,
        "gda:cgroup_cpu_nr_periods": 10,
        "gda:cgroup_memory_current_bytes": 500,
    }
    assert set(samples) <= ALLOWED
    assert "EXPOSED" not in repr(samples)


def test_duplicate_metric_and_invalid_sample_remain_unknown():
    samples = parse_container_resource_snapshot(
        "gda:cgroup_cpu_usage_usec 10\n"
        "gda:cgroup_cpu_usage_usec 11\n"
        "gda:cgroup_cpu_nr_throttled -1\n"
        "gda:cgroup_cpu_nr_periods 4.5\n"
        "gda:cgroup_memory_oom_kill_total 0\n"
    )
    assert samples == {"gda:cgroup_memory_oom_kill_total": 0}


def test_deltas_quota_and_cpu_throttling_are_observed_not_inferred():
    before = {
        "gda:cgroup_cpu_usage_usec": 100_000,
        "gda:cgroup_cpu_nr_periods": 200,
        "gda:cgroup_cpu_nr_throttled": 5,
        "gda:cgroup_cpu_throttled_usec": 900,
        "gda:cgroup_memory_oom_total": 0,
        "gda:cgroup_memory_oom_kill_total": 0,
        "gda:cgroup_memory_current_bytes": 1000,
        "gda:cgroup_memory_peak_bytes": 1200,
        "gda:cgroup_cpu_quota_usec": 200_000,
        "gda:cgroup_cpu_period_usec": 100_000,
    }
    after = {
        **before,
        "gda:cgroup_cpu_usage_usec": 1_100_000,
        "gda:cgroup_cpu_nr_periods": 240,
        "gda:cgroup_cpu_nr_throttled": 15,
        "gda:cgroup_cpu_throttled_usec": 5000,
        "gda:cgroup_memory_current_bytes": 1600,
        "gda:cgroup_memory_peak_bytes": 1700,
    }
    report = model_container_resource_delta(before, after)
    assert report["status"] == "observed"
    assert report["counter_deltas"]["gda:cgroup_cpu_usage_usec"] == 1_000_000
    assert report["counter_deltas"]["gda:cgroup_cpu_throttled_usec"] == 4100
    assert report["counter_deltas"]["gda:cgroup_memory_oom_total"] == 0
    assert report["cpu_throttled_period_fraction"] == 0.25
    assert report["observed_effective_cpu_limit"] == 2.0
    assert report["boundary_gauges"]["gda:cgroup_memory_peak_bytes"] == {
        "before": 1200, "after": 1700
    }
    assert any("not request-exclusive" in x for x in report["limits"])


def test_resource_counter_reset_and_quota_change_are_unknown():
    report = model_container_resource_delta(
        {
            "gda:cgroup_cpu_nr_throttled": 11,
            "gda:cgroup_cpu_nr_periods": 15,
            "gda:cgroup_cpu_quota_usec": 200000,
            "gda:cgroup_cpu_period_usec": 100000,
        },
        {
            "gda:cgroup_cpu_nr_throttled": 1,
            "gda:cgroup_cpu_nr_periods": 30,
            "gda:cgroup_cpu_quota_usec": 300000,
            "gda:cgroup_cpu_period_usec": 100000,
        },
    )
    assert report["status"] == "partial"
    assert report["counter_deltas"]["gda:cgroup_cpu_nr_throttled"] is None
    assert report["counter_resets"] == ["gda:cgroup_cpu_nr_throttled"]
    assert report["cpu_throttled_period_fraction"] is None
    assert report["observed_effective_cpu_limit"] is None


def test_absent_cgroup_and_invalid_numeric_are_not_zero_usage():
    missing = model_container_resource_delta(None, None)
    assert missing["status"] == "unavailable"
    assert missing["cpu_throttled_period_fraction"] is None
    assert missing["observed_effective_cpu_limit"] is None
    assert all(x is None for x in missing["counter_deltas"].values())
    invalid = model_container_resource_delta(
        {"gda:cgroup_cpu_usage_usec": True},
        {"gda:cgroup_cpu_usage_usec": float("inf")},
    )
    assert invalid["counter_deltas"]["gda:cgroup_cpu_usage_usec"] is None


def test_probe_script_is_private_allowlisted_cgroup_v2_only():
    assert "/sys/fs/cgroup/cpu.stat" in MODEL_CGROUP_PROBE_SCRIPT
    assert "/sys/fs/cgroup/memory.events" in MODEL_CGROUP_PROBE_SCRIPT
    assert "/sys/fs/cgroup/cpu.max" in MODEL_CGROUP_PROBE_SCRIPT
    assert "/proc" not in MODEL_CGROUP_PROBE_SCRIPT
    assert "subprocess" not in MODEL_CGROUP_PROBE_SCRIPT
    # A syntax-only check; it does not claim the hosted model container
    # supports cgroup v2, nor that this snapshot is a complete runtime trial.
    compile(MODEL_CGROUP_PROBE_SCRIPT, "<bounded-cgroup-probe>", "exec")


def test_existing_private_model_scrape_reuses_one_exec_for_both_sources():
    qualifier = object.__new__(
        runpy.run_path(str(ROOT / "scripts" / "qualify_container.py"))[
            "ContainerQualification"
        ]
    )
    qualifier.override = Path("/tmp/isolated-fake-compose-override.json")
    calls = []

    def fake_compose(args, label, **kwargs):
        calls.append((args, label, kwargs))
        return subprocess.CompletedProcess(
            args, 0,
            "llamacpp:prompt_tokens_total 9\n"
            "gda:cgroup_cpu_usage_usec 500000\n"
            "gda:cgroup_cpu_nr_periods 7\n"
            "gda:cgroup_memory_current_bytes 1024\n"
            "unsupported_name 99\n",
            "",
        )

    qualifier.compose = fake_compose
    server = qualifier.server_metric_snapshot("before")
    assert server == {"llamacpp:prompt_tokens_total": 9}
    assert qualifier._resource_snapshots["before"] == {
        "gda:cgroup_cpu_usage_usec": 500000,
        "gda:cgroup_cpu_nr_periods": 7,
        "gda:cgroup_memory_current_bytes": 1024,
    }
    assert len(calls) == 1
    args, label, kwargs = calls[0]
    assert args[:4] == ["exec", "-T", "model", "python"]
    assert "/metrics" in args[-1] and "/sys/fs/cgroup/cpu.stat" in args[-1]
    assert label == "model-metrics-before"
    assert kwargs == {"timeout": 10}
    # Verify the exact concatenated Python probe can compile without Docker.
    compile(args[-1], "<private-model-and-cgroup-probe>", "exec")


def test_server_metric_unavailable_can_still_retain_cgroup_observation():
    qualifier = object.__new__(
        runpy.run_path(str(ROOT / "scripts" / "qualify_container.py"))[
            "ContainerQualification"
        ]
    )
    qualifier.override = Path("/tmp/isolated-fake-compose-override.json")
    qualifier.compose = lambda args, label, **kwargs: subprocess.CompletedProcess(
        args, 0, "gda:cgroup_cpu_usage_usec 123456\\n", ""
    )
    # Server-only evidence is missing but independent cgroup evidence is real
    # data from this bounded synthetic output, not fabricated zero usage.
    assert qualifier.server_metric_snapshot("after") is None
    assert qualifier._resource_snapshots["after"] == {
        "gda:cgroup_cpu_usage_usec": 123456
    }
    assert model_container_resource_delta(
        None, qualifier._resource_snapshots["after"]
    )["status"] == "unavailable"


def test_without_docker_override_model_and_cgroup_remain_unavailable():
    qualifier = object.__new__(
        runpy.run_path(str(ROOT / "scripts" / "qualify_container.py"))[
            "ContainerQualification"
        ]
    )
    assert qualifier.server_metric_snapshot("before") is None
    assert not hasattr(qualifier, "_resource_snapshots")
    assert model_container_resource_delta(None, None)["status"] == "unavailable"
