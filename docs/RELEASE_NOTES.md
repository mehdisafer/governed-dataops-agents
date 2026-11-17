# Release candidate: v0.1.0a1

**State: public source repository, unreleased candidate; acceptance withheld.** No release tag or GitHub release exists for this candidate. The clean native application source is `f1e6e2f3800242ec210145680261da8ab60f38b4`; the reviewed [implementation PR](https://github.com/mehdisafer/governed-dataops-agents/pull/2) also retains the subsequent evidence and documentation. Read the [qualification ledger](QUALIFICATION.md) before interpreting an implemented capability as an accepted release.

## Included

- An authenticated operator console and API with scoped incident traces, explicit diagnostic engine selection, separate approval credentials and cancellation.
- Five actual row-based synthetic incident fixtures: freshness, transient failure, incompatible schema, quality rejection and duplicate delivery.
- Real MCP stdio capabilities, PydanticAI structured local inference and a Temporal workflow with bounded activities, approval signals and replay support.
- Independent deterministic policy, canonical plan digests, signed and persisted approvals, fresh revision checks and one-action budgets.
- Atomic business effects and receipts, reconciliation after a deliberately lost HTTP response, idempotent event admission and bounded backpressure.
- Frozen dependencies and schemas, native/container qualification harnesses, CI configuration, security/component inventories, and deployment/recovery procedures.

## Observed qualification

The complete native run passed **14/18 requested checks** and returned a nonzero exit. It exercised all five runbook outcomes, refusal of tampered/stale/expired approvals, worker restart with buffered approval, changed policy, incomplete MCP evidence, genuine model outage, target contention, admission recovery and an executed paired restore. All 56 current closed histories replayed; 26 earlier histories replayed across a query-only workflow change, with the earlier dirty-source limitation retained.

The frozen reserved comparison attempted ten cases per engine and observed every final business state. The runbook achieved **10/10** strict successes. The local agent achieved **2/10**: two accepted proposals were correct and eight attempts produced no accepted diagnosis before escalation. Agent median/p95 were **91.425/210.917 seconds**, versus **5.350/7.026 seconds** for the runbook. No unjustified effect was observed in these twenty cases, but model usage was incomplete for eight agent attempts. No measured agent advantage is established.

The separate bounded runbook load used twelve incidents at concurrency four, with zero errors and p95 **6.150 seconds** against the predeclared 45-second threshold. It does not establish model throughput or multi-host scalability. The frozen implementation passed 172 unit/boundary tests; the later full local suite passed **232**, including the post-run qualifier and security-verifier regressions, as recorded separately in [publication checks](../evidence/publication-checks/).

All 192 original files from the native run are retained, including failed cases, logs and resource samples. Post-run review corrected a contradictory evaluation gate, separating baseline competence from comparative score measurement while keeping agent quality and strict superiority requirements. It also hardened exact paired-case accounting and extended semantic secret-review support for the container source manifest. These corrections have separate regression tests; the original 14/18 native result is unchanged. See the [evidence index](../evidence/README.md), [evaluation report](EVALUATION.md) and [prioritized backlog](BACKLOG.md).

## Most recent merged source instrumentation — 17 November 2026

The current public source `main` [`263a6c1c7226`](https://github.com/mehdisafer/governed-dataops-agents/commit/263a6c1c72260c7be6ba7ba7aeb1a4a891b7f41f) integrates [PR #17](https://github.com/mehdisafer/governed-dataops-agents/pull/17): bounded model-latency/failure attribution, original failed-probe preservation and correct restored-stack startup selection. Its PR head `e81309b` and GitHub Actions merge-preview `158e52c5` have the same Git tree. [Run #43990582623](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43990582623) passed **284 Python core tests, real governance/two-queue Temporal, ten container checks, infrastructure**, and the two CircleCI source/security checks were green. **Mandatory model-evaluation FAILED** with **6/10 strict agent** versus **10/10 runbook** on ten observed model responses. Model quality in the real container remained false.

The original [container timings](MODEL_LATENCY.md) measured **67.004099s `Agent.run`** inclusive of transport/inference/native output validation and a correct **17.568490s restored stack** startup; internal inference-only/queue-stage times remain unknown. No model weights, prompt, 90s budget, approvals, external provider or business effect contract were altered. This is *not* a new stable release, model-value acceptance or production-readiness claim. Earlier guarded and historical comparisons below remain separate, source-bound failures. The independent post-merge main CI must receive its own receipt.

## Earlier guarded-source security and model-value limits — 17 November 2026

Current public source `main` at
[`9635dbcc`](https://github.com/mehdisafer/governed-dataops-agents/commit/9635dbccfe8cfd168f14ee9380eeb1f03e105a0c)
contains opt-in fixed target partition routing and explicit wrong-worker /
cross-partition signed-approval refusal tests (PRs #14–#15), and [PR #13](https://github.com/mehdisafer/governed-dataops-agents/pull/13)'s
typed-snapshot model proposal guard. Wrong model category/action pairs are
rejected, never rewritten as successful runbook responses.

[GitHub Actions full main run 43988865699](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43988865699)
executed **272 passing core tests**, successful governance (including real
two-queue Temporal), successful containers/paired restore, and successful
infrastructure. **Frozen model-evaluation remained FAILED**: 10/10 model
responses, **7/10 strict model success vs 10/10 runbook**, three wrong
diagnoses escalated without unauthorized effects, no measured advantage.
Both current CircleCI unit/publication-security checks succeeded.
The independent source-specific original model artifacts preserve
all negative results, including the earlier 2/10 and 1/10 attempts and
`diagnostic_quality_passed=false` in the real container case.

This is a security and bounded single-host platform improvement, **not a
production-ready or accepted agent-value V1**. Shared-model saturation,
prospective unseen v2 evaluation and independent-host operations remain open.

## Later hosted platform checks and remaining release gates

The agent reliability/value gate failed in the original native comparison (agent 2/10 vs runbook 10/10) and the separate hosted frozen evaluation (agent 1/10 vs runbook 10/10). Development failures include output truncation, absent answers and transport delays. The causes are not fully established; increasing timeouts or tuning against the exposed reserved set is not acceptance evidence.

The original 14 November Docker, Terraform and Chromium attempts were blocked and remain documented as historical failures. Later hosted checks passed: governance/browser and infrastructure profiles at `924dd24` and ten real Docker/Temporal/local-model platform gates at `cad9cc6`. The container case still recorded `diagnostic_quality_passed=false` for an incorrect model action safely denied by policy. The original GitHub Actions runner-allocation failures remain historical. The later 16 November full run `7b709ff` actually executed and passed core, governance, containers and infrastructure but **failed model-evaluation**. The subsequent docs-only `351817e` passed core with 245 tests and skipped runtime jobs. None of these results constitutes model utility or production acceptance. No production Terraform apply was claimed.

The repository's original source has the explicitly selected [Apache License 2.0](../LICENSE), and its description/topics are configured. Public visibility is **confirmed by GitHub repository metadata (16 November 2026)**. Supported branch protections and anonymous-access readback remain separate; no billing, deployment or accepted release is implied.

## Installation and compatibility

Python 3.12 and the committed `uv.lock` define the Python environment. The reference runtime is private Linux amd64 with local SQLite persistence and a local CPU model. Read [DEPLOYMENT.md](DEPLOYMENT.md) before starting it; a hosted reference-container run passed its scoped execution gates, not its model diagnosis quality or production acceptance. The target schema version is 1; unsupported newer schemas are refused. Rollback requires a stopped paired restore with the matching approval-signing identity.

## Review status

The reference implementation was merged in [PR #2](https://github.com/mehdisafer/governed-dataops-agents/pull/2), the passing CircleCI unit integration in [PR #5](https://github.com/mehdisafer/governed-dataops-agents/pull/5), and corrected container integration is tracked by [PR #4](https://github.com/mehdisafer/governed-dataops-agents/pull/4). Reviews by the authoring automation do not constitute independent approval. Full model-value acceptance, complete protection-settings verification and a stable production release remain withheld. Source visibility alone does not close those gates.
