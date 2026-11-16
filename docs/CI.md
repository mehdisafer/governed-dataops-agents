# CI provenance and scope

This repository has two independent CI providers. The results below are deliberately scoped to the **observed run's source SHA**. The unit check is now successful on an observed `main` SHA, and the separate container platform profile has passed on its recorded branch SHA. These scoped results do **not** establish model diagnostic value or production readiness.

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

## GitHub Actions is a different failure domain

GitHub Actions [run 43769325453](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43769325453) on the merged CircleCI unit-configuration commit failed before assigning a runner. The [core job](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43769325453/job/132981467752) had runner ID 0, **zero executed steps**, and downstream jobs were skipped; attempting to fetch the job logs returned `404 BlobNotFound`. The cause is not confirmed. This does **not** mean the test suite itself failed, nor does the CircleCI unit PASS resolve the GitHub Actions runner problem.

## Required owner-side CircleCI configuration checks

For the GitHub App integration, each pipeline has its own **configuration source**, **checkout source** and **trigger** in CircleCI Project Setup. Ensure that:

1. The ordinary `build-and-test` pipeline reads `.circleci/config.yml` from this repository and checks out the intended commit/branch, especially after integration into `main`.
2. Its push/PR triggers match the intended source, and no double-trigger causes unplanned usage.
3. The manual reference pipeline reads `.circleci/reference.yml`, is not made a routine required check, and is invoked only with explicit authorization for machine resources.
4. Each reported job is tied to an observed checkout SHA and its original artifacts. A failed, skipped, missing or pre-run job is not PASS.
5. The separate GitHub Actions runner annotation is read from the owner's authenticated interface; do not speculate about billing or runner availability.

Do not change account billing, increase usage limits, or silently select another execution provider to hide a failing acceptance criterion.

## Automated publication security gate — PR execution observed

The ordinary CircleCI workflow now proposes a separate `publication-security` job running on the lightweight `cimg/python:3.12` Docker image with `resource_class: small`. It **does not** launch the large machine/model reference, buy credits, modify settings or use any external inference provider.

The job explicitly fetches all visible branches and tags and rejects a shallow or incomplete Git history. It invokes the repository's checksum-pinned Gitleaks wrapper twice: once on the Git-aware worktree (including tracked ignored files) and once on every reachable Git ref. Each result retains raw redacted findings and recomputed non-secret review proofs; missing scans and unresolved findings produce nonzero exits. The published job artifact contains both JSON reports, source SHA, visible refs and exit status.

A separate component inventory and strict pip-audit of frozen runtime requirements run even if the scanner step fails, and retain their original reports as job artifacts. Installed licence metadata is a provenance observation rather than a legal compatibility verdict. Scanner limitations include unreachable dangling objects, opaque compressed archive interiors, false negatives and credentials outside the Git repository. Existing separately reviewed expanded archives retain their own content manifests and provenance.

**Observed on 16 November 2026:** GitHub's commit-status API reports both `ci/circleci: publication-security` ([successful hosted job](https://app.circleci.com/workflow/592660d1-ce36-46b0-b3c0-373cdd13d005/job/b3f0e796-3e8f-4f0f-be65-1eb4b8f3df74)) and `ci/circleci: build-and-test` ([successful hosted job](https://app.circleci.com/workflow/592660d1-ce36-46b0-b3c0-373cdd13d005/job/44a8eef9-50da-4b35-aa47-8058d29bbaee)) as **success** at PR head `10f1510f4eab314c0679c384ad1ef4341cac8254`. This establishes hosted job conclusions on that exact source, **not independent reinspection of artifact JSON, full-history coverage, component inventory or vulnerability detail**. A subsequent documentation edit must obtain its own CI; the exact merged `main` SHA must also be checked before any public-visibility decision. Scan findings, scanned refs and retained artifacts must be reviewed, not inferred solely from a green job badge. No broad ignore or generic hexadecimal waiver is authorized.
