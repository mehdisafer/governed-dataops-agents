# Release candidate: v0.1.0a1

**State: unreleased private candidate; acceptance withheld.** No release tag or GitHub release exists for this candidate. The clean native application source is `f1e6e2f3800242ec210145680261da8ab60f38b4`; the reviewed [implementation PR](https://github.com/mehdisafer/governed-dataops-agents/pull/2) also retains the subsequent evidence and documentation. Read the [qualification ledger](QUALIFICATION.md) before interpreting an implemented capability as an accepted release.

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

## Remaining release gates

The agent reliability/value gate failed. A development quality case exceeded its output-token limit, later cases lacked completed responses, and two reserved cases had additional workflow/transport delays. Their underlying causes are not established; increasing timeouts or retuning against the exposed set is not acceptance evidence.

Docker was unavailable before build. Terraform version, formatting and readonly initialization succeeded, but provider-schema loading failed; no plan or apply executed. Chromium failed to create a required local socket, so rendered-console behavior has not been qualified. Both hosted CI attempts failed before runner assignment with zero steps; the available records do not establish the cause. These remain separate gates, with their original failures preserved.

The repository's own licence remains undecided. Public visibility, repository metadata and protection administration require the owner decisions/access described in [PUBLICATION.md](PUBLICATION.md). No billing or visibility change follows from this candidate.

## Installation and compatibility

Python 3.12 and the committed `uv.lock` define the Python environment. The reference runtime is private Linux amd64 with local SQLite persistence and a local CPU model. Read [DEPLOYMENT.md](DEPLOYMENT.md) before starting it; the container reference still requires actual qualification. The target schema version is 1; newer schemas are rejected rather than automatically downgraded. Rollback requires a stopped, paired restore of application and Temporal state with the matching signing identity.

## Review status

The implementation PR tracks issue #1 and records automated review findings, fixes, tests and remaining limits. Reviews performed by the authoring automation are labelled as such and do not constitute independent human approval. The reviewed experimental implementation is prepared for default-branch integration and the maintainer's public-repository workflow. Integration does not close issue #1, establish agent value or create an accepted release.
