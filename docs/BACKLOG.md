# Remaining acceptance work

## Starting point and rules

The clean native integration run on
`f1e6e2f3800242ec210145680261da8ab60f38b4` finished with **14/18 selected gates passing**
and a failed overall result. The heldout agent passed 2/10 cases; the competent
runbook passed 10/10. All twenty final business states were observed, with no
unknown or benchmark-unjustified effects. Source remained unchanged and all
tracked direct children stopped. This backlog addresses the remaining gaps; it
does not reopen or relabel the original result. Sources:
[run](../evidence/qualification-f1e6e2f/run.json),
[results](../evidence/qualification-f1e6e2f/results.json),
[comparison](../evidence/qualification-f1e6e2f/comparison.json), and
[the consolidated evaluation](EVALUATION.md).

All prioritized work items below are **open**. Priorities describe evidence needed
before the corresponding acceptance claim; they do not mean that changes have been
implemented or validated. Preserve v1 results, failures and hashes. Keep the
baseline, original Pydantic contracts, complete-evidence requirement, signed
approval, live policy checks, fixed effect keys, reconciliation and absence of
model tools/provider fallback. Future work must not obtain a green result by
relaxing those controls or excluding failed attempts.

## Post-run harness correction

Independent review found that the v1 conjunction was unsatisfiable: a perfect
N/N heldout baseline was required at the same time as an agent score strictly
greater than N on those N cases. **Semantics 1.1 is implemented and 61 focused
synthetic harness tests passed; native requalification has not been performed.** It retains
five-case strict reference competence, changes heldout baseline gating to complete safe paired
measurement, preserves the agent's strict quality and strictly-greater value
requirements, and checks exact case identities and denominators. Pre-admission
business state, recomputed scores, permitted effects and unchanged-state
abstentions are validated. The
[qualification tests](../tests/test_qualification.py) retain the original closure
and cleanup guards alongside new comparison/safety cases. See
[the correction specification](EVALUATION.md#post-run-harness-correction-semantics-11).

Focused unit verification is separate from a new native run. The original
14/18 result, 2/10 versus 10/10 comparison and version 1.0 artifacts must remain
unchanged. The current corpus still has a 10/10 baseline ceiling, so this logic
correction alone cannot demonstrate agent value. The open items below therefore
remain necessary.

The separate hosted frozen evaluation at `924dd24` scored agent 1/10 versus runbook 10/10; the original 2/10 result remains an independent historical failure, not a score to average or replace.

## Prioritized open work

| Order | Priority | Item | Current missing claim |
| --- | --- | --- | --- |
| 1 | P0 | Reserve evaluation v2 before new tuning | An independent result for any future changed candidate |
| 2 | P0 | Observe rejected/unfinished responses | An explanation of output truncation and unreported server work |
| 3 | P0 | Diagnose Temporal reporting and workflow-task delays | Predictable bounded end-to-end failure propagation |
| 4 | P0 | Localize inference slowdown, then improve completion | Reliable diagnostic availability within the declared budget |
| 5 | P0 | Qualify target partitioning and worker additions | Business invariants under partition routing, ownership changes and saturation |
| 6 | P1 | Retain hosted browser/container qualification and assess remaining production boundaries | The tested single-host reference passes its declared gates; production topology, multi-host guarantees and model quality remain unproven |
| 7 | P0 for an LLM-value claim | Measure useful advantage over a competent baseline | Additional operational benefit from inference |
| 8 | P2 | Replay between clean identified revisions | A clean-version upgrade claim beyond the current retained histories |

## 1. Reserve evaluation v2 before candidate changes

**Evidence gap.** All v1 labels, responses and failures are now known. Reusing
v1 as a tuning target and then calling it heldout would invalidate the claimed
separation. Earlier diagnostic-only trials also exposed the log-injection
template. See [corpus boundaries](EVALUATION.md#corpus-separation-and-strict-scoring).

**Next work.** Keep v1 as an immutable regression corpus and retain its failed
qualification. Before new prompt, schema, model or runtime tuning, create a
versioned development set and a separately reserved evaluation set, with
provenance, expected outcomes, business invariants, budgets and scoring rules.
Generate reproducible development requests with fixed synthetic identities and
timestamps when comparing performance, so incidental context changes are not
confounded with the intended variable. Freeze the candidate source, model bytes,
command, prompt and generation schema before the new reserved run.

**Acceptance evidence.** A new corpus manifest and candidate hash, all scheduled
attempts retained, the unchanged runbook evaluated on the same target conditions,
and a fresh clean-source run. Report diagnostic availability, conditional
correctness, strict success and missing usage separately. The old 2/10 result
remains visible. A different workload or benefit criterion must be declared
before observing its evaluation results.

## 2. Preserve enough evidence for unfinished responses

**Observed gap.** Clean-run development quality returned 300 output tokens and
raised `OutputTokenLimitExceeded` after 51.819624 seconds. Its unfinished response
text and exact unfinished field were not retained. The eight heldout timeouts
have no client-observed complete response or usage. Their zero token counters
are not zero inference cost. Source:
[development cases](../evidence/qualification-f1e6e2f/cases-development-agent.json)
and [heldout cases](../evidence/qualification-f1e6e2f/cases-heldout-agent.json).

**Next work.** Add bounded observability for synthetic development requests:
request-to-server correlation, prompt and generation timing, response finish
reason, observed/accepted distinction, cancellation request and acknowledgement,
and complete versus partial usage. Where the SDK exposes rejected output,
retain a bounded sanitized fragment or artifact with a hash and truncation
marker. Never copy role tokens, private keys or authorization headers into these
artifacts. Do not log unrestricted real-world input as a shortcut.

**Acceptance evidence.** A deliberately incomplete synthetic response is retained
as incomplete, cannot become a plan, and includes its actual finish reason and
known usage. A timed-out request records what was observed without inventing
missing tokens or a category. Cancellation can be correlated to server work.
These observations must remain outside the business authorization path.

## 3. Investigate Temporal transport and late workflow-task timeouts

**Observed gap A.** In heldout-06, the diagnostic failure was audited at
13:12:49.896876, but escalation was audited 95.514681 seconds later. Original
history event 21 records a non-retryable activity failure; events 23–24 show a
workflow task running for an observed 90.135327 seconds before its start-to-close
timeout was recorded, despite a configured 10-second task timeout. Its
replacement task completed in 12.277 ms. The diagnostic itself had one attempt
and did not exceed its 210-second activity limit.

**Observed gap B.** In heldout-10, the model failed locally after 90.096719 seconds.
No accepted `ActivityTaskFailed` appears in its history. The activity eventually
reached its 210-second start-to-close timeout and exhausted its single attempt.
During the gap, the worker logged heartbeat timeouts and an activity-completion
RPC error, `Unavailable` / HTTP/2 `KeepAliveTimedOut`. Case wall time was
210.9171 seconds. These are transport symptoms, not an established root cause.
The exact histories, traces and worker log are in
[full-originals.tar.gz](../evidence/qualification-f1e6e2f/full-originals.tar.gz),
under `qualification-f1e6e2f/`, for incidents
`inc-8412f3b7f3ec4fa6af` and `inc-4d96d5123a32430ca7`.

**Next work.** Correlate activity return, SDK completion-RPC attempts, server
acceptance, workflow-task queue/start/finish, timer processing and terminal audit.
Capture bounded Temporal server/worker diagnostic metrics and CPU profiles on a
synthetic reproduction. Existing resource samples show continued sampling and
300.74 Temporal CPU-seconds over an 88.895-second portion of the first gap;
that directs investigation but does not identify a hot loop or prove saturation.
Distinguish unavailable transport, delayed server processing and blocked worker
execution before changing timeouts, concurrency or retry behavior.

**Acceptance evidence.** A failed diagnostic propagates to a closed terminal
workflow within a separately declared end-to-end budget on a supported runner.
A deliberately interrupted completion acknowledgement remains recoverable and
auditable, produces no extra model attempt beyond the declared budget, and never
repeats an uncertain business effect blindly. Original histories must distinguish
workflow-task recovery from activity retries. A larger timeout alone is not a
root-cause fix.

## 4. Localize inference slowdown before selecting a remedy

**Observed gap.** The heldout agent accepted two proposals, both correct, and
missed eight client response deadlines. That establishes 2/10 availability,
not eight observed semantic errors. The clean-run development quality response
also exhausted its output limit. Model logs show its recent generation speed
falling from approximately 12 tokens/s to below one token/s; they do not separate
the cause. Model peak sampled RSS was 1,889,692 KiB. Final model exit was zero;
no OOM cause is established by these facts. Sources:
[EVALUATION.md](EVALUATION.md#observed-performance-and-temporal-delays) and
[resources](../evidence/qualification-f1e6e2f/resources.json).

**Next work.** Begin with the same verified model bytes, command, request,
schema and budgets on development inputs. Measure cold/warm behavior,
prompt processing, model evaluation and native-grammar sampling separately;
correlate CPU quotas/throttling, scheduling, memory pressure, page faults and
I/O where available. Compare inference alone with the full service stack as
separate controlled conditions. Change one justified variable at a time. The
current CPU/RSS counters alone do not establish host pressure or grammar cost.

Only after locating the failure mechanism should a candidate runtime, generation
constraint or model change be proposed. Preserve full Pydantic validation,
evidence citation checks and the finite action catalog. Increasing output
length or duration must be justified against a declared operating budget, not
used to erase inconvenient failures.

**Acceptance evidence.** Repeated development requests return complete valid
proposals within predeclared budgets, with measured request availability and
latency distributions. Then the frozen candidate faces evaluation v2 with all
attempts retained. Conditional correctness alone, an isolated successful request,
or a faster synthetic schema benchmark cannot close this item.

## 5. Qualify target partitioning and worker additions

**Implementation progress — candidate branch, not full acceptance.** The
opt-in fixed-width router records a target's initial Temporal queue in its
durable admission transaction and refuses silent route drift. Per-queue quotas
are enforced inside the independently scoped `(environment, scope)`
admission fence already merged in PR #10. Tests cover legacy drain refusal,
stable event identity and worker ownership. A real two-queue Temporal profile
is wired into governance CI but must actually execute and preserve business
effects and histories before this criterion is closed. See
[partitioning design](PARTITIONING.md).



**Mandatory acceptance gap.** The original scope requires preserving business
invariants when targets are partitioned and workers are added. The
source-level admission fix from [PR #10](https://github.com/mehdisafer/governed-dataops-agents/pull/10), now merged at `33a8eba`,
implements independent `(environment, scope)` admission budgets in one durable
SQLite transaction. The exact source `8ab185f` passed 247 core tests,
twelve real governance checks, ten container checks and infrastructure checks,
but its frozen model evaluation still **failed**. Concurrent tests cover two
scopes, globally immutable event identity and independent capacity recovery.
This is **not** a dedicated Temporal routing or worker-saturation qualification;
do not close
this P0 criterion until the actual workflow/worker/target evidence below exists. The native test
`two_workers_one_target` proves its specific contention and duplicate-event
invariants with two workers on one task queue and one target. It does not test
partitioning or saturation isolation. This requirement remains open; it is not
conditional on a future deployment choice. Source:
[results.json](../evidence/qualification-f1e6e2f/results.json).

**Next work.** Define explicit routing and ownership for each target's environment,
scope and partition, including what happens to in-flight workflows when workers
are added, restarted or reassigned. Keep incident/event identity and canonical
effect keys stable across routing changes. Preserve the single durable workflow
authority, exact signed approval binding to target, scope, plan and revision,
and reconciliation against the correct target's durable effect journal. A stale
route, duplicate delivery or ownership overlap must not create another authority
or authorize an effect on a different partition. Declare how admission and worker
capacity are allocated so saturation in one partition cannot silently consume
another partition's entire service capacity.

**Acceptance evidence.** An initial single-host setup with at least two explicit
target partitions is sufficient to test the requirement; multiple hosts are not
mandatory. Retain routing/ownership metadata and original histories for concurrent
partition traffic, worker additions, a restart or reassignment with an approval
pending, and an ambiguous effect that requires reconciliation. Prove no lost or
duplicate business effect, no cross-partition mutation or approval reuse, and
the same row/revision/duplicate invariants before and after the ownership change.
Saturate one partition while continuing work in the other, with a separately
declared admission/latency bound and recovery check for each. A second worker on
the existing shared queue alone does not close this item.

## 6. Retain hosted browser and container qualification without overstating it

**Original limitation (14 November).** The native Chromium launch failed with `socket() failed: Operation not permitted`; Docker was unavailable and Terraform provider-schema validation did not complete. These failures remain in the [original run](../evidence/qualification-f1e6e2f/results.json) and must not be rewritten as a pass on the old source.

**New scoped evidence (15 November).** CircleCI [hosted governance/browser/infrastructure checks on `924dd24`](https://github.com/mehdisafer/governed-dataops-agents/commit/924dd24780b332b13f24a5394a725ad2c55888ba) reported success for their declared single-host scope. The [corrected real-container reference at `cad9cc6`](https://app.circleci.com/workflow/15f6d873-dc0d-4e83-8d20-d3abf1ec20c9) passed ten platform execution gates, including business effects, paired restoration, secret/network isolation and a real model response. Its separate semantic model result was **incorrect and safely denied** (`diagnostic_quality_passed=false`).

**Remaining evidence.** Retain the original artifacts and screenshots with source/runtime versions and resource limits. Confirm other host or production targets only when explicitly authorized; there has been no production Terraform apply. Multi-host partitioning, untrusted-tenant isolation and an accepted model-value benefit are still unproven. Diagnose the unrelated GitHub Actions runner-allocation error from its actual annotation rather than guessing.

**Acceptance boundary.** The named CircleCI single-host platform and browser execution checks can be reported as passed. That does not qualify a general deployment, high availability, external-system exactly-once effects, or the model's diagnostic accuracy.

## 7. Establish useful LLM value, or retain the experimental label

**Observed gap.** The predeclared advantage criterion failed: 2/10 strict
successes versus 10/10, median 91.42505 versus 5.3503 seconds, and no verified
agent resolution. Model cost excludes compute, energy and human effort.
The target's decisive fields are already machine-readable. Source:
[comparison.json](../evidence/qualification-f1e6e2f/comparison.json).

**Next work.** Decide whether there is a defensible task requiring inference
beyond this finite rule table. If so, define the workload and outcome before
evaluation, preserve a competent baseline and the same governance controls,
and measure the proposed benefit: for example, additional correct diagnostics
on relevant inputs or reduced measured operator effort at comparable safety.
Do not remove baseline capabilities, count explanations as a business benefit,
or treat a correct policy refusal of a wrong proposal as diagnostic success.

**Acceptance evidence.** A predeclared benefit is observed on a new reserved
workload, with adequate replication and all latency, cost, availability and
safety tradeoffs disclosed. A perfect runbook already saturates the current
strict-success criterion; merely matching 10/10 would not establish advantage.
If useful benefit remains absent, retain the agent as an explicitly experimental
component and present the validated governance/runbook capabilities within their
actual scope. Full agent-value acceptance remains open.

## 8. Strengthen replay provenance for future upgrades

**Current boundary.** All 56 histories from the clean native run replayed, as did
26 histories from an earlier revision. The earlier revision had a dirty source
manifest. These are useful concrete replay results, but not a clean released
version-to-version upgrade qualification. Source:
[results.json](../evidence/qualification-f1e6e2f/results.json) and
[prior histories](../evidence/recovery-development/prior-histories.tar.gz).

**Next work.** Before a workflow behavior change, retain histories from an
identified clean prior commit, including waiting approval, invalid/expired
approval, uncertain-effect reconciliation and terminal states. Record old/new
workflow hashes, preserve compatible patch markers and replay the originals
against the candidate.

**Acceptance evidence.** The documented earlier-clean-source histories replay
under the new version, followed by real recovery checks for changed behavior.
This closes only the tested migration scope; arbitrary future compatibility
remains unclaimed.
