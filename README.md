# Governed DataOps Agents

I am building an evidence-led incident response system for a synthetic industrial data platform. The goal is an operator console that explains an incident, the evidence behind its diagnosis, the proposed action, its authorization, and the verified business outcome.

The implementation uses MCP for narrowly scoped capabilities, PydanticAI for structured diagnosis, and Temporal as the durable workflow authority. Model proposals do not grant permissions. Every effect must pass deterministic policy and be verified against fresh target state.

## Delivery scope

- Five reproducible incident classes: stale data, transient failures, incompatible schema, rejected quality batches, and duplicate processing risk.
- Scoped approvals, idempotent effect reconciliation, restart/replay tests, and a deterministic baseline comparison.
- A reproducible private demonstration, container reference deployment, observable operations, and original test evidence.

## Status

Initial inventory: this repository was empty. Implementation and acceptance are tracked in [issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1). No runtime or production acceptance is claimed by this initial commit.

The project uses synthetic data and no client systems. A repository licence has not yet been selected; third-party components retain their own licences.
