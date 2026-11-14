# Delivery plan and acceptance ledger

The intended product is an operator console and API that explains a synthetic industrial data incident, collects evidence through MCP, uses PydanticAI for a bounded model diagnosis, asks deterministic policy for authority, executes through Temporal, and verifies the resulting business state.

## Scope and boundaries

- Only this repository and isolated demonstration infrastructure are in scope. No personal computer, client environment or other portfolio repository is used.
- All business data are synthetic. Models have no general shell, direct database connection or write capability.
- The repository remains private. Its own licence is undecided; third-party licences continue to apply.
- Public release, billing changes and externally hosted resources require separate explicit authorization.

## Recovery note — 2026-11-14

The temporary development workspace from the previous session was no longer available when work resumed. GitHub retained the initial README commit (`827858f777f2fffd2869853bdcd96ed6628e99e8`), issue #1 and the feature branch, but no implementation commit or pull request. Source is being reconstructed from the retained implementation context. Previous test counts and benchmark numbers are historical conversation reports; their original artifacts are unavailable and are **not acceptance evidence for this revision**. New evidence must be produced against the reconstructed source and retained in Git or CI artifacts.

## Acceptance criteria

| Area | Required evidence |
|---|---|
| Business value | Five real row-based fixtures; truthful resolution, containment or escalation |
| Integration | Actual MCP client/server, actual PydanticAI inference, actual Temporal histories |
| Authorization | Independent scope/environment/role/budget/precondition policy and signed approvals |
| Durable effects | Atomic target effect and journal; reconciliation before retries after ambiguous response |
| Negative behavior | Stale/tampered/expired approvals, changed policy, incomplete evidence, injection, model outage |
| Recovery | Worker outage, buffered approval, idempotent duplicate ingress, old history replay, backup/restore |
| Capacity | Target contention, bounded admission, saturation recovery, declared load threshold and measured resources |
| Model evaluation | Frozen held-out corpus compared with a competent deterministic runbook; all denominators/failures |
| Operations | Locked dependencies, container reference, CI, secret scan, dependency/licence inventory, procedures |
| Publication | Coherent commits, reviewed PR, concrete release notes, no unsupported claims or licence choice |

Implemented, executed, tested and accepted are distinct states. See [QUALIFICATION.md](QUALIFICATION.md) for the current observed status and original evidence links. The scope issue remains open until its requirements are evidenced.

## Priority order

1. Restore contracts, target, policy and the complete vertical path; commit the source checkpoint.
2. Exercise real services and the bounded local model; fix concrete defects.
3. Run independent recovery/security/capacity checks and the frozen comparative evaluation.
4. Complete deployment checks, operations and publication review; publish remaining gaps explicitly.
