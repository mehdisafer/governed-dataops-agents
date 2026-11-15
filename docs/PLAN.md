# Delivery plan and acceptance ledger

The intended product is an operator console and API that explains a synthetic industrial data incident, collects evidence through MCP, uses PydanticAI for a bounded model diagnosis, asks deterministic policy for authority, executes through Temporal, and verifies the resulting business state. Acceptance also requires measured agent value over a competent deterministic runbook.

**The implemented reference and its dated qualification evidence are retained; full agent-value acceptance remains open.** The clean 14 November native source `f1e6e2f` passed 14/18 checks (agent 2/10 versus runbook 10/10). CircleCI subsequently passed unit checks on `main` at `2460012`, hosted governance/browser checks at `924dd24`, and ten actual container-platform checks at `cad9cc6`. The separate 15 November frozen model evaluation still failed (agent **1/10**, runbook **10/10**). GitHub Actions runner allocation and target-partitioning evidence remain open. [Issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) remains open.

## Scope and boundaries

- Only this repository and isolated demonstration infrastructure are in scope. No personal computer, client environment or other portfolio repository is used.
- All business data are synthetic. The model has no general shell, direct database connection or write capability.
- The repository remains private at the inspected date. Original project source is licensed under [Apache-2.0](../LICENSE); dependency/model licences remain independent.
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
| Model evaluation | Frozen reserved corpus, competent baseline, complete failures/denominators and measured value | Native: agent 2/10 vs runbook 10/10; later hosted: agent 1/10 vs runbook 10/10. Both fail the value criterion |
| Operator console | Correlated trace display, approval/cancellation and real-browser interactions | Original native Chromium launch blocked; later hosted governance profile at `924dd24` passed its declared browser gate |
| Deployment | Actual container build/run and supported Terraform validation/plan | Real corrected reference containers passed ten execution checks at `cad9cc6`; hosted infrastructure job passed at `924dd24`. Neither is a production apply or LLM-value PASS |
| Operations and CI | Locked dependencies, security inventory, CI, restores and runbooks | CircleCI unit passed on `main` at `2460012`, governance at `924dd24` and container at `cad9cc6`; GitHub Actions still fails before runner assignment |
| Publication | Coherent commits, reviewed PRs, identified candidate release, licence and public review | PR #2 and unit CI PR #5 merged; corrected runtime in PR #4; Apache-2.0 selected; visibility private and stable acceptance withheld |

Implemented, executed, tested and accepted remain distinct states. [QUALIFICATION.md](QUALIFICATION.md) gives the exact evidence and limits. A checked subset does not close the original scope issue.

## Next work in dependency order

1. Diagnose GitHub Actions' independent pre-run failure using its actual annotation; keep already passing CircleCI results bound to their source SHAs, and do not speculate about billing.
2. Investigate the retained local-model slowdown, missing responses and Temporal/transport delays using development inputs and isolated measurements. Keep failed attempts and usage uncertainty visible.
3. Select any revised model, prompt, runtime or diagnostic contract using development data only. Freeze a new evaluation prospectively; the now-exposed reserved set remains a regression set.
4. Evaluate concrete agent utility while preserving the competent baseline, safety invariants and complete outcome/cost denominators. Matching the existing baseline does not demonstrate added value.
5. Qualify target-partitioning invariants and additional worker behavior, then close agent-value/release gates with new evidence. Apache-2.0 is already selected; owner-managed visibility and branch protections remain separate. Two-worker contention on one queue is not partitioning.

The [detailed backlog](BACKLOG.md) defines evidence needed to close these items. No deadline increase, implicit runbook fallback, excluded failure or reduced baseline is used to turn the current result into acceptance.
