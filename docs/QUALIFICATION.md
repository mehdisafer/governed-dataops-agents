# Qualification ledger

**Acceptance remains open.** The complete native integration run returned a nonzero exit with **14 of 18 requested checks passed**. The frozen agent completed the expected diagnostic and business outcome in **2 of 10 reserved cases**, compared with **10 of 10** for the unchanged deterministic runbook. No measured agent advantage is established. Browser and deployment verification also remain incomplete.

[PR #2](https://github.com/mehdisafer/governed-dataops-agents/pull/2) records the reviewed implementation, and [issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) remains open. Integration into the default branch and public visibility are delivery steps; they do not close the original technical acceptance criteria.

## Source, environment and retained originals

The native run executed **2026-11-14, 12:57:19–13:22:15 UTC**, from source commit [`f1e6e2f3800242ec210145680261da8ab60f38b4`](https://github.com/mehdisafer/governed-dataops-agents/commit/f1e6e2f3800242ec210145680261da8ab60f38b4). The tracked worktree was clean at both ends, and the executable/input content manifest remained identical:

`e00ebb5acdc7570b1339ef5b5defa63152882f41b9585ba48149fcdcfb9666d1`

The environment reported Linux x86_64, glibc 2.41, Python 3.12.14, nine logical CPUs and 10,206,472 KiB total RAM. Available memory at the initial observation was 3,795,684 KiB. These observations do not establish exclusive CPU or memory capacity. The installed application versions included MCP 2.3.0, PydanticAI slim 2.68.0, Temporal SDK 1.36.0, Pydantic 2.14.3 and FastAPI 0.141.1. Runtime executable/weight fingerprints, process arguments and all input identities are retained with the run.

The [complete evidence directory](../evidence/qualification-f1e6e2f/) contains readable results and a complete archive of the **192 original run files**, including service logs, resource samples, 56 native workflow histories and their correlated traces/results. Original failed cases are retained. Credentials and live databases were kept outside that directory and were not distributed.

The most useful entry points are the original [run metadata](../evidence/qualification-f1e6e2f/run.json), [individual checks](../evidence/qualification-f1e6e2f/results.json), [engine comparison](../evidence/qualification-f1e6e2f/comparison.json) and [load measurements](../evidence/qualification-f1e6e2f/load.json). The archive is [full-originals.tar.gz](../evidence/qualification-f1e6e2f/full-originals.tar.gz). Its expanded files are reviewed before compression; compression is not a secret-scanning substitute.

Documentation and evidence-publication changes after this source commit do not retroactively change the run. Its hashes identify its own exact inputs. Subsequent qualification-harness and security-verifier corrections are regression-tested separately and do not imply that the native application was rerun against another commit.

## Native integration checks

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

### Replay scope

The previous workflow fingerprint was `92739ffdd0b9508707229e3f55d9841712a64da74a54142e729510617a52a67c`; the tested current workflow fingerprint was `4269035147f9aac85d7fb2cf4f52048c4320be2ac11a640804190f901e68845e`. The change adds the `workflow_revision` query field without changing command ordering. The earlier histories and their provenance limits are described in [development recovery evidence](../evidence/recovery-development/README.md).

This concrete replay result does not validate arbitrary workflow upgrades, schema migrations, multi-host partitioning or compatibility with future code. The dirty historical source manifest is not presented as a clean build. Lost evidence from the still earlier transient workspace is not reused as current validation.

## Frozen comparison

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

### Post-run correction to the evaluation harness

Review found a contradiction in the frozen harness: `heldout_runbook` required all ten strict successes, while `measured_agent_advantage` required the agent to exceed the runbook on the same ten cases. Passing the first condition made the second mathematically impossible. This defect is independent of the eight actually unavailable model diagnoses.

The subsequent harness correction separates baseline competence on the five reference cases from complete, safe measurement of its reserved score. It preserves the agent quality requirement and the strict superiority criterion; parity is still not added value. It also checks the exact paired case identities and denominators before comparing engines. These are post-run regression-tested evaluation changes, not a new native qualification or a revision of the original 14/18 result. The current corpus still has a perfect baseline and does not distinguish additional agent value. A future claim needs prospectively declared measurements and fresh reserved data, as explained in [EVALUATION.md](EVALUATION.md).

### Performance and transport findings

Model-server logs show a generation slowdown during the development quality case and later cancellation around client deadlines. They do not identify the underlying cause. One reserved incident took 187.327 seconds: after its 90-second diagnostic timeout, a started Temporal workflow task expired late and was recovered. The final reserved incident took 210.917 seconds and reached the diagnostic activity timeout after its completion could not be recorded normally. Worker logs contain later heartbeat and completion-RPC transport errors. These observations are retained and require investigation; they are not replaced with an unsupported CPU, memory, grammar or network explanation.

The maximum sampled model RSS was **1,889,692 KiB**, approximately **1.80 GiB**. Samples cover direct supervisor children at 0.5-second intervals, exclude transient MCP children, and include shared/mapped pages. They are not a complete host memory profile or an OOM diagnosis.

The separate runbook load profile measured 17.753 seconds for twelve incidents, approximately 0.676 incidents/s, median 5.660 seconds and p95 6.150 seconds, with zero errors. Its predeclared gate was p95 at most 45 seconds and zero errors. This is bounded single-host runbook throughput; it does not characterize model capacity or prove scalability.

## Source and security checks

The frozen implementation passed **172 unit/boundary tests**, Ruff, JavaScript syntax validation and contract regeneration without drift. Real SQLite, cryptography and the actual MCP stdio contract exchange are used where declared; tests with fake Temporal/provider boundaries label that scope. The original JUnit report is in [security evidence](../evidence/security/).

After the qualification-harness and semantic-verifier corrections, subsequently committed as [`062daaf`](https://github.com/mehdisafer/governed-dataops-agents/commit/062daaf419b419665729e4c63c1fa6ddfeb7d8d2), the full local suite passed **232 tests**, with zero failures, errors or skips. This includes 61 synthetic qualifier-boundary cases and preserves all seven original closure/cleanup cases. Ruff, JavaScript syntax, contract regeneration and comparison of the unchanged application/model/prompt/corpus/lock inputs also passed. The [publication checks](../evidence/publication-checks/) retain those separate original reports; no fresh native integration is implied.

The frozen-source worktree scan covered 86 committed files. Its reachable-history scan covered three commits through `f1e6e2f`. Each retained **seven raw generic-key candidates**, with seven exact, recomputed non-secret proofs and zero unresolved findings. The candidates are legitimate idempotency identifiers in the unchanged development trace/history. Later expanded-artifact and publication scans retain their own raw counts and review records; these are not silently folded into the earlier seven-candidate result.

The strict pip-audit report covers fifty frozen runtime dependencies, with zero known vulnerabilities reported and zero skipped dependencies at its recorded query time. Its input requirements and lock hashes match the frozen source. The installed inventory records 61 distributions, 64 lock entries and six verified local runtime assets. The project's own licence remains undecided. These checks do not audit all OS packages, OCI layers or native code and do not certify security or licence compatibility. See [SECURITY.md](SECURITY.md), [THIRD_PARTY.md](THIRD_PARTY.md) and their retained originals.

## Deployment and CI gates

| Gate | Observed status | Evidence and consequence |
| --- | --- | --- |
| Native MCP / PydanticAI / Temporal / target execution | Executed | Actual processes and business-state observations retained; model reliability still failed |
| Reference Docker stack | Blocked before build | [Container run](../evidence/containers-f1e6e2f/run.json): Docker CLI/daemon unavailable; no stack or image was created |
| Terraform version / formatting / readonly initialization | Executed successfully | [Infrastructure evidence](../evidence/infrastructure-f1e6e2f/); Terraform 1.17.2 and pinned provider 4.7.0 |
| Terraform validation / local Docker plan | Not qualified | Provider schema/handshake failure during validation; no plan or apply executed |
| Browser rendering and interaction | Not qualified | Original Chromium socket-permission failure in the native results; no successful screenshot |
| GitHub Actions run 43597256488 | Failed before runner assignment | Both attempts of `core` have runner ID 0 and zero steps; the four dependent jobs were skipped |
| Public publication, project licence and protections | Pending | Repository remains private; no licence, billing, visibility or administration change was made |

The original [GitHub API observations](../evidence/github-actions-43597256488/) include one bounded retry. Log retrieval returned 404; the connector did not support reading the check annotation. A logged-out isolated cloud-browser view yielded no further diagnostic. The cause of the pre-run CI failure is therefore **unknown**. It is not reported as a failing project test, a confirmed billing issue, or a successful CI validation. The owner can inspect the annotation on the [failed core job](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43597256488/job/132455148696).

## Acceptance decision and next work

The backend's tested governance and recovery paths are implemented and evidenced. Full acceptance is withheld because the agent's reliability/value criterion failed and the operator-console/container/infrastructure gates lack successful execution evidence. Multi-host operation and partitioned queues also remain outside the measured reference profile.

The [prioritized backlog](BACKLOG.md) preserves those gaps without weakening the baseline, increasing deadlines to hide a failure, or relabelling a blocked check as passed. The [publication preparation](PUBLICATION.md) contains the concrete metadata and owner decisions required before public release. The reviewed implementation can be integrated for the maintainer's intended public portfolio while its experimental status stays explicit. No accepted-release tag or production-readiness claim follows from the successful subset; the maintainer handles visibility and licence decisions.
