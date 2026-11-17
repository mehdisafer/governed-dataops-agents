"""Read-only cgroup-v2 model-container resource observations.

The values are container-wide boundary snapshots, not request-exclusive
CPU/inference timing. All missing, unsupported or reset values stay unknown.
No host path, credential, raw log or command output is included in the report.
"""

CPU_COUNTERS = (
    "gda:cgroup_cpu_usage_usec",
    "gda:cgroup_cpu_nr_periods",
    "gda:cgroup_cpu_nr_throttled",
    "gda:cgroup_cpu_throttled_usec",
)
MEMORY_COUNTERS = (
    "gda:cgroup_memory_oom_total",
    "gda:cgroup_memory_oom_kill_total",
)
GAUGES = (
    "gda:cgroup_memory_current_bytes",
    "gda:cgroup_memory_peak_bytes",
    "gda:cgroup_cpu_quota_usec",
    "gda:cgroup_cpu_period_usec",
)
COUNTERS = (*CPU_COUNTERS, *MEMORY_COUNTERS)
ALLOWED = frozenset((*COUNTERS, *GAUGES))
MAX_CGROUP_COUNTER = (1 << 64) - 1

# This literal is executed ONLY inside the already-running private model
# container, after the existing bounded private /metrics scrape. It reads only
# allowlisted Linux cgroup-v2 files, never the host filesystem or model text.
# Missing v2 files are intentionally not replaced with guessed v1 values.
MODEL_CGROUP_PROBE_SCRIPT = """
def _gda_cgroup_read(path):
    try:
        with open(path, 'rb') as handle:
            data = handle.read(4097)
    except OSError:
        return None
    if len(data) > 4096:
        return None
    try:
        return data.decode('ascii')
    except UnicodeError:
        return None

def _gda_cgroup_emit_pairs(path, names):
    raw = _gda_cgroup_read(path)
    if raw is None:
        return
    seen = set()
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) != 2 or fields[0] not in names or fields[0] in seen:
            continue
        seen.add(fields[0])
        if fields[1].isdecimal():
            print(names[fields[0]], int(fields[1]))

_gda_cgroup_emit_pairs('/sys/fs/cgroup/cpu.stat', {
    'usage_usec': 'gda:cgroup_cpu_usage_usec',
    'nr_periods': 'gda:cgroup_cpu_nr_periods',
    'nr_throttled': 'gda:cgroup_cpu_nr_throttled',
    'throttled_usec': 'gda:cgroup_cpu_throttled_usec',
})
_gda_cgroup_emit_pairs('/sys/fs/cgroup/memory.events', {
    'oom': 'gda:cgroup_memory_oom_total',
    'oom_kill': 'gda:cgroup_memory_oom_kill_total',
})
for _gda_path, _gda_name in (
    ('/sys/fs/cgroup/memory.current', 'gda:cgroup_memory_current_bytes'),
    ('/sys/fs/cgroup/memory.peak', 'gda:cgroup_memory_peak_bytes'),
):
    _gda_raw = _gda_cgroup_read(_gda_path)
    if _gda_raw is not None and _gda_raw.strip().isdecimal():
        print(_gda_name, int(_gda_raw.strip()))
_gda_max = _gda_cgroup_read('/sys/fs/cgroup/cpu.max')
if _gda_max is not None:
    _gda_parts = _gda_max.split()
    if len(_gda_parts) == 2:
        if _gda_parts[0].isdecimal():
            print('gda:cgroup_cpu_quota_usec', int(_gda_parts[0]))
        if _gda_parts[1].isdecimal():
            print('gda:cgroup_cpu_period_usec', int(_gda_parts[1]))
"""


def parse_container_resource_snapshot(text: str) -> dict[str, int]:
    """Accept finite, unsigned, unlabelled allowlisted integer observations."""
    values: dict[str, int] = {}
    duplicates: set[str] = set()
    for line in text.splitlines():
        fields = line.strip().split()
        if len(fields) != 2 or fields[0] not in ALLOWED:
            continue
        name, raw = fields
        # Cgroup counters fit unsigned machine integers. Arbitrarily long or
        # non-ASCII output must not trigger a parser exception in the qualifier.
        if not (raw.isascii() and raw.isdecimal() and len(raw) <= 20):
            continue
        value = int(raw)
        if value > MAX_CGROUP_COUNTER:
            continue
        if name in values:
            duplicates.add(name)
        else:
            values[name] = value
    for name in duplicates:
        values.pop(name, None)
    return values


def model_container_resource_delta(
    before: dict[str, int] | None, after: dict[str, int] | None
) -> dict:
    """Compute source-bound deltas; unknown/reset never becomes zero."""
    start = before if isinstance(before, dict) else {}
    finish = after if isinstance(after, dict) else {}

    def observed(sample: dict, name: str) -> int | None:
        value = sample.get(name)
        return value if type(value) is int and value >= 0 else None

    deltas: dict[str, int | None] = {}
    resets: list[str] = []
    for name in COUNTERS:
        first, last = observed(start, name), observed(finish, name)
        if first is None or last is None:
            deltas[name] = None
        elif last < first:
            deltas[name] = None
            resets.append(name)
        else:
            deltas[name] = last - first

    gauges = {
        name: {"before": observed(start, name), "after": observed(finish, name)}
        for name in GAUGES
    }
    periods = deltas["gda:cgroup_cpu_nr_periods"]
    throttled = deltas["gda:cgroup_cpu_nr_throttled"]
    fraction = (
        round(throttled / periods, 6)
        if periods is not None and throttled is not None
        and periods > 0 and throttled <= periods
        else None
    )
    quota, period = (
        gauges["gda:cgroup_cpu_quota_usec"],
        gauges["gda:cgroup_cpu_period_usec"],
    )
    effective_cpu_limit = (
        round(quota["after"] / period["after"], 6)
        if quota["before"] is not None and period["before"] is not None
        and quota["before"] == quota["after"] and period["before"] == period["after"]
        and period["after"] > 0
        else None
    )
    measured = sum(value is not None for value in deltas.values())
    return {
        "status": "observed" if measured == len(COUNTERS) else (
            "partial" if measured or any(x["after"] is not None for x in gauges.values())
            else "unavailable"
        ),
        "resource_scope": (
            "cgroup v2 mount read inside the restored model container; "
            "mount/namespace attribution not independently verified"
        ),
        "counter_deltas": deltas,
        "boundary_gauges": gauges,
        "available_counter_count": measured,
        "total_counter_count": len(COUNTERS),
        "counter_resets": resets,
        "cpu_throttled_period_fraction": fraction,
        "observed_effective_cpu_limit": effective_cpu_limit,
        "limits": [
            "Container-wide CPU usage and throttling are not request-exclusive.",
            "Throttled microseconds cannot be subtracted from wall time to claim queue delay.",
            "Memory current and peak snapshots do not prove the time of peak pressure.",
            "Missing cgroup-v2 fields, reset counters and unavailable quota remain unknown.",
            "Two snapshots cannot establish transient CPU or memory pressure causality.",
            "The cgroup mount/namespace identity must be independently verified before attributing these counters exclusively to the model container.",
            "No model, timeout, CPU allocation, prompt, retry or policy is modified.",
        ],
    }
