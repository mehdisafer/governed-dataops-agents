# Fixed target partitions — opt-in, experimental

## Goal and evidence level

The reference now contains **opt-in, fixed-width target routing** on one
Temporal namespace. Existing deployments keep their original single
\`governed-dataops-v1\` queue and unchanged workflow implementation.

SHA-256 deterministically assigns a target ID to a queue such as
\`governed-dataops-v1.p00\` or \`.p01\`. Admission stores the first route in the
same SQLite transaction as the incident and execution intent. Later incidents
for that target must keep the same route, even after previous work terminates.
Event retries also preserve the original mode, target, and route.

A partition worker checks that its configured queue is the stored target
owner **before** collecting evidence, diagnosing, authorizing, executing,
verifying or writing workflow phases. The existing target policy additionally
checks the signed approval, environment, scope, evidence revision, budget,
idempotency key and effect receipt. A worker replica may subscribe to the
same partition queue without changing target/effect identities.

## Single-host example

Use a fixed topology and explicit admission budgets for the API:

\`\`\`dotenv
DATAOPS_TASK_QUEUE=governed-dataops-v1
DATAOPS_PARTITION_COUNT=2
DATAOPS_PARTITION_ADMISSION_LIMIT=1
DATAOPS_MAX_PENDING_INCIDENTS=2
\`\`\`

Start separate worker processes with identical trusted application and Temporal
connections but explicit queue affinity:

\`\`\`dotenv
# Worker for partition 0
DATAOPS_WORKER_PARTITION=0
# Worker for partition 1
DATAOPS_WORKER_PARTITION=1
\`\`\`

A multi-partition worker without an explicit slot **refuses startup**.
The same queue can have additional worker replicas for extra capacity.
The required global admission limit is at least the partition count multiplied
by the per-partition budget. Both global admission and each queue reservation
are enforced within the authenticated **(environment, scope)**, preserving
PR #10's scoped capacity. One partition cannot consume another partition's
reserved *admission* allocation inside that scope.

The data store still uses one SQLite WAL and model service. **Per-partition
model latency, persistent admission during an old unpartitioned backlog, and
multi-host availability are not established by this quota mechanism.**

## Changes and recovery

- Never silently change the partition count on a running installation.
  Earlier routes remain bound for the lifetime of a target. A changed
  assignment is rejected rather than silently re-sharding workflows.
- First drain existing unpartitioned pending incidents. Partition activation
  is refused while such incidents are active. An existing legacy target has
  no partition binding and must not be silently reassigned.
- A missing or wrong worker ownership prevents any activity from issuing a
  model or effect request. Reconciliation must use the original target and
  action key; retrying under a new route/identity is not recovery.
- When adding a replica, keep its partition queue, Temporal namespace, build
  compatibility and role credentials consistent. An in-flight approval must
  remain signed and bound to the original target/plan/revision.
- There is no automated target rebalancing or rollback from partition queues
  to the original single queue. Drain work and review queued histories,
  approvals and receipts before reverting the topology.

## Status and required qualification

**Implemented:** deterministic queue mapping, transactional route binding,
sticky event intent, per-queue admission capacity and activity ownership guard.
The single-queue mode retains the previous behavior.

**Unit-tested on this branch:** SQLite admission, retry and route integrity,
wrong-worker/legacy-drift denial, deterministic worker slots and ASGI dispatch.
The Temporal client used by the ASGI test is a fake; these tests do not
constitute a real multi-worker integration.

**Not yet demonstrated:** real Temporal workers on two distinct queues,
pending-approval handover after a restart, concurrent effects on both
partitions, lost-response reconciliation across worker replicas, partition A
saturation while partition B proceeds within a declared latency bound, and
isolation of local-model inference capacity. Retain genuine source-correlated
workflow histories, before/after business rows, effect receipts, resource
measurements and cleanup before claiming partitioning acceptance.

Partition safety is independent of the separate failed LLM-value benchmark;
both remain tracked in [issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1).
