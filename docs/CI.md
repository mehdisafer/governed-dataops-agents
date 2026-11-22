# CI provenance and scope

## Current source execution — 23 November 2026

The complete [PR #25 run 45082434901](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/45082434901) checked out
preview `87da59dd`; the independent [main run 45083502058](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/45083502058)
checked out exact `ea80f2524060fcba745c23e85b344a9ad010b782`. Both use the verified tree
`60d4a8049a1cb02cc770ed4dc2c832c65c0e3ac4`. Both attempts completed **314 core
tests/Ruff, governance, real containers and infrastructure successfully**,
with **model-evaluation FAILED** and overall **FAILURE**. No skipped runtime
job is counted as an executed check in these two runs.

All ten original GHA ZIPs were independently downloaded, CRC checked and
SHA-256 matched; [QUALIFICATION.md](QUALIFICATION.md) records their identities.
Both worktree/history scans reported 31/62 raw candidates and zero unresolved
findings with source-specific proofs. The main's two CircleCI unit/security
statuses also read SUCCESS, separately from the still-failed model gate.

Any later documentation-only commit requires its own source/CI record.
A green core and skipped runtime profiles, if observed, must not replace
the full failed workflow or imply another model/container execution. The PR and main runs above are
source qualifications, not B01–B04; no manual retry or inference-triggering
workflow change accompanies this documentation update.

This repository has two independent CI providers. The results below are deliberately scoped to the **observed run's source SHA**. The unit check is now successful on an observed `main` SHA, and the separate container platform profile has passed on its recorded branch SHA. These scoped results do **not** establish model diagnostic value or production readiness.

## PR #21 — private llama.cpp metrics, executed source and outstanding quality gate

The historical [PR #21](https://github.com/mehdisafer/governed-dataops-agents/pull/21) merged into public `main` as [`4ec7adbf`](https://github.com/mehdisafer/governed-dataops-agents/commit/4ec7adbf204955081a4984afc29166d9c8a8e6f2). Its original corrected source `44dabbf`, preview `a636933` and final merge have **identical Git tree `ce5653be`**.

In [GitHub Actions PR run #44161986053](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44161986053), **core 292 tests/Ruff, governance, infrastructure and real containers SUCCESS**, while **model-evaluation FAILED**. CircleCI `build-and-test` and `publication-security` also succeeded on the exact reviewed PR head. An earlier revision failed two fake-qualifier tests; both were fixed without changing the model or diagnostic deadline. The real container log confirms a private restored-stack `llama.cpp` probe, 2-CPU model quota, **4/4 observed server counters**, and **69.247s model-response gate**; its independent `diagnostic_quality_passed` was **false**. [Original container ZIP #14363268796](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44161986053/artifacts/14363268796) is retained but its detailed binary counters have not been independently re-read via this connector. Process-wide counters cannot prove request-exclusive inference latency or transient queue peaks.

The independent [merged-`main` run #44163668519](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44163668519) completed on exact `4ec7adbf` (**identical Git tree**), with overall **FAILURE**: `core` **292 tests/Ruff**, `governance`, `infrastructure` **SUCCESS**, but `containers` and mandatory `model-evaluation` **FAILED**. The source-bound [main container artifact #14363928475](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44163668519/artifacts/14363928475) was uploaded and original logs show **4/4 cumulative server counters observed**, a restored 2-CPU model stack, **`real_local_model_response` FAILED at 94.880s** (`AssertionError`, no console reason), and `diagnostic_quality_passed=false`. The exact same tree had passed that response gate in **69.247s** on the PR preview. The [main model artifact #14364697423](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44163668519/artifacts/14364697423) retains the failed frozen 10-case evaluation. These data establish a **same-source latency/reliability discrepancy**, not its cause; the subsequent original-ZIP readback in [MODEL_LATENCY.md](MODEL_LATENCY.md) preserves **8/10** strict agent cases, four resolutions and the **90.003133-second** client timeout. The initial review was logs-only; the later archive observations do not turn either failed gate into a success. No second run or additional paid infrastructure was requested.

[Issue #16](https://github.com/mehdisafer/governed-dataops-agents/issues/16) remains open for causal localization and prospectively declared repeated 2-CPU evidence; [issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) stays open for measured model value and further production boundaries. Passing CircleCI/security does not override either substantive failure.

## Historical PR #17 instrumentation: exact-tree CI and non-acceptance — 17 November 2026

The runtime-qualified `main` revision at that checkpoint was [`263a6c1c7226`](https://github.com/mehdisafer/governed-dataops-agents/commit/263a6c1c72260c7be6ba7ba7aeb1a4a891b7f41f), integrating [PR #17](https://github.com/mehdisafer/governed-dataops-agents/pull/17) after concurrent docs-only changes. [GitHub Actions #43990582623](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43990582623) ran the preview commit `158e52c5`, **identical Git tree** `77c18f708010dc51687d5e6022000eb6a05f4d18` to PR source `e81309b`: Core **284 tests/Ruff PASS**, Governance **PASS**, Containers **10/10 platform PASS**, Infrastructure **PASS**, and **model-evaluation FAILED** (runbook 10/10, local agent 6/10 with ten actual responses). CircleCI build/test and publication-security both passed on `e81309b`. This is a **failed overall agent-value acceptance**, not an infrastructure test error.

The original [container artifact #14288017124](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43990582623/artifacts/14288017124) independently confirms `model-latency.json` now attributes **17.568490s** startup to the *restored stack used by inference*, not the initial stack's **18.442006s**. The prior misattribution was fixed and real-run verified without increasing model timeout or changing model outputs. The original frozen [evaluation artifact #14288370568](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43990582623/artifacts/14288370568) retains failures and all ten cases.

**Independent post-merge `main` proof:** [GitHub Actions run #43992090061](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43992090061) completed on exact merged source `263a6c1c72260c7be6ba7ba7aeb1a4a891b7f41f`. **Core 284 tests/Ruff, Governance, Containers (ten platform checks) and Infrastructure all SUCCESS; model-evaluation FAILED**, so overall workflow conclusion was **failure**. The [original mainline model artifact #14288013914](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43992090061/artifacts/14288013914) was downloaded and its original `comparison.json` verified (ZIP integrity PASS, 120 entries, SHA-256 `dd572cb2572d0b5ecc9e55c127522655a47104a24881db7adf691098934744e8`): runbook **10/10**, model **6/10** strict, all ten responses observed, **model resolved 2**, runbook resolved **6**; model case median/p95 **24.6661/28.0617s**, runbook **3.93485/6.2401s**, and zero observed unjustified/unknown effects. These are distinct measurements from the PR-head 6/10 run, which resolved three rather than two cases. Both remain failures of the unwaived value criterion.

[Original mainline container #14287384372](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43992090061/artifacts/14287384372) was also downloaded and integrity-checked (146 entries, SHA-256 `38ea1171dbfb9ed3feeeff89b88149d83a9934b017f3d322976220c82632333a`). Its source remained unchanged, credential scan passed, ten platform checks passed and semantic `diagnostic_quality_passed=false`. `commands.json` confirms initial stack **17.926662s**, restored stack **18.077121s**; `model-latency.json` correctly selects the **18.077121s restored stack**, with full agent gate **66.719662s**, inclusive `Agent.run` **63.465644s**, client slot wait **0.000016s** and independent typed business validation **0.000022s**. Inference-only and llama.cpp server queue time remain null/unobserved.



## Previous guarded-source post-merge CI — 17 November 2026

After [security PR #13](https://github.com/mehdisafer/governed-dataops-agents/pull/13),
the exact `main` SHA `9635dbccfe8cfd168f14ee9380eeb1f03e105a0c`
completed [GitHub Actions run #43988865699](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43988865699).
**The run conclusion is FAILURE**, because its frozen `model-evaluation`
job is genuinely red (**agent 7/10**, competent runbook **10/10**). In the
same run, **`core` (272 Python tests), `governance`, `containers`, and
`infrastructure` all SUCCESS**. Both CircleCI
`ci/circleci: build-and-test` and `ci/circleci: publication-security`
were **SUCCESS** on that same SHA.

The actual [model-evaluation artifact #14286528694](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43988865699/artifacts/14286528694)
has been downloaded and independently inspected: all ten agent responses
completed, three contradictory typed-snapshot proposals were refused with
zero effects, no measured agent advantage. The original container
[artifact #14285959973](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43988865699/artifacts/14285959973)
retains `diagnostic_quality_passed=false`. **A safely refused model proposal
is not a correct diagnosis**. This is a source-specific security/Temporal
platform qualification, not a green overall V1.

The actual opt-in two-queue Temporal profile and SQLite/Ed25519 partition
authority regressions are included in this source. Remaining source CI
does not validate LLM throughput isolation, dynamic partition migration,
independent tenant security, multi-host or production operations.

## CircleCI unit checks

- Pipeline configuration: [`.circleci/config.yml`](../.circleci/config.yml).
- Suite configuration: [`.circleci/test-suites.yml`](../.circleci/test-suites.yml).
- Source: CircleCI GitHub App project `mehdisafer/governed-dataops-agents`; `build-and-test` runs with `cimg/python:3.12`, the frozen project dependencies, Ruff, `circleci testsuite doctor`, the `python-unit` suite and JUnit uploads.
- **Observed PASS:** [CircleCI pipeline #9](https://app.circleci.com/pipelines/circleci/Um5XQQtD4BE9Jcfy4XTzBb/4P4AtAuA5YqBNdWVbP3AXC/9), job `build-and-test` #17, executed 2026-11-15 on commit `25913b0c3a0fa7ab6f2aaf6d6146dac5e61da323` on `circleci-project-setup`. Earlier pipelines #7 and #8 also report success on earlier commits. This is a unit/lint pipeline result, **not** proof of container behavior.
- The two unit configuration files have unchanged Git blob identities after that passing commit (the reviewed setup-branch head was `cad9cc6eb28a70f24e9bf02774a7614cc4cb9631`); the application sources, tests and lock file are unchanged relative to the base `main` on that branch. The merged `main` source `2460012b4ef460dc33a3389a8ece0341a709d033` subsequently received a [successful CircleCI unit status](https://app.circleci.com/workflow/9f31433c-2712-467c-89be-34ad2c3285c8/job/9d5fd2e8-3c67-4a35-861c-6feb9a735ea7).

Do not automatically run costly machine/model evaluation on ordinary documentation pushes. No paid CircleCI plan or additional credit allocation is authorized by these repository files.

## Manual real-container qualification

The [`.circleci/reference.yml`](../.circleci/reference.yml) file is a **different manual pipeline definition**. Its `machine` executor, `large` resource class, real Docker Compose stack, local model and Temporal tests can consume more resources than the unit workflow.

- **Observed FAIL:** [CircleCI container pipeline #10](https://app.circleci.com/pipelines/circleci/Um5XQQtD4BE9Jcfy4XTzBb/4P4AtAuA5YqBNdWVbP3AXC/10), [job #18](https://app.circleci.com/pipelines/circleci/Um5XQQtD4BE9Jcfy4XTzBb/4P4AtAuA5YqBNdWVbP3AXC/10/workflows/3294d37b-e8f3-47ac-a3a7-1d9df18f8315/jobs/18), on `25913b0`, 2026-11-15. The exact failing command and original logs were not available in the read-only pipeline listing and have not been independently verified.
- **Observed PASS at corrected source:** [CircleCI reference-container workflow](https://app.circleci.com/workflow/15f6d873-dc0d-4e83-8d20-d3abf1ec20c9) reported success at `cad9cc6eb28a70f24e9bf02774a7614cc4cb9631` after asset-permission, network, volume and CPU-quota fixes. The [qualification ledger](QUALIFICATION.md) reports ten passed container-execution checks, but `diagnostic_quality_passed=false`: the model proposed an incorrect action and independent policy denied it. Later commits through `e71638b` modify documents only.
- [PR #4](https://github.com/mehdisafer/governed-dataops-agents/pull/4) records the integration of corrected platform source and the hosted evidence. The model-quality/value gate remains open regardless of platform CI status.
- The historical reserved comparison remains agent **2/10** versus runbook **10/10**, and the later hosted frozen comparison at `924dd24` was agent **1/10** versus runbook **10/10**. Neither establishes model advantage.

## GitHub Actions — historical runner failures and subsequent real qualification

Earlier GitHub Actions [run 43769325453](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43769325453) failed **before runner assignment**: `core` had zero steps. That historical provider/account cause remains unproven. Later, on 16 November, runner-assigned [full run 43919667084 at `7b709ff`](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43919667084) completed `core`, `governance`, `containers` and `infrastructure` successfully, but **failed `model-evaluation`**. The core scanned the worktree/history (31/62 raw Gitleaks findings, reviewed as non-secrets), completed its dependency audit and 232 tests. The real container platform passed with `diagnostic_quality_passed=false`; the Terraform local plan succeeded without `apply`. Separate [docs-only run 43924763001 at `351817e`](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43924763001) succeeded in `core` with **245 tests**, Ruff, scanned history and no unresolved package licence metadata; governance, containers, infrastructure and model-evaluation were **skipped**. The original runner-allocation cause is not determined by this later success, and the model's failed value criterion is not resolved.

## Required owner-side CircleCI configuration checks

For the GitHub App integration, each pipeline has its own **configuration source**, **checkout source** and **trigger** in CircleCI Project Setup. Ensure that:

1. The ordinary `build-and-test` pipeline reads `.circleci/config.yml` from this repository and checks out the intended commit/branch, especially after integration into `main`.
2. Its push/PR triggers match the intended source, and no double-trigger causes unplanned usage.
3. The manual reference pipeline reads `.circleci/reference.yml`, is not made a routine required check, and is invoked only with explicit authorization for machine resources.
4. Each reported job is tied to an observed checkout SHA and its original artifacts. A failed, skipped, missing or pre-run job is not PASS.
5. Treat the old zero-runner checks as historical; new GitHub Actions runners now execute real jobs. Keep original failure records without guessing whether repository visibility caused the change.

Do not change account billing, increase usage limits, or silently select another execution provider to hide a failing acceptance criterion.

## Automated publication security gate — observed on `main`

The ordinary CircleCI workflow now proposes a separate `publication-security` job running on the lightweight `cimg/python:3.12` Docker image with `resource_class: small`. It **does not** launch the large machine/model reference, buy credits, modify settings or use any external inference provider.

The job explicitly fetches all visible branches and tags and rejects a shallow or incomplete Git history. It invokes the repository's checksum-pinned Gitleaks wrapper twice: once on the Git-aware worktree (including tracked ignored files) and once on every reachable Git ref. Each result retains raw redacted findings and recomputed non-secret review proofs; missing scans and unresolved findings produce nonzero exits. The published job artifact contains both JSON reports, source SHA, visible refs and exit status.

A separate wheel check builds with pinned Hatchling, verifies the PEP 639 SPDX `License-Expression: Apache-2.0`, matches the embedded `LICENSE` bytes to this repository, and rejects private/runtime/evidence paths in the distributable wheel. This test does not publish to PyPI or establish third-party licence compatibility.

A separate component inventory and strict pip-audit of frozen runtime requirements run even if the scanner step fails, and retain their original reports as job artifacts. Installed licence metadata is a provenance observation rather than a legal compatibility verdict. Scanner limitations include unreachable dangling objects, opaque compressed archive interiors, false negatives and credentials outside the Git repository. Existing separately reviewed expanded archives retain their own content manifests and provenance.

**Observed on 16 November 2026:** GitHub's commit-status API reports both `ci/circleci: publication-security` ([successful hosted job](https://app.circleci.com/workflow/592660d1-ce36-46b0-b3c0-373cdd13d005/job/b3f0e796-3e8f-4f0f-be65-1eb4b8f3df74)) and `ci/circleci: build-and-test` ([successful hosted job](https://app.circleci.com/workflow/592660d1-ce36-46b0-b3c0-373cdd13d005/job/44a8eef9-50da-4b35-aa47-8058d29bbaee)) as **success** at PR head `10f1510f4eab314c0679c384ad1ef4341cac8254`. This establishes hosted job conclusions on that exact source, **not independent reinspection of artifact JSON, full-history coverage, component inventory or vulnerability detail**. The merged `main` subsequently reported **success** at `9b41e2a1a5f5fe5696dbbbb1561ac616238ee206` for [publication-security](https://app.circleci.com/workflow/b56c8a6e-7331-4c6a-b003-f36eb2a68cc9/job/d280075d-b0bf-4922-a90d-5f9499c741d6) and [build-and-test](https://app.circleci.com/workflow/b56c8a6e-7331-4c6a-b003-f36eb2a68cc9/job/6749ffb0-bfd0-43da-831f-0d798c0abae6). GitHub reports this repository **public** on 16 November. A subsequent documentation edit needs its own CI; scanned refs, findings and original reports still require artifact-level review. Neither public visibility nor a green job badge proves the agent-evaluation gate. No broad ignore or generic hexadecimal waiver is authorized.

**Additional exact-source observation:** the public `main` commit [`351817e`](https://github.com/mehdisafer/governed-dataops-agents/commit/351817eeecc969dd13491e592b3510f8ae38ea7d) reported both CircleCI `build-and-test` and `publication-security` **SUCCESS**, alongside GitHub Actions `core` SUCCESS. These jobs and their content-bound reviewed findings do not cover unreachable Git objects or opaque archive interiors, and do not constitute a blanket security certification.
