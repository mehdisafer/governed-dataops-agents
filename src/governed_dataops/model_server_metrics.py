"""Defensive observation of llama.cpp b12368 server metrics.

These are process-wide Prometheus counters and boundary gauges, not proven
per-request inference timing or a trace of the internal request queue.
"""

import math

COUNTERS = (
    "llamacpp:prompt_tokens_total",
    "llamacpp:tokens_predicted_total",
    "llamacpp:prompt_seconds_total",
    "llamacpp:tokens_predicted_seconds_total",
)
GAUGES = ("llamacpp:requests_processing", "llamacpp:requests_deferred")
METRICS = frozenset((*COUNTERS, *GAUGES))


def parse_metric_snapshot(text: str) -> dict[str, float]:
    """Accept only unlabelled finite, nonnegative allowlisted numeric samples.

    Duplicate or labelled samples are not silently summed across models/slots.
    The pinned reference uses one local model, but changes in its exporter must
    produce missing metrics rather than guessed totals.
    """
    values: dict[str, float] = {}
    duplicated = set()
    for line in text.splitlines():
        fields = line.strip().split()
        if len(fields) != 2 or fields[0] not in METRICS:
            continue
        name = fields[0]
        try:
            value = float(fields[1])
        except ValueError:
            continue
        if not math.isfinite(value) or value < 0:
            continue
        if name in values:
            duplicated.add(name)
        else:
            values[name] = value
    for name in duplicated:
        values.pop(name, None)
    return values


def model_metric_delta(
    before: dict[str, float] | None,
    after: dict[str, float] | None,
) -> dict:
    """Calculate bounded deltas, retaining nulls for unavailable/reset counters."""
    start, finish = before or {}, after or {}
    deltas: dict[str, float | None] = {}
    reset = []
    for name in COUNTERS:
        a, b = start.get(name), finish.get(name)
        if a is None or b is None or b < a:
            if a is not None and b is not None and b < a:
                reset.append(name)
            deltas[name] = None
        else:
            deltas[name] = round(b - a, 6)
    gauges = {
        name: {"before": start.get(name), "after": finish.get(name)}
        for name in GAUGES
    }
    measured = sum(value is not None for value in deltas.values())
    return {
        "status": "observed" if measured == len(COUNTERS) else (
            "partial" if measured else "unavailable"
        ),
        "exporter": "llama.cpp b12368 --metrics",
        "counter_deltas": deltas,
        "boundary_gauges": gauges,
        "available_counter_count": measured,
        "total_counter_count": len(COUNTERS),
        "counter_resets": reset,
        "limits": [
            "Process-wide server totals may include other requests; request exclusivity is unverified.",
            "Two boundary gauge snapshots cannot establish transient server queue waits or peaks.",
            "Missing, duplicated, labelled and reset samples are unavailable, never zero.",
            "Server prompt/predict seconds exclude some client transport and validation work.",
            "No model, prompt, deadline, retry or semantic acceptance threshold was changed.",
        ],
    }
