# Fixed target partitions — opt-in, experimental

## Goal and evidence level

The reference now contains **opt-in, fixed-width target routing** on one
Temporal namespace. Existing deployments keep their original single
`governed-dataops-v1` queue and unchanged workflow implementation.

SHA-256 deterministically assigns a target ID to a queue such as
`governed-dataops-v1.p00` or `.p01`. Admission stores the first route in the
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

```dotenv
DATAOPS_TASK_QUEUE=governed-dataops-v1
DATAOPS_PARTITION_COUNT=2
DATAOPS_PARTITION_ADMISSION_LIMIT=1
DATAOPS_MAX_PENDING_INCIDENTS=2
```

Start separate worker processes with identical trusted application and Temporal
connections but explicit queue affinity:

```dotenv
# Worker for partition 0
DATAOPS_WORKER_PARTITION=0
# Worker for partition 1
DATAOPS_WORKER_PARTITION=1
```

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

## Qualification observations and remaining work

**Implemented and tested:** fixed-width SHA-256 target queue routing, first-admission
transactional route binding, per-(environment, scope, partition) capacity,
fail-closed worker ownership, legacy-drain refusal and duplicate-event identity.
The single-queue configuration remains the default.

**Real-service qualification observed (16 November):** [GitHub Actions PR #14
run 43980366884](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43980366884)
reported `two_partition_recovery_and_isolation` **passed (29.409 s)**.
It used actual Temporal workers on two distinct queues, a stopped queue owner,
a signed approval buffered during the outage, another queue completing a
lost-response reconciliation within the declared 45-second bound, a replica
added to the unaffected queue, resumed target work and fresh business receipts.
The source-equivalent [PR #14](https://github.com/mehdisafer/governed-dataops-agents/pull/14)
was merged at `585de77`. CI logs and retained histories are source-bound to
the executed PR merge preview; do not reinterpret them as arbitrary topology
or multi-host evidence.

**Additional negative regressions now integrated and tested (17 November):**
[PR #15](https://github.com/mehdisafer/governed-dataops-agents/pull/15)
merged at `32ec8a74853032c98e1d36f61a048fe41ce8581c`.
Its actual SQLite/Ed25519 tests reject a legitimate approval for target/partition
A when replayed on B, forged plan/route envelope bindings, a wrong worker's
activity, and silent re-sharding after a completed incident. They assert
**zero unauthorized target/effect mutations** and that correctly signed,
correctly owned work still succeeds. They are **unit/cryptographic regression
evidence**, not another separate full two-queue Temporal execution. That real
integration was observed in the earlier PR #14 run and again on the
[merged security-guard main run #43988865699](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43988865699)
(`governance` job SUCCESS); its model-value gate still FAILED.

**Still unverified:** isolation of the shared local model's latency/throughput
under per-partition inference saturation; dynamic repartitioning or multi-host
availability; recovery across a changed worker build; hostile-tenant isolation.
The reference remains experimental and the independent frozen model-value
criterion is still failed. The current acceptance evidence and outstanding
conditions are maintained in [issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1).
