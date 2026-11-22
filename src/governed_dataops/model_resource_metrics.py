"""Bounded cgroup-v2 observations for the exact private model container.

Only visible container counters are measured. Host/ancestor contention,
request-exclusive CPU time and a causal explanation are not inferred.
This module is stdlib-only so its exact source can run via bounded docker exec.
"""

import json
import re
from pathlib import Path

CPU_COUNTERS = (
    "usage_usec", "user_usec", "system_usec", "nr_periods", "nr_throttled", "throttled_usec",
)
MEMORY_COUNTERS = ("low", "high", "max", "oom", "oom_kill", "oom_group_kill")
IDENTITY_FIELDS = ("container_id", "boot_id", "pid1_start_ticks", "cgroup_device", "cgroup_inode")


def bounded_text(path: Path) -> str:
    with path.open("rb") as stream:
        value = stream.read(65537)
    if len(value) > 65536:
        raise ValueError("resource observation exceeds bounded size")
    return value.decode("ascii")


def unsigned(value: str) -> int | None:
    return int(value) if re.fullmatch(r"[0-9]{1,20}", value) else None


def keyed_counters(value: str, allowed: tuple[str, ...]) -> dict[str, int | None]:
    result = dict.fromkeys(allowed)
    seen = set()
    for line in value.splitlines():
        fields = line.split()
        if not fields or fields[0] not in result:
            continue
        name = fields[0]
        result[name] = unsigned(fields[1]) if len(fields) == 2 and name not in seen else None
        seen.add(name)
    return result


def resource_snapshot(
    root: Path = Path("/sys/fs/cgroup"), proc: Path = Path("/proc"),
) -> dict:
    """Read a v2 namespace root; the caller must also verify Docker private mode."""
    result = {"schema_version": 1, "status": "unavailable", "errors": {}}

    def read(path: Path, label: str) -> str | None:
        try:
            return bounded_text(path)
        except (OSError, ValueError, UnicodeError) as exc:
            result["errors"][label] = type(exc).__name__
            return None

    membership = read(proc / "self/cgroup", "cgroup_membership")
    if membership is None or membership.strip() != "0::/" or not (root / "cgroup.controllers").is_file():
        result["reason"] = "private_cgroup_v2_namespace_unverified"
        return result
    result["cgroup_version"] = 2
    result["cpu_stat"] = keyed_counters(read(root / "cpu.stat", "cpu.stat") or "", CPU_COUNTERS)
    result["memory_events"] = keyed_counters(
        read(root / "memory.events", "memory.events") or "", MEMORY_COUNTERS,
    )
    for filename in ("memory.current", "memory.max"):
        raw = read(root / filename, filename)
        raw = raw.strip() if raw is not None else None
        result[filename.replace(".", "_") + "_bytes"] = unsigned(raw) if raw is not None else None
        if filename == "memory.max":
            result["memory_max_unlimited"] = (
                raw == "max" if raw == "max" or (raw is not None and unsigned(raw) is not None) else None
            )
    raw = read(root / "cpu.max", "cpu.max")
    fields = raw.split() if raw is not None else []
    quota = unsigned(fields[0]) if len(fields) == 2 else None
    period = unsigned(fields[1]) if len(fields) == 2 else None
    valid_quota = quota is not None and quota > 0
    unlimited = len(fields) == 2 and fields[0] == "max"
    valid = (valid_quota or unlimited) and period is not None and period > 0
    result["cpu_max"] = {
        "quota_usec": quota if valid else None,
        "period_usec": period if valid else None,
        "unlimited": unlimited if valid else None,
    }
    identity = {}
    boot = read(proc / "sys/kernel/random/boot_id", "boot_identity")
    if boot is not None and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", boot.strip()):
        identity["boot_id"] = boot.strip()
    process = read(proc / "1/stat", "process_identity")
    if process is not None:
        # comm may contain spaces or parentheses; fields after its final ')' start at field 3.
        fields = process.rsplit(")", 1)[-1].split()
        start = unsigned(fields[19]) if ")" in process and len(fields) >= 20 else None
        if start is not None:
            identity["pid1_start_ticks"] = start
    try:
        info = root.stat()
        identity.update(cgroup_device=info.st_dev, cgroup_inode=info.st_ino)
    except OSError as exc:
        result["errors"]["cgroup_identity"] = type(exc).__name__
    result["identity"] = identity
    observations = [
        *result["cpu_stat"].values(), *result["memory_events"].values(),
        result["memory_current_bytes"], result["memory_max_unlimited"],
        result["cpu_max"]["period_usec"],
    ]
    complete = all(x is not None for x in observations) and len(identity) == 4
    result["status"] = "observed" if complete else (
        "partial" if any(x is not None for x in observations) else "unavailable"
    )
    return result


def resource_delta(before: dict | None, after: dict | None) -> dict:
    """Compare numeric counters only with a verified stable container lifetime."""
    start, finish = before or {}, after or {}
    a, b = start.get("identity", {}), finish.get("identity", {})
    identity_matches = all(a.get(k) is not None and a.get(k) == b.get(k) for k in IDENTITY_FIELDS)
    identity_matches = identity_matches and start.get("cgroup_version") == finish.get("cgroup_version") == 2
    identity_matches = identity_matches and (
        start.get("cgroup_namespace_mode") == finish.get("cgroup_namespace_mode") == "private"
    )
    resets = []
    counters = {}
    for section, names in (("cpu_stat", CPU_COUNTERS), ("memory_events", MEMORY_COUNTERS)):
        counters[section] = {}
        for name in names:
            left, right = start.get(section, {}).get(name), finish.get(section, {}).get(name)
            valid = type(left) is int and type(right) is int and left >= 0 and right >= left
            if identity_matches and type(left) is int and type(right) is int and right < left:
                resets.append(section + "." + name)
            counters[section][name] = right - left if identity_matches and valid else None
    count = sum(value is not None for group in counters.values() for value in group.values())
    total = len(CPU_COUNTERS) + len(MEMORY_COUNTERS)
    return {
        "status": "observed" if count == total else ("partial" if count else "unavailable"),
        "identity_matches": identity_matches,
        "visible_limits_match": (
            start.get("cpu_max", {}).get("period_usec") is not None
            and start.get("memory_max_unlimited") is not None
            and all(start.get(k) == finish.get(k) for k in (
                "cpu_max", "memory_max_bytes", "memory_max_unlimited",
            ))
        ),
        "before": before, "after": after,
        "counter_deltas": counters, "counter_resets": resets,
        "available_counter_count": count, "total_counter_count": total,
        "limits": [
            "Container-wide counters include probe overhead and other work, not request-exclusive CPU time.",
            "Visible cpu.max and cpu.stat do not expose ancestor quotas or prove absence of host contention.",
            "Boundary memory.current samples do not measure transient memory peaks.",
            "Missing samples, changed container/process identities and reset counters remain null.",
            "Resource correlation does not establish the cause of model latency or a verified mitigation.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(resource_snapshot()))
