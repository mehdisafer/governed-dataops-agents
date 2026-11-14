# Delivery plan and acceptance ledger

The intended product is an operator console and API that explains a synthetic industrial data incident, collects evidence through MCP, uses PydanticAI for a bounded model diagnosis, asks deterministic policy for authority, executes through Temporal, and verifies the resulting business state. Acceptance also requires measured agent value over a competent deterministic runbook.

**The implementation and its first complete native qualification are retained; full project acceptance remains open.** The frozen source at `f1e6e2f3800242ec210145680261da8ab60f38b4` passed 14/18 requested native checks. The reserved comparison was 10/10 for the runbook and 2/10 for the agent. Deployment, browser and CI gates also require successful execution evidence. [Issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) remains open. [PR #2](https://github.com/mehdisafer/governed-dataops-agents/pull/2) records delivery and automated review of the experimental implementation.

## Scope and boundaries

- Only this repository and isolated demonstration infrastructure are in scope. No personal computer, client environment or other portfolio repository is used.
- All business data are synthetic. The model has no general shell, direct database connection or write capability.
- The repository remains private. Its own licence is undecided; third-party licences continue to apply.
- Public release, billing changes and externally hosted resources require separate explicit authorization.

## Recovery and retained implementation

The temporary development workspace from the previous session was no longer available when work resumed on 2026-11-14. GitHub retained the initial README commit (`827858f777f2fffd2869853bdcd96ed6628e99e8`), issue #1 and the feature branch, but no implementation commit or pull request. Source was reconstructed from the retained implementation context and inspected afresh. Earlier conversation-only test counts and benchmarks are not acceptance evidence for this revision.

The reconstructed vertical slice was committed as `78a46751f69cc719c85aee123b58a7f86810df97`. Recovery, governance, exact-source checks, deployment harnesses and the frozen comparison were committed as `f1e6e2f3800242ec210145680261da8ab60f38b4`. The complete native run then used that clean source without modifications. Later publication work retains its originals and documents the failures; it does not change which source was exercised.

The final review also corrected an impossible combination of evaluation gates: a perfect required baseline score followed by a strictly greater agent score on the same finite set. Baseline competence is now checked separately from the comparative measurement. The quality and superiority requirements remain, the original result is unchanged, and a prospective discriminating evaluation is still needed. The changed harness has separate boundary tests; no new native model result is implied.

## Acceptance criteria and observed state

| Area | Required evidence | Current state |
| --- | --- | --- |
| Business paths | Five actual row-based fixtures; truthful resolution, containment or escalation | Implemented and exercised in runbook mode; agent outcomes reported separately |
| Integration | Actual MCP client/server, actual PydanticAI inference and actual Temporal histories | Executed natively with local model calls; model reliability failed |
| Authorization | Independent scope, environment, role, budget and precondition policy; signed approvals | Implemented, boundary-tested and exercised for the named native negative cases |
| Durable effects | Atomic target mutation and receipt; reconciliation before retrying an ambiguous response | Demonstrated against the supplied transactional target |
| Negative behavior | Stale/tampered/expired approvals, changed policy, incomplete evidence, injection and model outage | Named refusals/outage exercised; known injection template only, no general attack-resistance claim |
| Recovery | Worker outage, buffered approval, duplicate ingress, old-history replay and backup/restore | Executed; 56 current and 26 earlier histories replayed with the documented source/change limits |
| Capacity | Target contention, bounded admission, saturation recovery, partitioning invariants, load threshold and resource observations | Contention/admission/load exercised on one host; required target-partitioning qualification remains open |
| Model evaluation | Frozen reserved corpus, competent baseline, all failures and denominators, measured value | Comparison completed; agent 2/10 versus runbook 10/10; value criterion failed |
| Operator console | Real correlated trace display and approval/cancellation interaction | Implemented; real Chromium launch blocked before rendered interaction |
| Deployment | Actual container build/run and supported Terraform resource validation/plan | Reference implemented; Docker unavailable, Terraform provider-schema load failed, no plan/apply |
| Operations and CI | Locked dependencies, security/component inventory, CI execution, restore and operating procedures | Local checks and native restore retained; hosted CI failed before runner assignment on both attempts |
| Publication | Coherent commits, reviewed PR, identified release, licence decision and authorized public review | Reviewed implementation and unreleased candidate prepared for the default branch; review labelled as automation; licence/administration/publication pending |

Implemented, executed, tested and accepted remain distinct states. [QUALIFICATION.md](QUALIFICATION.md) gives the exact evidence and limits. A checked subset does not close the original scope issue.

## Next work in dependency order

1. Resolve the hosted runner prerequisite from the actual GitHub check annotation. Reproduce the Docker, Terraform and rendered-console checks in an authorized environment that provides their required facilities.
2. Investigate the retained local-model slowdown, missing responses and Temporal/transport delays using development inputs and isolated measurements. Keep failed attempts and usage uncertainty visible.
3. Select any revised model, prompt, runtime or diagnostic contract using development data only. Freeze a new evaluation prospectively; the now-exposed reserved set remains a regression set.
4. Evaluate concrete agent utility while preserving the competent baseline, safety invariants and complete outcome/cost denominators. Matching the existing baseline does not demonstrate added value.
5. Qualify the required target-partitioning invariants and additional-worker behavior, complete the outstanding release gates, then obtain the explicit repository licence and publication decisions. The current two-worker contention result does not establish partitioned routing.

The [detailed backlog](BACKLOG.md) defines evidence needed to close these items. No deadline increase, implicit runbook fallback, excluded failure or reduced baseline is used to turn the current result into acceptance.
