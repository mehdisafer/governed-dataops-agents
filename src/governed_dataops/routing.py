"""Deterministic fixed-width queues; reconfiguration requires a drained target route.

The SHA-256 mapping avoids Python hash randomization. The database persists the
chosen queue on first incident admission, so changing the configured partition
count cannot silently move an existing target or an in-flight Temporal workflow.
"""

import hashlib


def queue_for_slot(base: str, count: int, slot: int) -> str:
    if count < 1 or not 0 <= slot < count:
        raise ValueError("invalid partition slot")
    return base if count == 1 else f"{base}.p{slot:02d}"


def queue_for_target(base: str, count: int, target_id: str) -> str:
    if count < 1:
        raise ValueError("partition count must be positive")
    digest = hashlib.sha256(target_id.encode("utf-8")).digest()
    slot = int.from_bytes(digest[:8], "big") % count
    return queue_for_slot(base, count, slot)


def queue_for_worker(base: str, count: int, slot: int | None) -> str:
    if count > 1 and slot is None:
        raise ValueError("a partitioned worker requires explicit worker_partition")
    return queue_for_slot(base, count, slot if slot is not None else 0)
