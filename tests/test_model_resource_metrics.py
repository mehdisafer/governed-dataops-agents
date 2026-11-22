"""Resource evidence boundaries; no model, Docker daemon or inference is started."""

import copy
import json
import runpy
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from governed_dataops.model_resource_metrics import (
    CPU_COUNTERS,
    MEMORY_COUNTERS,
    keyed_counters,
    resource_delta,
    resource_snapshot,
)


def fixture_cgroup(tmp_path):
    root, proc = tmp_path / "cgroup", tmp_path / "proc"
    root.mkdir()
    for path, content in {
        "cgroup.controllers": "cpu memory\n",
        "cpu.stat": "\n".join(f"{name} {100 + i}" for i, name in enumerate(CPU_COUNTERS)),
        "memory.events": "\n".join(f"{name} {i}" for i, name in enumerate(MEMORY_COUNTERS)),
        "cpu.max": "200000 100000\n", "memory.current": "12345\n", "memory.max": "3221225472\n",
    }.items():
        (root / path).write_text(content)
    for path, content in {
        "self/cgroup": "0::/\n",
        "sys/kernel/random/boot_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee\n",
        "1/stat": "1 (synthetic (private) name) " + " ".join(["S", *["0"] * 18, "123456"]),
    }.items():
        target = proc / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    return root, proc


def fixture_snapshot(tmp_path):
    snapshot = resource_snapshot(*fixture_cgroup(tmp_path))
    snapshot["identity"]["container_id"] = "a" * 64
    snapshot["cgroup_namespace_mode"] = "private"
    return snapshot


def test_v2_snapshot_observes_actual_units_and_excludes_untrusted_fields(tmp_path):
    root, proc = fixture_cgroup(tmp_path)
    with (root / "cpu.stat").open("a") as stream:
        stream.write("\nunknown_raw_prompt secret-value-never-copy\n")
    result = resource_snapshot(root, proc)
    assert result["status"] == "observed"
    assert result["cpu_max"] == {"quota_usec": 200000, "period_usec": 100000, "unlimited": False}
    assert result["memory_current_bytes"] == 12345
    assert result["memory_max_bytes"] == 3221225472
    assert result["identity"]["pid1_start_ticks"] == 123456
    assert set(result["cpu_stat"]) == set(CPU_COUNTERS)
    assert "secret-value" not in json.dumps(result)


@pytest.mark.parametrize("membership", ["4:cpu,cpuacct:/\n", "0::/host/other-container\n", ""])
def test_v1_host_namespace_and_missing_membership_never_become_model_metrics(tmp_path, membership):
    root, proc = fixture_cgroup(tmp_path)
    (proc / "self/cgroup").write_text(membership)
    result = resource_snapshot(root, proc)
    assert result["status"] == "unavailable"
    assert result["reason"] == "private_cgroup_v2_namespace_unverified"
    assert "cpu_stat" not in result


def test_missing_and_oversized_files_stay_unknown_with_only_error_types(tmp_path):
    root, proc = fixture_cgroup(tmp_path)
    (root / "cpu.stat").unlink()
    (root / "memory.current").write_text("sensitive" * 9000)
    result = resource_snapshot(root, proc)
    assert result["status"] == "partial"
    assert all(x is None for x in result["cpu_stat"].values())
    assert result["memory_current_bytes"] is None
    assert result["errors"] == {"cpu.stat": "FileNotFoundError", "memory.current": "ValueError"}
    assert "sensitive" not in json.dumps(result)


def test_duplicated_negative_noninteger_and_nonfinite_counters_stay_unknown():
    result = keyed_counters(
        "usage_usec 1\nusage_usec 2\nusage_usec 3\nuser_usec -1\nsystem_usec 1.2\n"
        "nr_periods NaN\nnr_throttled Infinity\nthrottled_usec 0\n", CPU_COUNTERS,
    )
    assert result == {name: 0 if name == "throttled_usec" else None for name in CPU_COUNTERS}


def test_unlimited_quota_is_explicit_not_zero_cpu_or_memory(tmp_path):
    root, proc = fixture_cgroup(tmp_path)
    (root / "cpu.max").write_text("max 100000")
    (root / "memory.max").write_text("max")
    result = resource_snapshot(root, proc)
    assert result["cpu_max"] == {"quota_usec": None, "period_usec": 100000, "unlimited": True}
    assert result["memory_max_unlimited"] is True
    assert result["memory_max_bytes"] is None


@pytest.mark.parametrize("quota", ["0 100000", "200000 0", "200000", "NaN 100000"])
def test_invalid_cpu_limit_is_not_a_measured_quota(tmp_path, quota):
    root, proc = fixture_cgroup(tmp_path)
    (root / "cpu.max").write_text(quota)
    (root / "memory.max").write_text("invalid")
    result = resource_snapshot(root, proc)
    assert all(value is None for value in result["cpu_max"].values())
    assert result["memory_max_unlimited"] is None
    assert result["status"] == "partial"


@pytest.mark.parametrize("field", ["container_id", "pid1_start_ticks", "cgroup_inode", "boot_id"])
def test_replaced_restarted_or_unidentified_container_invalidates_all_deltas(tmp_path, field):
    before = fixture_snapshot(tmp_path)
    after = copy.deepcopy(before)
    after["identity"].pop(field)
    result = resource_delta(before, after)
    assert result["identity_matches"] is False
    assert result["status"] == "unavailable"
    assert all(v is None for group in result["counter_deltas"].values() for v in group.values())


def test_valid_same_lifetime_counter_deltas_preserve_resets_and_boundary_memory(tmp_path):
    before = fixture_snapshot(tmp_path)
    after = copy.deepcopy(before)
    after["cpu_stat"]["usage_usec"] += 50
    after["cpu_stat"]["nr_throttled"] = 1
    after["memory_current_bytes"] = 99999
    result = resource_delta(before, after)
    assert result["identity_matches"] is True
    assert result["counter_deltas"]["cpu_stat"]["usage_usec"] == 50
    assert result["counter_deltas"]["cpu_stat"]["nr_throttled"] is None
    assert result["counter_resets"] == ["cpu_stat.nr_throttled"]
    assert result["before"]["memory_current_bytes"] == 12345
    assert result["after"]["memory_current_bytes"] == 99999
    assert result["status"] == "partial"
    assert result["visible_limits_match"] is True
    after["cpu_max"]["quota_usec"] = 400000
    assert resource_delta(before, after)["visible_limits_match"] is False


def qualifier_without_docker():
    definitions = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/qualify_container.py"))
    return object.__new__(definitions["ContainerQualification"])


def test_exact_container_exec_never_attaches_to_another_service_by_name(tmp_path):
    qualifier = qualifier_without_docker()
    qualifier.override = tmp_path / "synthetic-override.json"
    calls = []
    sample = fixture_snapshot(tmp_path)

    def compose(args, label, **kwargs):
        calls.append((args, label, kwargs))
        return subprocess.CompletedProcess(args, 0, "a" * 64 + "\n", "")

    def execute(args, label, **kwargs):
        calls.append((args, label, kwargs))
        value = "private" if args[1] == "inspect" else sample
        return subprocess.CompletedProcess(args, 0, json.dumps(value), "")

    qualifier.compose, qualifier.execute = compose, execute
    result = qualifier.resource_snapshot("before")
    assert calls[0][0] == ["ps", "-q", "model"]
    assert calls[1][0] == [
        "docker", "inspect", "--format", "{{json .HostConfig.CgroupnsMode}}", "a" * 64,
    ]
    assert calls[2][0][:5] == ["docker", "exec", "a" * 64, "python", "-c"]
    assert all(call[2] == {"timeout": 5} for call in calls)
    assert result["identity"]["container_id"] == "a" * 64
    assert result["probe_wall_seconds"] >= 0


@pytest.mark.parametrize("mode", ["host", "", None])
def test_host_or_unknown_docker_namespace_never_executes_cgroup_read(tmp_path, mode):
    qualifier = qualifier_without_docker()
    qualifier.override = tmp_path / "synthetic-override.json"
    qualifier.compose = lambda args, *_a, **_k: subprocess.CompletedProcess(args, 0, "a" * 64, "")

    def inspect_only(args, *_args, **_kwargs):
        assert args[1] == "inspect"
        return subprocess.CompletedProcess(args, 0, json.dumps(mode), "")

    qualifier.execute = inspect_only
    result = qualifier.resource_snapshot("before")
    assert result["status"] == "unavailable"
    assert result["reason"] == "private_cgroup_namespace_unverified"
    assert "cpu_stat" not in result


def test_unconfigured_or_timed_out_probe_cannot_mask_original_model_failure(tmp_path):
    qualifier = qualifier_without_docker()
    assert qualifier.resource_snapshot("before")["reason"] == "stack_unconfigured"
    qualifier.override = tmp_path / "synthetic-override.json"

    def offline(*args, **kwargs):
        raise TimeoutError("raw sensitive provider detail")

    qualifier.compose = offline
    result = qualifier.resource_snapshot("after")
    assert result["error_type"] == "TimeoutError"
    assert result["status"] == "unavailable"
    assert "sensitive" not in json.dumps(result)
    assert resource_delta(None, result)["status"] == "unavailable"


def test_subprocess_probe_timeout_preserves_original_model_exception_and_artifact(tmp_path):
    qualifier = qualifier_without_docker()
    qualifier.override = tmp_path / "synthetic-override.json"
    qualifier.output = tmp_path
    qualifier.stack = "restored"
    qualifier.records = []
    qualifier.args = SimpleNamespace(model_cpus=2.0)
    qualifier.submit = lambda *_args, **_kwargs: "inc-model-failure"
    qualifier.request = lambda *_args, **_kwargs: {"events": []}

    def probe_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(["docker"], 5, output="private text")

    def original_failure(_incident):
        raise RuntimeError("original model failure")

    qualifier.compose = probe_timeout
    qualifier.complete = original_failure
    with pytest.raises(RuntimeError, match="original model failure"):
        qualifier.agent_case()
    report = json.loads((tmp_path / "model-latency.json").read_text())
    assert report["failure_type"] == "RuntimeError"
    resources = report["model_container_resources"]
    assert resources["before"]["error_type"] == "TimeoutExpired"
    assert resources["after"]["error_type"] == "TimeoutExpired"
    assert resources["status"] == "unavailable"
    assert "private text" not in json.dumps(report)
