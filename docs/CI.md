# CI provenance and scope

This repository has two independent CI providers. The results below are deliberately scoped to the **observed run's source SHA**. This document does not certify the current default branch, a Docker deployment, or model quality.

## CircleCI unit checks

- Pipeline configuration: [`.circleci/config.yml`](../.circleci/config.yml).
- Suite configuration: [`.circleci/test-suites.yml`](../.circleci/test-suites.yml).
- Source: CircleCI GitHub App project `mehdisafer/governed-dataops-agents`; `build-and-test` runs with `cimg/python:3.12`, the frozen project dependencies, Ruff, `circleci testsuite doctor`, the `python-unit` suite and JUnit uploads.
- **Observed PASS:** [CircleCI pipeline #9](https://app.circleci.com/pipelines/circleci/Um5XQQtD4BE9Jcfy4XTzBb/4P4AtAuA5YqBNdWVbP3AXC/9), job `build-and-test` #17, executed 2026-11-15 on commit `25913b0c3a0fa7ab6f2aaf6d6146dac5e61da323` on `circleci-project-setup`. Earlier pipelines #7 and #8 also report success on earlier commits. This is a unit/lint pipeline result, **not** proof of container behavior.
- The two unit configuration files have unchanged Git blob identities after that passing commit (the reviewed setup-branch head was `cad9cc6eb28a70f24e9bf02774a7614cc4cb9631`); the application sources, tests and lock file are unchanged relative to the base `main` on that branch. Nevertheless, success must be confirmed on the exact integrated `main` commit.

Do not automatically run costly machine/model evaluation on ordinary documentation pushes. No paid CircleCI plan or additional credit allocation is authorized by these repository files.

## Manual real-container qualification (separate draft PR)

The source branch's [`.circleci/reference.yml`](https://github.com/mehdisafer/governed-dataops-agents/blob/circleci-project-setup/.circleci/reference.yml) is a **different manual pipeline definition**. Its `machine` executor, `large` resource class, real Docker Compose stack, local model and Temporal tests can consume more resources than the unit workflow.

- **Observed FAIL:** [CircleCI container pipeline #10](https://app.circleci.com/pipelines/circleci/Um5XQQtD4BE9Jcfy4XTzBb/4P4AtAuA5YqBNdWVbP3AXC/10), [job #18](https://app.circleci.com/pipelines/circleci/Um5XQQtD4BE9Jcfy4XTzBb/4P4AtAuA5YqBNdWVbP3AXC/10/workflows/3294d37b-e8f3-47ac-a3a7-1d9df18f8315/jobs/18), on `25913b0`, 2026-11-15. The exact failing command and original logs were not available in the read-only pipeline listing and have not been independently verified.
- Later commits on `circleci-project-setup` include fixes for immutable model-asset directory traversal, internal/ingress network isolation, non-root volume ownership and the model CPU quota. No successful real-container run at the revised head is established by the inspected observations.
- [PR #4](https://github.com/mehdisafer/governed-dataops-agents/pull/4) retains the remaining runtime/deployment changes **as a draft**, until original job evidence and a successful revised-container execution are available.
- Even a successful container build is not evidence that the agent outperforms the deterministic runbook. The frozen comparison remains agent **2/10** vs runbook **10/10** strict successes.

## GitHub Actions is a different failure domain

GitHub Actions [run 43754179426](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43754179426) on the Apache-2.0 licence commit failed before assigning a runner. The `core` job had runner ID 0, **zero executed steps**, and downstream jobs were skipped; attempting to fetch the job logs returned `404 BlobNotFound`. The cause is not confirmed. This does **not** mean the test suite itself failed, nor does the CircleCI unit PASS resolve the GitHub Actions runner problem.

## Required owner-side CircleCI configuration checks

For the GitHub App integration, each pipeline has its own **configuration source**, **checkout source** and **trigger** in CircleCI Project Setup. Ensure that:

1. The ordinary `build-and-test` pipeline reads `.circleci/config.yml` from this repository and checks out the intended commit/branch, especially after integration into `main`.
2. Its push/PR triggers match the intended source, and no double-trigger causes unplanned usage.
3. The manual reference pipeline reads `.circleci/reference.yml`, is not made a routine required check, and is invoked only with explicit authorization for machine resources.
4. Each reported job is tied to an observed checkout SHA and its original artifacts. A failed, skipped, missing or pre-run job is not PASS.
5. The separate GitHub Actions runner annotation is read from the owner's authenticated interface; do not speculate about billing or runner availability.

Do not change account billing, increase usage limits, or silently select another execution provider to hide a failing acceptance criterion.
