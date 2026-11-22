# Delivery plan and acceptance ledger

The intended product is an operator console and API that explains a synthetic industrial data incident, collects evidence through MCP, uses PydanticAI for a bounded model diagnosis, asks deterministic policy for authority, executes through Temporal, and verifies the resulting business state. Acceptance also requires measured agent value over a competent deterministic runbook.

**The experimental reference and its dated qualification evidence are retained; full agent-value acceptance remains open.** The 14 November native run passed 14/18 selected checks (agent 2/10, runbook 10/10). The distinct 15 November hosted evaluation failed (agent 1/10, runbook 10/10). On 16 November GitHub Actions at `7b709ff` passed core, governance, containers and infrastructure, but failed model-evaluation; a docs-only `351817e` run passed core with 245 tests and skipped four runtime profiles. Multi-host partitioning and model-value proof remain open. [Issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) remains open.

## Current runtime checkpoint — 23 November 2026

Executable source `ea80f2524060fcba745c23e85b344a9ad010b782` integrates [PR #25](https://github.com/mehdisafer/governed-dataops-agents/pull/25).
The [PR run](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/45082434901) and
[independent main run](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/45083502058) each passed four platform jobs, including 314 core
tests, but both model evaluations failed at
7/10 strict / 3 resolutions versus runbook 10/10 / 6. Their separate original
archives and resource observations are retained in [QUALIFICATION.md](QUALIFICATION.md).
The prospective B01–B04 trials remain unexecuted and V2 feasibility remains
in draft PR #23; full agent-value acceptance remains open.

## Scope and boundaries

- The reproducible repository and isolated synthetic demonstration environment define the project scope. Access to any personal workstation, client system or unrelated portfolio project is not required or authorized by this task.
- All business data are synthetic. The model has no general shell, direct database connection or write capability.
- GitHub reports the source repository Public (16 November 2026); original source and wheel are declared Apache-2.0, while dependencies/weights retain their own terms. Local runtime endpoints remain private and are not hosted publicly.
- Public release, billing changes and externally hosted resources require separate explicit authorization.

## Recovery and retained implementation

The temporary development workspace from the previous session was no longer available when work resumed on 2026-11-14. GitHub retained the initial README commit (`827858f777f2fffd2869853bdcd96ed6628e99e8`), issue #1 and the feature branch, but no implementation commit or pull request. Source was reconstructed from the retained implementation context and inspected afresh. Earlier conversation-only test counts and benchmarks are not acceptance evidence for this revision.

The reconstructed vertical slice was committed as `78a46751f69cc719c85aee123b58a7f86810df97`. Recovery, governance, exact-source checks, deployment harnesses and the frozen comparison were committed as `f1e6e2f3800242ec210145680261da8ab60f38b4`. The complete native run then used that clean source without modifications. Later publication work retains its originals and documents the failures; it does not change which source was exercised.

The final review also corrected an impossible combination of evaluation gates: a perfect required baseline score followed by a strictly greater agent score on the same finite set. Baseline competence is now checked separately from the comparative measurement. The quality and superiority requirements remain, the original result is unchanged, and a prospective discriminating evaluation is still needed. The changed harness has separate boundary tests; no new native model result is implied.

## Acceptance criteria and observed state

| Area | Required evidence | Current state |
| --- | --- | --- |
| Business paths | Five actual row-based fixtures; truthful resolution, containment or escalation | Implemented and exercised in runbook mode; agent outcomes reported separately |
| Integration | Actual MCP client/server, actual PydanticAI inference and actual Temporal histories | Executed on identified native and hosted sources with real local model calls; model quality/value remain failed |
| Authorization | Independent scope, environment, role, budget and precondition policy; signed approvals | Implemented, boundary-tested and exercised for the named native negative cases |
| Durable effects | Atomic target mutation and receipt; reconciliation before retrying an ambiguous response | Demonstrated against the supplied transactional target |
| Negative behavior | Stale/tampered/expired approvals, changed policy, incomplete evidence, injection and model outage | Named refusals/outage exercised; known injection template only, no general attack-resistance claim |
| Recovery | Worker outage, buffered approval, duplicate ingress, old-history replay and backup/restore | Executed; 56 current and 26 earlier histories replayed with the documented source/change limits |
| Capacity | Target contention, bounded admission, saturation recovery, partitioning invariants, load threshold and resource observations | Fixed two-queue Temporal recovery/admission isolation and bounded load exercised on one host; shared-model saturation, dynamic ownership changes and multi-host assurance remain open |
| Model evaluation | Frozen reserved corpus, competent baseline, complete failures/denominators and measured value | Historical scores retained; separate PR #25 and exact-main evaluations each measured agent 7/10 strict / 3 resolutions vs runbook 10/10 / 6. Both failed model value; see [EVALUATION.md](EVALUATION.md) |
| Operator console | Correlated trace display, approval/cancellation and real-browser interactions | Original native Chromium failure retained; PR #25 and independent exact-main governance profiles exercised the real browser console |
| Deployment | Actual container build/run and supported Terraform validation/plan | PR #25 and independent exact-main runs passed actual reference containers and isolated local Docker Terraform plans; no production apply or accepted model value |
| Operations and CI | Locked dependencies, security inventory, CI, restore and runbooks | Both latest fully executed source qualifications passed four platform jobs, including 314 core tests; model evaluation failed. Exact-main CircleCI unit/security statuses succeeded; see [CI.md](CI.md) |
| Publication | Reviewed PRs, release candidate, licence, public source and protections | PRs #2/#4/#5/#6/#7/#8 merged; public source and Apache-2.0 packaging verified; `main` unprotected and full agent acceptance withheld |

Implemented, executed, tested and accepted remain distinct states. [QUALIFICATION.md](QUALIFICATION.md) gives the exact evidence and limits. A checked subset does not close the original scope issue.

## Next work in dependency order

1. Preserve the historical GitHub Actions pre-run failures without speculative causal claims. New runners execute full jobs; prioritize the failed frozen model-value gate and source-specific evidence.
2. Investigate the retained local-model slowdown, missing responses and Temporal/transport delays using development inputs and isolated measurements. Keep failed attempts and usage uncertainty visible.
3. Select any revised model, prompt, runtime or diagnostic contract using development data only. Freeze a new evaluation prospectively; the now-exposed reserved set remains a regression set.
4. Evaluate concrete agent utility while preserving the competent baseline, safety invariants and complete outcome/cost denominators. Matching the existing baseline does not demonstrate added value.
5. Extend the qualified fixed two-queue reference to shared-model saturation, dynamic ownership changes and target-specific operational requirements, then reassess agent-value/release gates with new evidence. Apache-2.0 is already selected; owner-side publication controls remain separate. The bounded two-queue result does not establish shared-inference isolation or multi-host availability.

The [detailed backlog](BACKLOG.md) defines evidence needed to close these items. No deadline increase, implicit runbook fallback, excluded failure or reduced baseline is used to turn the current result into acceptance.
