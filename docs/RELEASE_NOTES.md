# Release candidate: v0.1.0a1

**State: unreleased private candidate.** This identifier does not mark a passed model-quality gate or a production release. The final delivered source commit, CI runs and retained evidence are identified in [QUALIFICATION.md](QUALIFICATION.md).

## Included

- An authenticated operator console and API with scoped incident traces, explicit diagnostic engine selection, separate approval credentials and cancellation.
- Five row-based synthetic incident fixtures: freshness, transient failure, schema drift, quality rejection and duplicate delivery.
- Real MCP stdio capabilities, PydanticAI structured local inference and a Temporal workflow with bounded activities, approval signals and replay support.
- Independent deterministic policy, canonical plan digests, signed and persisted approvals, fresh revision checks and one-action budgets.
- Atomic business effects and receipts, reconciliation after a deliberately lost HTTP response, idempotent event admission and bounded backpressure.
- Frozen dependencies and schemas, native/container qualification harnesses, CI, security/component inventories and deployment/recovery procedures.

## Known release gates

The local Qwen Q2 candidate completed the frozen development trial but selected the correct category and action in only two of five cases. Correct output syntax and citations do not establish diagnostic correctness. The held-out comparison and its exact observed result remain authoritative for this candidate. No value over the competent deterministic runbook is claimed merely because the model generated an explanation.

Native services, Docker execution, Terraform validation, browser behavior, load, replay and restore are separate gates. Their statuses are recorded individually; a blocked or failed check is not represented as a pass. The repository licence, public visibility change, repository metadata administration and any branch-protection setup remain owner decisions or connector-dependent actions.

## Installation and compatibility

Python 3.12 and the committed `uv.lock` define the Python environment. The reference runtime is private Linux amd64 with local SQLite persistence and a local CPU model. Read [DEPLOYMENT.md](DEPLOYMENT.md) before starting it. The target schema version is 1; newer schemas are rejected rather than automatically downgraded. Rollback requires a stopped, paired restore of application and Temporal state with the matching signing identity.

## Evidence and review

The implementation PR links issue #1 and records automated review findings, fixes, tests and remaining limits. Reviews performed by the authoring automation are labelled as such; they are not an independent human approval. No tag, GitHub release or public visibility change is created by this document.
