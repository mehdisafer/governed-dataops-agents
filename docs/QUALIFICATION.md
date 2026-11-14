# Qualification status

Status: implementation reconstructed; clean-source integration qualification pending. The pull request remains a draft and the acceptance issue remains open.

No prior session result is counted as validation of the reconstructed source. Source checkpoints and retained original reports identify the commit, configuration, input corpus, commands, outcomes and limitations. A service that merely starts, a mocked client, or a skipped test does not establish integration acceptance.

## Observed before the qualification freeze — 2026-11-14

| Check | Observed result | Scope |
| --- | --- | --- |
| Unit and boundary suite | 172 tests passed | Actual SQLite, signatures and MCP stdio where declared; fake external boundaries in the labelled unit tests do not establish service integration |
| Ruff, JavaScript syntax, contract export | Passed with no contract drift | Source checks, not browser behavior |
| Native governance development run | Eleven platform checks passed; browser check failed | Real Temporal, MCP and target; worktree changed during this development run, so it is not clean-source acceptance |
| Worker recovery and approval buffering | Observed on real services | Also exercised approval expiry during the outage, changed policy, tampering and stale state |
| Durable effect and restore | Observed on real services | Response loss reconciled; paired application/Temporal databases restored into a new directory; old outcome and a new incident checked |
| Development load | 8 incidents, concurrency 4; zero errors; p95 5.763 s | Explicit runbook mode; declared p95 threshold 45 s; not LLM throughput |
| Development history replay | 26 actual histories replayed | Same-workflow replay; broader upgrade compatibility is not established |
| Final diagnostic development trial | 2/5 expected category/action pairs | Actual local PydanticAI inference; the quality gate failed; prompt and generation profile frozen |
| Runtime dependency audit | 50 dependencies, zero reported vulnerabilities, zero skipped | Strict pip-audit on the frozen runtime export; no OS-image audit claim |
| Current source and selected recovery artifacts | 7 raw candidates, 7 exact non-secret proofs, zero unresolved | Raw scanner findings retained; see [security method](SECURITY.md) and [review registry](../evidence/secret-review.json) |
| Browser execution in the authoring environment | Blocked | Chromium cannot create its required AF_UNIX socket; console rendering remains unverified here |
| Docker execution in the authoring environment | Blocked | No Docker daemon/client; real container qualification is configured in CI |
| Terraform validation in the authoring environment | Blocked after initialization | Provider cannot create its AF_UNIX socket; actual validation and a non-applying local Docker plan are configured in CI |

The complete development run is not published as a compressed substitute for evidence review. Its dirty source-manifest hashes cannot all be reconstructed against the named commit. The unchanged, individually reviewed [transient trace and history](../evidence/recovery-development/README.md) are retained with the exact limitation.

## Required before acceptance

Run the frozen source with `scripts/qualify.py --profile integration --source-commit <commit>`, retain its original outputs and compare both diagnostic modes on all ten reserved instances per mode. The requested checks must continue after a failed model case, and the overall result must remain failed when any required gate fails.

CI separately exercises source/security checks, native governance and browser rendering, model evaluation, real containers, and Terraform validation/plan. A workflow file is an implementation, not evidence that those jobs ran successfully. The consolidated ledger will report their actual run and artifact URLs.

The local model has not demonstrated a benefit over the competent runbook. Licence choice, public publication and repository-administration controls also remain unresolved. None is implied by a passing platform subset.
