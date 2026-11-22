# Remaining acceptance work

## Current remaining gates — 23 November 2026

[PR #25](https://github.com/mehdisafer/governed-dataops-agents/pull/25), merged into executable source
`ea80f2524060fcba745c23e85b344a9ad010b782`, implements and source-qualifies bounded
cgroup-v2 observations on the exact restored private model container.
Both the [PR](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/45082434901) and
[independent main](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/45083502058) executed four platform jobs successfully, including **314 core tests**;
their model comparisons independently
failed at **7/10 strict / 3 resolutions versus runbook 10/10 / 6**.
The [qualification](QUALIFICATION.md), [resource](MODEL_LATENCY.md) and
[evaluation](EVALUATION.md) ledgers preserve their exact original evidence.

- **Implemented and observed:** 12 resource counters, private namespace and
  lifetime/limit identity, bounded collection overhead, missing/reset handling
  and original-error preservation. Source and reachable-history scans passed
  their scoped reviewed-findings gates. These measurement prerequisites no
  longer belong in the backlog as entirely unimplemented probes.
- **Still open in #16:** causal localization of latency variability and an
  effective mitigation with prospectively specified repeated evidence.
  B01–B04 remain unexecuted; the two CI qualifications are not replacements.
- **Still open in #20 / #1:** reliable diagnosis and operational model value.
  Draft [PR #23](https://github.com/mehdisafer/governed-dataops-agents/pull/23) requires a legitimate additional authorized
  task, a capable comparator and unseen data before tuning; it is unchanged.
- **Still open operationally:** shared-model isolation, dynamic ownership
  changes, target-specific/multi-host requirements and owner-side publication
  controls. The bounded two-queue result and source-publication status do not
  establish those guarantees.

The earlier 8/10, 6/10 and timed-out executions remain failed historical
observations, not erased by either new successful response gate.

## Historical post-instrumentation P0 checkpoint — 17 November 2026

[PR #17](https://github.com/mehdisafer/governed-dataops-agents/pull/17) merged as [`263a6c1c7226`](https://github.com/mehdisafer/governed-dataops-agents/commit/263a6c1c72260c7be6ba7ba7aeb1a4a891b7f41f). The original [GitHub Actions #43990582623](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43990582623) qualified the exact PR source tree: **Core 284 tests/Ruff, native governance (including fixed two-queue Temporal), ten container checks, Infrastructure, and both CircleCI source/security jobs PASS**. The mandatory **model evaluation FAILED: agent 6/10 versus runbook 10/10**, ten responses observed, no measured advantage. This is an instrumentation improvement, not a candidate that meets agent quality. Historical independent model scores 7/10 (twice on different sources), 2/10 and 1/10 remain original failed/limited records, not a pooled trend.

The corrected `model-latency.json` now attributes **17.568490s** to the active *restored* Compose stack rather than the first project's startup, while documenting total agent gate **69.936369s**, inclusive `Agent.run` **67.004099s**, and explicitly unknown inference-only/server-queue timings. Provenance and partial-failure reporting have improved; **no model server root cause, p95 reliability distribution, prospective unseen evaluation v2 or model-value benefit has been demonstrated**.

**Independent post-merge `main` proof:** [GitHub Actions run #43992090061](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43992090061) completed on exact merged source `263a6c1c72260c7be6ba7ba7aeb1a4a891b7f41f`. **Core 284 tests/Ruff, Governance, Containers (ten platform checks) and Infrastructure all SUCCESS; model-evaluation FAILED**, so overall workflow conclusion was **failure**. The [original mainline model artifact #14288013914](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43992090061/artifacts/14288013914) was downloaded and its original `comparison.json` verified (ZIP integrity PASS, 120 entries, SHA-256 `dd572cb2572d0b5ecc9e55c127522655a47104a24881db7adf691098934744e8`): runbook **10/10**, model **6/10** strict, all ten responses observed, **model resolved 2**, runbook resolved **6**; model case median/p95 **24.6661/28.0617s**, runbook **3.93485/6.2401s**, and zero observed unjustified/unknown effects. These are distinct measurements from the PR-head 6/10 run, which resolved three rather than two cases. Both remain failures of the unwaived value criterion.

[Original mainline container #14287384372](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43992090061/artifacts/14287384372) was also downloaded and integrity-checked (146 entries, SHA-256 `38ea1171dbfb9ed3feeeff89b88149d83a9934b017f3d322976220c82632333a`). Its source remained unchanged, credential scan passed, ten platform checks passed and semantic `diagnostic_quality_passed=false`. `commands.json` confirms initial stack **17.926662s**, restored stack **18.077121s**; `model-latency.json` correctly selects the **18.077121s restored stack**, with full agent gate **66.719662s**, inclusive `Agent.run` **63.465644s**, client slot wait **0.000016s** and independent typed business validation **0.000022s**. Inference-only and llama.cpp server queue time remain null/unobserved.

Continue [latency investigation #16](https://github.com/mehdisafer/governed-dataops-agents/issues/16), strict [V1 #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1), and the separate fixed-partition versus shared-model saturation limits. No budget change, provider fallback or unapproved production deployment was made.

## Historical starting point and rules

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

## Historical post-run harness correction

Independent review found that the v1 conjunction was unsatisfiable: a perfect
N/N heldout baseline was required at the same time as an agent score strictly
greater than N on those N cases. **Semantics 1.1 is implemented and 61 focused
synthetic harness tests passed at that checkpoint; native requalification had not yet been performed.** It retains
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

The separate hosted frozen evaluation at `924dd24` scored agent 1/10 versus runbook 10/10; the original 2/10 result remains an independent historical failure, not a score to average or replace. **A third source-bound hosted evaluation on `8ab185f` returned 10/10 observed responses but only 7/10 strict correct cases versus runbook 10/10**; all three incorrect proposals falsely requested schema migration even though the typed source and accepted schema were equal. See [forensic readback](EVALUATION.md#earlier-original-hosted-model-artifact-forensic-readback--17-november-2026) and [issue #12](https://github.com/mehdisafer/governed-dataops-agents/issues/12). This is still failed comparative acceptance, not a reason to average results or tune on formerly reserved labels.

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

## 5. Partition routing — delivered single-host evidence and open limits

**Implemented and source-tested, not production/general-topology accepted.** [PR #14](https://github.com/mehdisafer/governed-dataops-agents/pull/14) integrated opt-in deterministic SHA-256 target-to-queue routing, durable first-admission owner identity, per-`(environment,scope,partition)` admission reservations and fail-closed worker ownership. [PR #15](https://github.com/mehdisafer/governed-dataops-agents/pull/15) subsequently added actual SQLite/Ed25519 cross-partition signed approval and forged-route negative tests on `main` `32ec8a7`. Source and permission checks retain stable incident/event/effect identities, revision and plan bindings, no unauthorized target mutation and refusal to silently re-shard old target work.

**Executed real Temporal proof:** [PR #14 run #43980366884](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43980366884) passed `two_partition_recovery_and_isolation` on two actual Temporal queues (29.409 seconds), including a stopped owner, buffered approved work, other partition progress during saturated admission, lost-response effect reconciliation, worker replica and resumed work. The [post-merge PR #13 source run #43988865699](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43988865699) again passed governance and the partitioning gate on `9635dbcc`. This is a **bounded, single-host, fixed-partition acceptance**, not broad worker migration or multi-host guarantees.

**Still missing:** shared Qwen/model inference scheduling and latency under one partition's saturation; dynamic repartitioning; cross-build Temporal workflow migration; independent tenant isolation and multi-host availability. Record predeclared per-queue admission/latency/resource bounds and real execution before claiming these behaviors. The selected earlier [single-queue source's two-worker test](../evidence/qualification-f1e6e2f/results.json) remains historical and must not be substituted for the separate executed two-queue trial. See the [current partitioning design](PARTITIONING.md).

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
