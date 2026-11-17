# Qualification ledger

Updated 17 November 2026. **Platform execution is qualified for the declared synthetic reference checks; full agent-value acceptance is withheld.** A green container workflow verifies its declared infrastructure/effect gates, not comparative diagnosis quality. The original [acceptance issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) remains open. No accepted stable V1 or production-readiness claim follows from the passing subset.

## New server-metric evidence — PR #21, 17 November 2026

| Source and exact execution | Reported result | Limit |
| --- | --- | --- |
| [PR head `44dabbf`](https://github.com/mehdisafer/governed-dataops-agents/commit/44dabbf19de9c223027627a8e493a6ca63490c4a), preview `a636933` (same tree `ce5653be`) | [GitHub Actions #44161986053](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44161986053): **core 292 tests, governance, infrastructure, containers SUCCESS; model-evaluation FAILED** | Process execution and independent agent-quality criterion must remain separate |
| Original real [container artifact #14363268796](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44161986053/artifacts/14363268796) | Private restored-stack llama.cpp metrics **4/4 cumulative counters observed** at **2 CPU**; model-response gate **69.247s**; `container_execution=passed`, `diagnostic_quality_passed=false` | Individual numeric deltas in binary artifact not independently inspected through this connector; no inference-only or server queue peak claim |
| Original [model-evaluation artifact #14363284141](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44161986053/artifacts/14363284141) | **FAILED**: all 10 agent cases attempted, strict agreement and measured advantage absent | Do not infer an exact 0–10 numerator without independently reading its original comparison data |
| [Merged `main` `4ec7adbf`](https://github.com/mehdisafer/governed-dataops-agents/commit/4ec7adbf204955081a4984afc29166d9c8a8e6f2) | [Full GitHub Actions #44163668519](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44163668519) **FAILED** on identical source tree: core **292 tests**, governance and infrastructure **SUCCESS**; containers and model-evaluation **FAILED** | [Container artifact #14363928475](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44163668519/artifacts/14363928475): **4/4** server counters observed but response gate **FAILED in 94.880s**, diagnostic quality false, versus **69.247s PASS** on the PR preview; root cause unknown |

**The independent main execution must not be collapsed into the PR preview's success.** At the same 2-CPU quota and identical executable tree, the container's model-response gate failed after 94.880s with an empty-message `AssertionError`; its mainline metric sampling itself still reported four counters. The mainline model-evaluation separately failed the unwaived strict-quality/value gate. The [original model artifact #14364697423](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44163668519/artifacts/14364697423) remains accessible by GitHub Actions, but the connector did not independently read its binary ZIP to establish a precise case numerator.

The observed server counters improve visibility into prompt/generation workload but are process-wide and only two snapshots. They do not identify the cause of intermittent 2-CPU response delays. The 90-second model deadline, constrained actions, original business checks and existing evaluation failures remain unchanged. [Issues #16](https://github.com/mehdisafer/governed-dataops-agents/issues/16) and [#1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) stay OPEN.

## Most recent source-integrated qualification — 17 November 2026

Merged [PR #17](https://github.com/mehdisafer/governed-dataops-agents/pull/17) established qualified runtime `main` revision [`263a6c1c7226`](https://github.com/mehdisafer/governed-dataops-agents/commit/263a6c1c72260c7be6ba7ba7aeb1a4a891b7f41f). Its testable instrumentation head [`e81309b`](https://github.com/mehdisafer/governed-dataops-agents/commit/e81309b300b579f60298b77d6202ac67ea843ae4) and the reviewed GitHub Actions merge-preview `158e52c5` share identical Git tree `77c18f708010dc51687d5e6022000eb6a05f4d18`. [Original GitHub Actions #43990582623](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43990582623) and the two CircleCI checks were inspected.

| Executed check on identical PR source tree | Observed outcome | Qualification boundary |
|---|---|---|
| Core | **PASS** — 284 Python tests, Ruff | Includes active-restored-stack timing selection and partial-failure regression tests |
| Governance | **PASS** — actual single-host Temporal policies, recovery, browser and two-queue partitioning | Fixed partition queues, not shared-model latency isolation or multi-host guarantees |
| Containers | **PASS** — 10/10 checks, model/Temporal services, business rows, restored pair/cleanup | A real model response was observed but `diagnostic_quality_passed=false` |
| Infrastructure | **PASS** | Static/isolated infrastructure qualification, no cloud apply |
| CircleCI build-and-test / publication-security | **PASS / PASS** at exact `e81309b` | Unit/package/security scope |
| **Frozen model-evaluation** | **FAILED** — agent **6/10**, runbook **10/10** | All ten agent cases were attempted; model value not established |

[Original model-evaluation ZIP artifact #14288370568](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43990582623/artifacts/14288370568) and [real-container ZIP #14288017124](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43990582623/artifacts/14288017124) were downloaded and inspected without rewriting the original results. Source-bound model timing: **69.936369s total agent gate**, **67.004099s `Agent.run`** including transport/inference/native validation, **0.000020s client semaphore** and **0.000023s typed business validation**. The restored Docker stack actually used for the probe started in **17.568490s**, which corrected `model-latency.json` now records; the previous initial stack started in **18.442006s**. Model-only readiness, internal llama.cpp queue time and inference-only time remain **unknown, not zero**. Exact source tree and credential scan passed in the container report.

This is not evidence of improvement in model quality; the earlier guarded-source **7/10** result below and earlier unguarded **7/10**, native **2/10** and hosted **1/10** are separate executions. Only prospective, unseen evaluation can support future model-value claims. PR #17 has no weights/prompt/deadline/authorization change.

**Independent post-merge `main` proof:** [GitHub Actions run #43992090061](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43992090061) completed on exact merged source `263a6c1c72260c7be6ba7ba7aeb1a4a891b7f41f`. **Core 284 tests/Ruff, Governance, Containers (ten platform checks) and Infrastructure all SUCCESS; model-evaluation FAILED**, so overall workflow conclusion was **failure**. The [original mainline model artifact #14288013914](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43992090061/artifacts/14288013914) was downloaded and its original `comparison.json` verified (ZIP integrity PASS, 120 entries, SHA-256 `dd572cb2572d0b5ecc9e55c127522655a47104a24881db7adf691098934744e8`): runbook **10/10**, model **6/10** strict, all ten responses observed, **model resolved 2**, runbook resolved **6**; model case median/p95 **24.6661/28.0617s**, runbook **3.93485/6.2401s**, and zero observed unjustified/unknown effects. These are distinct measurements from the PR-head 6/10 run, which resolved three rather than two cases. Both remain failures of the unwaived value criterion.

[Original mainline container #14287384372](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43992090061/artifacts/14287384372) was also downloaded and integrity-checked (146 entries, SHA-256 `38ea1171dbfb9ed3feeeff89b88149d83a9934b017f3d322976220c82632333a`). Its source remained unchanged, credential scan passed, ten platform checks passed and semantic `diagnostic_quality_passed=false`. `commands.json` confirms initial stack **17.926662s**, restored stack **18.077121s**; `model-latency.json` correctly selects the **18.077121s restored stack**, with full agent gate **66.719662s**, inclusive `Agent.run` **63.465644s**, client slot wait **0.000016s** and independent typed business validation **0.000022s**. Inference-only and llama.cpp server queue time remain null/unobserved.

Keep [#1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) and [#16](https://github.com/mehdisafer/governed-dataops-agents/issues/16) open.

## Earlier guarded-source main qualification — 17 November 2026

The public `main` source after [security PR #13](https://github.com/mehdisafer/governed-dataops-agents/pull/13) is [`9635dbccfe8cfd168f14ee9380eeb1f03e105a0c`](https://github.com/mehdisafer/governed-dataops-agents/commit/9635dbccfe8cfd168f14ee9380eeb1f03e105a0c). Its Git tree `80331e7b1d1a64423182c33b4ad81737ed9b7a48` exactly matches the combined PR source tested by [GitHub Actions #43987760401](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43987760401). The [post-merge main run #43988865699](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43988865699) was separately **completed** and returned overall **failure solely because the mandatory `model-evaluation` job remained red**:

| Exact main job | Observed result | Boundaries |
|---|---|---|
| `core` | **SUCCESS, 272 Python tests**, Ruff and bounded source/security checks | Execution regression, not model quality |
| `governance` | **SUCCESS** — real Temporal workflows, signed-approval refusals, restart/restore, browser and `two_partition_recovery_and_isolation` | Single host, two fixed queues, one shared model service |
| `containers` | **SUCCESS** — real private local model/Temporal/target, paired restore and cleanup | The original report explicitly records `diagnostic_quality_passed=false` |
| `infrastructure` | **SUCCESS** — local Terraform/provider preparation | No production apply |
| `model-evaluation` | **FAILED** — frozen agent strict 7/10 vs competent runbook 10/10; measured advantage absent | Do **not** waive or replace this gate |
| CircleCI `build-and-test` / `publication-security` | **SUCCESS / SUCCESS** at exact `9635dbcc` | Source/unit/security scopes only |

The original [model-evaluation artifact #14286528694](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43988865699/artifacts/14286528694) and [container artifact #14285959973](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43988865699/artifacts/14285959973) were downloaded and ZIP integrity checked. The original comparison observed all **10/10 model responses** and final business states. Agent strict correct actions and outcomes were **7/10**, **3 resolved**, runbook strict **10/10**, **6 resolved**. Agent median **34.08195 s** versus runbook **5.3463 s**; compute/energy/human cost unmeasured. In failed cases **heldout-05, -06 and -10**, the model's impossible typed-state proposals were rejected with `DiagnosticError`, resulting in explicit escalation with **zero business effects**, not successful resolution. The container's one-case model diagnosis was similarly rejected (`diagnostic_quality_passed=false`). The original heldout corpus has been inspected, so new improvement claims require a **prospectively reserved evaluation v2**.

This earlier guarded source preserves [PR #14](https://github.com/mehdisafer/governed-dataops-agents/pull/14) opt-in target queue ownership and real two-queue Temporal qualification, plus [PR #15](https://github.com/mehdisafer/governed-dataops-agents/pull/15) real SQLite/Ed25519 cross-partition approval/route negative tests. Shared-model inference saturation, topology changes, hostile-tenant and multi-host behavior remain **unverified**. The historic native 14/18, agent 2/10, later hosted agent 1/10, and source-specific unguarded 7/10 results below retain their dates and exact sources; no result has been overwritten or averaged.

## Historical scoped admission and frozen evaluation — source of PR #10

Source change [PR #10](https://github.com/mehdisafer/governed-dataops-agents/pull/10) merged into `main` as [`33a8eba54600`](https://github.com/mehdisafer/governed-dataops-agents/commit/33a8eba54600a2c77f80e6cf119eeab85a9c111b). **Exact qualified PR source**: `8ab185fe2daf28624bba9bee47eca03920b154de`. This is an additional source qualification, not a rewrite of earlier runs and not a proof that a later `main` workflow has executed.

The SQLite `Store.record_incident` unfinished-admission count is now filtered by the incident's authenticated `(environment, scope)` under the **same `BEGIN IMMEDIATE` transaction** as insertion. Tests exercise independent admission capacity in two scopes and an independent environment; concurrent arrivals cannot oversubscribe a scope, previously used event identities remain globally immutable, and capacity returns after a terminal incident.

[GitHub Actions run #43976640653](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43976640653) inspected on this exact PR source:

| Executed gate | Observed result | Evidence boundary |
|---|---|---|
| Core | **SUCCESS** — 247 Python tests in 8.10s, Ruff and source checks | Includes the new scoped-admission unit/concurrency tests |
| Governance | **SUCCESS** — twelve named real-service checks | Includes five runbook business cases, stale approvals, restart, same-target worker contention, admission/recovery, paired restore, bounded load, retained replay and browser |
| Containers | **SUCCESS** — ten named platform checks | Real local-model response observed, but `diagnostic_quality_passed=false` |
| Infrastructure | **SUCCESS** | Synthetic local configuration/schema scope, no production `apply` |
| CircleCI build/test and publication security | Both **SUCCESS** on exact PR head | Does not substitute for real model comparison |
| Model evaluation | **FAILED** — heldout agent strict result and advantage gates | All ten agent cases attempted. The frozen runbook measurement passed; exact new agent correct-case count **not inferred from a status alone** |

The model-evaluation job retained original outputs under [GitHub artifact `14281900580`](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43976640653). Its logs explicitly identify `heldout_agent` strict diagnosis/action/outcome mismatch and `measured_agent_advantage` failure. Do not use the passing container model-response gate as semantic success. Prior 2/10 and 1/10 failures retain their own sources and denominators.

**At that PR #10 source**, separate Temporal queue/worker ownership, buffered approvals under reassignment and a second partition under saturation remained unqualified. [Subsequent PR #14 and #15](PARTITIONING.md) implemented and tested a fixed two-queue reference. The current remaining P0 is **shared model inference contention, prospective model evaluation and explicit operational acceptance**, not absence of any two-queue Temporal execution. No stable accepted V1 is claimed.

## GitHub Actions and publication qualification — 16 November 2026

| Source | Observed jobs | Limit |
| --- | --- | --- |
| [`7b709ff`](https://github.com/mehdisafer/governed-dataops-agents/commit/7b709ffdb8440a0b41c3d28e7ee7ec028cac1a8d) | [GitHub Actions full run #43919667084](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43919667084): `core`, `governance`, `containers`, `infrastructure` **SUCCESS**, `model-evaluation` **FAILED** | Ten reserved agent cases attempted but strict diagnosis/action/outcome agreement incomplete; advantage absent; exact count not asserted without artifact-level review |
| [`351817e`](https://github.com/mehdisafer/governed-dataops-agents/commit/351817eeecc969dd13491e592b3510f8ae38ea7d) | [GitHub Actions docs-only run #43924763001](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43924763001): `core` **SUCCESS**, other four runtime jobs **SKIPPED** | 245 passing tests, Ruff, 31/62 raw reviewed Gitleaks findings, no unresolved installed Python licence metadata, dependency audit no known vulnerabilities at scan time |
| `351817e` | CircleCI `build-and-test`, `publication-security` **SUCCESS** | Scanner and wheel results have declared scope and limits; no blanket claim about encrypted/opaque archives or unreachable Git objects |

These results are separate from the 14 November native run and 15 November CircleCI qualification below. The four successful GitHub Actions platform jobs show that runners can now execute; the prior zero-runner cause remains unknown. The 16 November container reported `diagnostic_quality_passed=false` despite a passing execution gate; the frozen model evaluation is **FAILED**. Terraform produced a local plan without `apply`. Public repository visibility is confirmed in GitHub metadata, but `main` has no branch protection and full agent-value V1 acceptance remains open.

## Historical 15 November container qualification

Source: `cad9cc6eb28a70f24e9bf02774a7614cc4cb9631`.
Pipeline: `3cfa3d77-80dc-4d4f-a8b8-f8d0005f9b34`.
[Workflow](https://app.circleci.com/workflow/15f6d873-dc0d-4e83-8d20-d3abf1ec20c9).
Job: `e2a33e1e-cd66-4b3b-bd36-a5efeb5f8698`.

The native Linux VM `.circleci/reference.yml` built and ran the actual application, Temporal and pinned model images. Its ten checks passed. The recorded source files remained unchanged during execution; the credential scan passed and owned-stack cleanup was verified.

| Actual check | Observation |
|---|---|
| Network, identities, secrets and resource limits | Non-root/read-only services, exact role-secret mounts, realized loopback port and backend isolation checked |
| Installed runtime asset identity | Actual model digest/size and installed package/runtime versions verified |
| Freshness | Real target rows and watermark corrected exactly once |
| Transient write ambiguity | Original effect receipt reconciled before fresh business verification |
| Schema incompatibility | Migration refused; no unauthorized effect |
| Quality | Separately authorized quarantine, reported as containment |
| Duplicate delivery | One equivalent business result, without duplicate output |
| Worker restart | Queued durable work completed after restart |
| Paired application/Temporal restoration | Fresh volumes restored; business rows and workflow history equal; duplicate delivery still deduplicated; new incident completed |
| Real model response | Actual local response observed within the unchanged diagnostic budget; this check alone does not require correct diagnosis |

The final report explicitly contains:

```json
{
  "status": "passed",
  "gate": "container_execution",
  "diagnostic_quality_passed": false,
  "model_cpu_override": 4.0,
  "full_acceptance_claimed": false
}
```

The freshness model case proposed a schema migration even though the observed schema versions agreed. Policy denied that wrong proposal. There was a real response and safe enforcement, **not a correct diagnosis or demonstrated model value**. The container script's optional `--require-model-quality` would make that one-case quality failure fatal; the separate frozen comparison remains the stronger mandatory full-acceptance gate.

### Original artifact integrity

SHA-256 values computed from downloaded, unmodified artifacts:

| File under `container/` | SHA-256 |
|---|---|
| `checks.json` | `11f77acc18d775b5bdce7832dc250bbbbfcc020790801c7be9d8b9a58142a196` |
| `cleanup.json` | `e57c8d58ba3ae360554294c3d41c44b8bc7d768f9429bfd59fd2eee19be75e5d` |
| `model-quality.json` | `a4c512881cba680dd04064349dd85bfc113a62eb6449219f3e7042c3df9ab95c` |
| `run.json` | `7d364645d3074e4ff3842ad45b89b16dbc23672effce1a7cbd6c54a713efc907` |

The downloaded set includes 87 original artifacts: source/runtime identities, command logs, business receipts, model trace, before/after histories and cleanup observations. Runtime secrets stayed outside the publishable proof. CircleCI retention is finite; this versioned ledger does not fabricate replacement execution outputs.

## Historical 15 November governance and frozen evaluation

Separate source `924dd24780b332b13f24a5394a725ad2c55888ba` executed in pipeline `2c9ce775-ea93-476c-b770-a28020d4d763`. The full source profile passed 232 tests and its static/security checks. The governance profile passed eight requested checks: actual governance integration; policy/clock/key negative cases; two-worker load/idempotence; ambiguous-write recovery; pending workflow after restart; paired restoration; real browser console; and durable checkpoint. Terraform/provider-schema and isolated local Docker infrastructure checks executed separately without a production apply.

Those governance gates deliberately exercise the deterministic runbook. They do not imply that an inference engine performed those business diagnoses. Subsequent container ownership/network corrections do not retroactively change this earlier source receipt.

The **frozen comparative evaluation failed**. Both engines attempted the reserved cases; incorrect/unavailable diagnoses remain in the original denominator:

| Metric | Runbook | Local agent |
|---|---:|---:|
| Reserved cases | 10 | 10 |
| Strict correct diagnosis/business outcomes | 10/10 | 1/10 |
| Actual model requests attempted | 0 | 10 |
| Actual model responses observed | Not applicable | 8 |
| Observed unauthorized/unsafe effects | 0 | 0 |
| Agent advantage | Baseline | Not demonstrated |

The hosted result is a separate run from the historical 2/10 agent result. It is not evidence of statistically established degradation, nor an opportunity to select only the better run. The corpus is small and within known families. Safe denial of a wrong diagnosis is an authority-control success, but still a diagnostic failure. Zero returned usage on missing responses is not zero compute. Compute, energy and human effort were not monetized.

The existing post-native harness correction separated baseline competence from the held-out comparison, resolving the formerly contradictory requirement that a perfect baseline must also be exceeded on the same ten cases. Strict superiority and exact paired denominators remain required. No prompt/model was retuned against these reserved outcomes during this CI work, no weaker baseline substituted, and parity is not redefined as added value. Any future value claim needs a prospectively specified evaluation and fresh reserved data; see [EVALUATION.md](EVALUATION.md).

## Deployment defects corrected and re-executed

- Manual CircleCI Actions runs may have no GitHub event file. Unknown scope now requests full qualification instead of crashing or suppressing runtime checks.
- Downloaded model files were private to the build user. Immutable assets now have explicit read permissions and a traversable directory; the non-root image build checks actual GGUF/license/provenance access.
- Temporal's runtime resource detector needed a valid execution identity. The image defines the non-root user and its environment rather than running the service as root.
- A configured host port on an internal-only network was not a realized reachable endpoint. Only the API now joins a separate ingress bridge; the exact realized loopback mapping and internal-only backend memberships are asserted.
- Fresh restore volumes could have ownership changed by image copy-up. Explicit `nocopy` mounts preserve the UID established by the scoped initialization service. The paired restore subsequently passed without world-writable permissions or a privileged application.
- The two-CPU model trial timed out and remains retained as failed. The final trial used the documented four-CPU allowance, with the same ninety-second model deadline. A real response was observed, but its quality still failed.

**Network consequence:** model, Temporal, worker and target have no published ports and remain on the internal network. Only API ingress is published to `127.0.0.1:8080`. The API can initiate egress; the whole stack is not air-gapped. There was no `0.0.0.0` host exposure or disabled browser sandbox added to obtain success.

## Historical evidence remains historical

The 14 November native integration at `f1e6e2f3800242ec210145680261da8ab60f38b4` returned nonzero with 14/18 checks. Its agent achieved 2/10 strict reserved successes versus 10/10 runbook; browser/socket and deployment prerequisites were blocked. The [192 original files](../evidence/qualification-f1e6e2f/full-originals.tar.gz), [run metadata](../evidence/qualification-f1e6e2f/run.json), [checks](../evidence/qualification-f1e6e2f/results.json), [comparison](../evidence/qualification-f1e6e2f/comparison.json), [load](../evidence/qualification-f1e6e2f/load.json) and [retained replay development evidence](../evidence/recovery-development/README.md) remain unchanged.

The prior 172-test source and later 232-test publication checks have separate sources. Original GitHub Actions run 43597256488 failed before runner assignment; its account-level cause remains unknown. These historical failures are not relabeled as passing. The new actual CircleCI browser/container results supersede the current execution gaps, not the historical records.

Replay acceptance concerns the concrete observed histories and unchanged workflow commands, not arbitrary future migrations. Single-host SQLite, limited admission and bounded workload results do not prove multi-host partitioning, hostile-tenant isolation or exactly-once behavior for arbitrary external APIs.

## Acceptance decision and remaining work

The reference's implemented governance, business effects, operator console, runtime packaging, restart and paired restoration now have passing execution evidence. **The project's central agent-quality/value criterion still fails and blocks full V1 acceptance.** A platform release may be documented as experimental; it must not claim that the model is superior to the runbook.

A stable full acceptance requires a defensible prospective model/value result, plus explicit target-specific operational acceptance for any production deployment. Public visibility and protections are separate maintainer choices. Original project code has the selected Apache-2.0 licence; dependency/weight rights remain separate. Earlier wording that the project licence was undecided applies only to the original pre-selection history.

The [backlog](BACKLOG.md), [publication instructions](PUBLICATION.md), [security](SECURITY.md) and [third-party inventory](THIRD_PARTY.md) remain relevant. Read this ledger as the current state wherever a dated historical document says browser or container execution was unavailable. No paid plan, real client system, external inference provider or production environment was modified by this work.

---

## Detailed historical native qualification — 14 November 2026

The historical ledger below describes **only** the clean `f1e6e2f` native run. Its original statements about unavailable browser/container execution remain dated evidence; the newer hosted results above supersede only those specific environmental limitations. The original failed model scores, timelines, replay scope, resource observations and exact artifacts are preserved.

### Source, environment and retained originals

The native run executed **2026-11-14, 12:57:19–13:22:15 UTC**, from source commit [`f1e6e2f3800242ec210145680261da8ab60f38b4`](https://github.com/mehdisafer/governed-dataops-agents/commit/f1e6e2f3800242ec210145680261da8ab60f38b4). The tracked worktree was clean at both ends, and the executable/input content manifest remained identical:

`e00ebb5acdc7570b1339ef5b5defa63152882f41b9585ba48149fcdcfb9666d1`

The environment reported Linux x86_64, glibc 2.41, Python 3.12.14, nine logical CPUs and 10,206,472 KiB total RAM. Available memory at the initial observation was 3,795,684 KiB. These observations do not establish exclusive CPU or memory capacity. The installed application versions included MCP 2.3.0, PydanticAI slim 2.68.0, Temporal SDK 1.36.0, Pydantic 2.14.3 and FastAPI 0.141.1. Runtime executable/weight fingerprints, process arguments and all input identities are retained with the run.

The [complete evidence directory](../evidence/qualification-f1e6e2f/) contains readable results and a complete archive of the **192 original run files**, including service logs, resource samples, 56 native workflow histories and their correlated traces/results. Original failed cases are retained. Credentials and live databases were kept outside that directory and were not distributed.

The most useful entry points are the original [run metadata](../evidence/qualification-f1e6e2f/run.json), [individual checks](../evidence/qualification-f1e6e2f/results.json), [engine comparison](../evidence/qualification-f1e6e2f/comparison.json) and [load measurements](../evidence/qualification-f1e6e2f/load.json). The archive is [full-originals.tar.gz](../evidence/qualification-f1e6e2f/full-originals.tar.gz). Its expanded files are reviewed before compression; compression is not a secret-scanning substitute.

Documentation and evidence-publication changes after this source commit do not retroactively change the run. Its hashes identify its own exact inputs. Subsequent qualification-harness and security-verifier corrections are regression-tested separately and do not imply that the native application was rerun against another commit.

### Native integration checks

| Requested check | Observed result | What the evidence establishes |
| --- | --- | --- |
| Five runbook business cases | Passed | Actual rows and revisions match all five expected outcomes |
| Tampered and stale approval | Passed | Both approval requests rejected with HTTP 409; no effect committed |
| Worker restart with buffered approval | Passed | Worker killed, separate approval signalled during outage, replacement worker completed one approved quarantine |
| Approval expiry during worker outage | Passed | Buffered expired approval rejected; no effect; incident cancelled |
| Incomplete real MCP evidence | Passed | Incomplete target observation crossed real MCP and caused escalation before inference |
| Changed policy | Passed | Old policy-bound authorization refused; no unauthorized effect |
| Two workers, one target | Passed | Three competing incidents produced one resolution, two refusals and one ledger effect; duplicate ingress reused the durable workflow |
| Admission saturation and recovery | Passed | Temporary limit of two pending incidents produced HTTP 429; retry after recovery returned 202 |
| Paired database restore | Passed | Application and Temporal backups restored into a new directory; row state and historical result preserved; a new incident resolved |
| Five agent business cases | **Failed** | 3/5 strict successes; one output-token-limit failure and one diagnostic timeout |
| Real model process outage | Passed | Missing model caused explicit escalation, zero effects and no runbook/provider fallback |
| Bounded load | Passed | Twelve runbook incidents at concurrency four, zero errors, p95 6.150 s against the declared 45 s threshold |
| Held-out runbook | Passed | 10/10 strict successes on the reserved instances |
| Held-out agent | **Failed** | 2/10 strict successes; eight unavailable diagnoses remained in the denominator |
| Measured agent advantage | **Failed** | The agent did not exceed the competent runbook's strict success count |
| Current retained-history replay | Passed | All 56 actual, closed histories replayed against the frozen workflow |
| Earlier-revision history replay | Passed with scope limit | Twenty-six retained development histories replayed after the query-only workflow change; the earlier overall worktree was dirty |
| Real browser console | **Blocked; recorded as failed** | Chromium aborted when creating its required local socket with `Operation not permitted`; no rendered-console acceptance or screenshot is claimed |

The target implements real transactional source, curated and quarantine rows. The ambiguity fixture commits its mutation and receipt before deliberately losing the HTTP response; the workflow reconciles that receipt before fresh business verification. This establishes the tested target behavior, not exactly-once semantics for arbitrary external APIs.

The current qualifier waits for the actual Temporal result, requires `WorkflowExecutionCompleted`, and compares the result with the terminal application projection before accepting a case. A terminal-looking database event alone is insufficient. All 56 retained histories end in completion. Cleanup recorded no failures and all direct children stopped. Model, Temporal and worker exits were zero; API and target exits were `-15` from the supervisor's SIGTERM shutdown. This is not a claim that every exit code was zero.

#### Replay scope

The previous workflow fingerprint was `92739ffdd0b9508707229e3f55d9841712a64da74a54142e729510617a52a67c`; the tested current workflow fingerprint was `4269035147f9aac85d7fb2cf4f52048c4320be2ac11a640804190f901e68845e`. The change adds the `workflow_revision` query field without changing command ordering. The earlier histories and their provenance limits are described in [development recovery evidence](../evidence/recovery-development/README.md).

This concrete replay result does not validate arbitrary workflow upgrades, schema migrations, multi-host partitioning or compatibility with future code. The dirty historical source manifest is not presented as a clean build. Lost evidence from the still earlier transient workspace is not reused as current validation.

### Frozen comparison

Each engine attempted all ten reserved cases; every case has a final business observation. The set contains two instances per known incident family, including five instances with a previously known malicious-log template. It is a small within-family evaluation, not an unseen-attack or industrial-population benchmark.

| Metric | Deterministic runbook | Frozen local agent |
| --- | ---: | ---: |
| Scheduled / attempted cases | 10 / 10 | 10 / 10 |
| Final business observations | 10 | 10 |
| Strict successful cases | **10/10** | **2/10** |
| Accepted diagnostic proposals | 10 | 2 |
| Correct proposals among accepted proposals | 10/10 | 2/2 |
| Verified resolutions | 6/6 resolution-eligible cases | 0/6 resolution-eligible cases |
| Contained outcomes | 2 | 1 |
| Refused outcomes | 2 | 1 |
| Escalated outcomes | 0 | 8 |
| Scripted approval decisions | 2 | 1 |
| Follow-up cases: denied, contained or escalated | 4 | 10 |
| Observed unjustified effects | 0/10 observed cases | 0/10 observed cases |
| Cases with unknown final effects | 0 | 0 |
| End-to-end median | 5.350 s | 91.425 s |
| End-to-end p95 | 7.026 s | 210.917 s |
| Cases with complete returned usage | 10 | 2 |
| Observed input / output tokens | 0 / 0 | 1,410 / 164, **incomplete** |
| Metered local-provider charge | $0 | $0 |

The eight unavailable diagnoses are failures of the operational criterion. They are not eight observed wrong categories. No completed response was received by the client for those attempts; zero returned token counts do not mean zero server work. Compute, energy, hardware and human effort were not monetized. The approval decisions were scripted with the separate approver credential, not timed human interactions.

The agent's two accepted proposals were a correct schema refusal and a correctly approved quality containment. No eligible incident was resolved by the agent on this reserved run. The absence of unjustified effects in these ten observable cases is a bounded observation, not a security certification or proof of general prompt-injection resistance.

Read [EVALUATION.md](EVALUATION.md) for all development trials, original case links, exact scoring rules and limitations. No prompt, model or baseline was retuned against this reserved result.

#### Post-run correction to the evaluation harness

Review found a contradiction in the frozen harness: `heldout_runbook` required all ten strict successes, while `measured_agent_advantage` required the agent to exceed the runbook on the same ten cases. Passing the first condition made the second mathematically impossible. This defect is independent of the eight actually unavailable model diagnoses.

The subsequent harness correction separates baseline competence on the five reference cases from complete, safe measurement of its reserved score. It preserves the agent quality requirement and the strict superiority criterion; parity is still not added value. It also checks the exact paired case identities and denominators before comparing engines. These are post-run regression-tested evaluation changes, not a new native qualification or a revision of the original 14/18 result. The current corpus still has a perfect baseline and does not distinguish additional agent value. A future claim needs prospectively declared measurements and fresh reserved data, as explained in [EVALUATION.md](EVALUATION.md).

#### Performance and transport findings

Model-server logs show a generation slowdown during the development quality case and later cancellation around client deadlines. They do not identify the underlying cause. One reserved incident took 187.327 seconds: after its 90-second diagnostic timeout, a started Temporal workflow task expired late and was recovered. The final reserved incident took 210.917 seconds and reached the diagnostic activity timeout after its completion could not be recorded normally. Worker logs contain later heartbeat and completion-RPC transport errors. These observations are retained and require investigation; they are not replaced with an unsupported CPU, memory, grammar or network explanation.

The maximum sampled model RSS was **1,889,692 KiB**, approximately **1.80 GiB**. Samples cover direct supervisor children at 0.5-second intervals, exclude transient MCP children, and include shared/mapped pages. They are not a complete host memory profile or an OOM diagnosis.

The separate runbook load profile measured 17.753 seconds for twelve incidents, approximately 0.676 incidents/s, median 5.660 seconds and p95 6.150 seconds, with zero errors. Its predeclared gate was p95 at most 45 seconds and zero errors. This is bounded single-host runbook throughput; it does not characterize model capacity or prove scalability.

### Source and security checks

The frozen implementation passed **172 unit/boundary tests**, Ruff, JavaScript syntax validation and contract regeneration without drift. Real SQLite, cryptography and the actual MCP stdio contract exchange are used where declared; tests with fake Temporal/provider boundaries label that scope. The original JUnit report is in [security evidence](../evidence/security/).

After the qualification-harness and semantic-verifier corrections, subsequently committed as [`062daaf`](https://github.com/mehdisafer/governed-dataops-agents/commit/062daaf419b419665729e4c63c1fa6ddfeb7d8d2), the full local suite passed **232 tests**, with zero failures, errors or skips. This includes 61 synthetic qualifier-boundary cases and preserves all seven original closure/cleanup cases. Ruff, JavaScript syntax, contract regeneration and comparison of the unchanged application/model/prompt/corpus/lock inputs also passed. The [publication checks](../evidence/publication-checks/) retain those separate original reports; no fresh native integration is implied.

The frozen-source worktree scan covered 86 committed files. Its reachable-history scan covered three commits through `f1e6e2f`. Each retained **seven raw generic-key candidates**, with seven exact, recomputed non-secret proofs and zero unresolved findings. The candidates are legitimate idempotency identifiers in the unchanged development trace/history. Later expanded-artifact and publication scans retain their own raw counts and review records; these are not silently folded into the earlier seven-candidate result.

The strict pip-audit report covers fifty frozen runtime dependencies, with zero known vulnerabilities reported and zero skipped dependencies at its recorded query time. Its input requirements and lock hashes match the frozen source. The installed inventory records 61 distributions, 64 lock entries and six verified local runtime assets. The project's own licence remains undecided. These checks do not audit all OS packages, OCI layers or native code and do not certify security or licence compatibility. See [SECURITY.md](SECURITY.md), [THIRD_PARTY.md](THIRD_PARTY.md) and their retained originals.

### Deployment and CI gates

| Gate | Observed status | Evidence and consequence |
| --- | --- | --- |
| Native MCP / PydanticAI / Temporal / target execution | Executed | Actual processes and business-state observations retained; model reliability still failed |
| Reference Docker stack | Blocked before build | [Container run](../evidence/containers-f1e6e2f/run.json): Docker CLI/daemon unavailable; no stack or image was created |
| Terraform version / formatting / readonly initialization | Executed successfully | [Infrastructure evidence](../evidence/infrastructure-f1e6e2f/); Terraform 1.17.2 and pinned provider 4.7.0 |
| Terraform validation / local Docker plan | Not qualified | Provider schema/handshake failure during validation; no plan or apply executed |
| Browser rendering and interaction | Not qualified | Original Chromium socket-permission failure in the native results; no successful screenshot |
| GitHub Actions run 43597256488 | Failed before runner assignment | Both attempts of `core` have runner ID 0 and zero steps; the four dependent jobs were skipped |
| Public publication and protections | Pending | Apache-2.0 was selected and committed after this native run; repository remains private, with no billing, visibility or administration change |

The original [GitHub API observations](../evidence/github-actions-43597256488/) include one bounded retry. Log retrieval returned 404; the connector did not support reading the check annotation. A logged-out isolated cloud-browser view yielded no further diagnostic. The cause of the pre-run CI failure is therefore **unknown**. It is not reported as a failing project test, a confirmed billing issue, or a successful CI validation. The owner can inspect the annotation on the [failed core job](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43597256488/job/132455148696).

### Acceptance decision and next work

The backend's tested governance and recovery paths are implemented and evidenced. Full acceptance is withheld because the agent's reliability/value criterion failed and the operator-console/container/infrastructure gates lack successful execution evidence. Multi-host operation and partitioned queues also remain outside the measured reference profile.

The [prioritized backlog](BACKLOG.md) preserves those gaps without weakening the baseline, increasing deadlines to hide a failure, or relabelling a blocked check as passed. The [publication preparation](PUBLICATION.md) contains the concrete metadata and owner decisions required before public release. The reviewed implementation can be integrated for the maintainer's intended public portfolio while its experimental status stays explicit. No accepted-release tag or production-readiness claim follows from the successful subset; the maintainer has selected Apache-2.0 and handles the remaining visibility and protection decisions.
