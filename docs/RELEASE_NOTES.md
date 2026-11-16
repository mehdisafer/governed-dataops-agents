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

## Later hosted platform checks and remaining release gates

The agent reliability/value gate failed in the original native comparison (agent 2/10 vs runbook 10/10) and the separate hosted frozen evaluation (agent 1/10 vs runbook 10/10). Development failures include output truncation, absent answers and transport delays. The causes are not fully established; increasing timeouts or tuning against the exposed reserved set is not acceptance evidence.

The original 14 November Docker, Terraform and Chromium attempts were blocked and remain documented as historical failures. Later hosted checks passed: governance/browser and infrastructure profiles at `924dd24` and ten real Docker/Temporal/local-model platform gates at `cad9cc6`. The container case still recorded `diagnostic_quality_passed=false` for an incorrect model action safely denied by policy. GitHub Actions continues failing before runner assignment; CircleCI success cannot diagnose that separate issue. No production Terraform apply was claimed.

The repository's original source has the explicitly selected [Apache License 2.0](../LICENSE), and its description/topics are configured. Public visibility is **confirmed by GitHub repository metadata (16 November 2026)**. Supported branch protections and anonymous-access readback remain separate; no billing, deployment or accepted release is implied.

## Installation and compatibility

Python 3.12 and the committed `uv.lock` define the Python environment. The reference runtime is private Linux amd64 with local SQLite persistence and a local CPU model. Read [DEPLOYMENT.md](DEPLOYMENT.md) before starting it; a hosted reference-container run passed its scoped execution gates, not its model diagnosis quality or production acceptance. The target schema version is 1; unsupported newer schemas are refused. Rollback requires a stopped paired restore with the matching approval-signing identity.

## Review status

The reference implementation was merged in [PR #2](https://github.com/mehdisafer/governed-dataops-agents/pull/2), the passing CircleCI unit integration in [PR #5](https://github.com/mehdisafer/governed-dataops-agents/pull/5), and corrected container integration is tracked by [PR #4](https://github.com/mehdisafer/governed-dataops-agents/pull/4). Reviews by the authoring automation do not constitute independent approval. Full model-value acceptance, complete protection-settings verification and a stable production release remain withheld. Source visibility alone does not close those gates.
