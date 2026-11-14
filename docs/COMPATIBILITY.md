# Runtime compatibility and trust boundaries

The selected runtime is Python 3.12. Direct dependencies are pinned in
`pyproject.toml`, and the lockfile records the resolved transitive graph.
Compatible dependency metadata is not evidence of an integrated deployment;
execution and model-quality results belong to the dated qualification records.

## Official release baseline

| Component | Version | Python requirement | License |
| --- | --- | --- | --- |
| MCP Python SDK | 2.3.0 | >=3.10 | MIT |
| PydanticAI Slim | 2.68.0 | >=3.11 | MIT |
| Temporal Python SDK | 1.36.0 | >=3.11 | MIT |

The following official tagged manifests and the corresponding publisher metadata
on PyPI were checked on 2026-11-14. Installed distributions and constructor
signatures were then inspected in the isolated project environment.

- [MCP v2.3.0 manifest](https://github.com/modelcontextprotocol/python-sdk/blob/v2.3.0/pyproject.toml)
- [PydanticAI v2.68.0 manifest](https://github.com/pydantic/pydantic-ai/blob/v2.68.0/pydantic_ai_slim/pyproject.toml)
- [Temporal 1.36.0 manifest](https://github.com/temporalio/sdk-python/blob/1.36.0/pyproject.toml)

MCP and PydanticAI require Pydantic >=2.12. Temporal's Pydantic extra supports
Pydantic >=2,<3. MCP uses HTTPX2 >=2.10; PydanticAI uses HTTPX2 >=2.7, and its
OpenAI extra requires OpenAI Python >=3.31. The restored environment uses
Pydantic 2.14.3, HTTPX2 2.16.0 and OpenAI Python 3.51.0. These are deliberately
pinned baselines, not a claim that every later release is interchangeable.

No upstream source code is vendored into this repository.

## MCP transport

The official v2 SDK exposes `MCPServer` and `Client`. Each worker tool call starts
the package's fixed stdio server in a subprocess. Incident metadata never chooses
a shell command. Only reader/executor credentials and the configured target
endpoint are supplied to the MCP subprocess. The model has no MCP connection and
receives no tool definitions.

The only tools are `collect_evidence`, `execute_action`, and `reconcile_effect`.
Inputs and outputs cross versioned Pydantic contracts. The client checks both
`is_error` and `structured_content`: a successful protocol exchange does not
establish a complete business result. A broken execution response becomes an
unknown outcome and requires a target-journal read.

Sources: [client API](https://py.sdk.modelcontextprotocol.io/client/),
[transport lifecycle](https://py.sdk.modelcontextprotocol.io/client/transports/),
[server execution](https://py.sdk.modelcontextprotocol.io/run/).

## PydanticAI model boundary

`OpenAIChatModel`, an explicit `OpenAIProvider(openai_client=...)`, and
`NativeOutput(Diagnosis, strict=True)` connect to a configured local
OpenAI-compatible inference server. This is a local-model integration using that
protocol. It is not an OpenAI-hosted model deployment.

The local decoding grammar keeps required fields, enum choices and the rejection
of extra fields. It omits string-length and array-count bounds from the native
grammar because long bounded strings can cause expensive grammar expansion.
The original `Diagnosis` model still validates every original bound after
decoding. Generation places factual summary, evidence references and rationale
before category/action. The output contract is unchanged; generation order and
the native schema hash are recorded in each model trace. Correctness is measured
separately on development and held-out incidents.

Complete evidence and matching target/environment/scope are required before a
model request. Returned evidence references must match the actual collected
observation. A valid JSON shape does not prove a correct diagnosis. A separate
deterministic policy checks the proposal against current business state and
authorization before any effect can occur.

Logs and incident descriptions are untrusted data. The prompt names that boundary;
stronger controls are the absence of model tools, a finite action catalog, target
authorization, signed approvals, and fresh pre/postcondition checks. Diagnostic
context is bounded without silent truncation. Credentials are scrubbed from that
context. HTTP clients do not inherit ambient proxies or follow redirects.

Provider retries are disabled. PydanticAI allows at most two requests, including
one output-validation retry, inside one overall diagnostic timeout. There is no
automatic fallback to an external provider or to the deterministic runbook.
The runbook is a separately selected and separately labelled comparison mode.

Traces distinguish an attempted request, an observed model response, and a valid
diagnosis. `model_used` means a completed model response was observed. A false
value after a timeout does not establish that the server performed no computation;
usage completeness and its accompanying note preserve that uncertainty.
The request fingerprint includes prompt/context hashes, model identity, configured
revision, parameters and native-schema hash. It is an application request
fingerprint, not a certificate of the server's actual weights.

External inference requires explicit deployment authorization, HTTPS and a separate
credential. Its provider cost remains unknown without a configured price. Local
traces report provider charge separately from unmeasured compute and energy.
Runtime provenance must additionally record the actual weight-file digest and
server command. Model licence and quantization provenance are distinct from the
licence of this repository.

Sources: [OpenAI-compatible provider](https://pydantic.dev/docs/ai/models/openai/),
[structured outputs](https://pydantic.dev/docs/ai/core-concepts/output/).

## Temporal authority and effects

`IncidentWorkflow` performs deterministic decisions, timers, activity commands,
queries and signals. Model calls, MCP, SQLite, HTTP and wall-clock expiry checks
occur only in activities. Ingress must supply `created_at`; workflow validation
must not invoke a wall-clock default during replay.

Approval signals carry references to durable authenticated approval records.
Signal identity fields alone do not establish trust. The API signs the exact
envelope with its Ed25519 private key. Activities and the target verify with the
public key, including the stored record and current plan/preconditions. Workers
receive neither the signing key nor approver credentials. Redelivering an
identical signed envelope does not consume another approval attempt.

Every execution activity first reads the target receipt using the same
deterministic idempotency key. That receipt survives a lost activity response and
is consulted before rejecting a revision made stale by its own successful effect.
The synthetic target atomically commits business rows and the receipt. An
uncertain write with no proven receipt escalates instead of being blindly
repeated. This guarantee depends on this target's transaction model; it is not
a promise about arbitrary external services or arbitrary MCP servers.

The workflow bounds approval time, distinct approval attempts, activity timeouts
and retries. Cancellation observed before dispatch prevents an effect, including
cancellation received during the preceding audit write. A later cancellation
still requires reconciliation and business verification; it does not claim
rollback of a committed effect.

The `incident-v1` patch marker establishes the orchestration baseline. Retained
real histories must be replayed before command order changes or marker removal.
Replaying a same-build history tests determinism; an upgrade claim additionally
requires histories from the previous build and the identities of both builds.

Sources: [conversion and replay](https://github.com/temporalio/sdk-python/blob/1.36.0/README.md),
[signals](https://docs.temporal.io/develop/python/workflows/message-passing),
[workflow versioning](https://docs.temporal.io/develop/python/workflows/versioning).

## Capacity and evidence limits

API admission bounds pending incidents. Temporal owns the durable queue and worker
activity capacity. Model semaphores apply per worker process; the model server's
decoding slots and memory caches are separate limits. Target transactions and
optimistic revision checks protect business state across workers. These controls
do not establish an unlimited-throughput or production-scalability claim.

The CPU inference profile explicitly bounds context, decoding slots, batch sizes
and memory caches. Disabling weight repacking can reduce memory duplication at
the cost of speed. Capacity claims must use observed resource measurements and
include the model plus the rest of the deployed stack.

`tests/test_runtime.py` includes a real stdio MCP catalog/contract test. Its
`FixtureGateway` tests deliberately bypass HTTP/MCP and do not establish a real
model or Temporal deployment. The cancellation regression uses explicit activity
stubs. Real integration, replay and model-quality evidence are recorded separately.
A missing model, failed service, timeout or invalid output remains a failure;
none is represented as a successful mocked integration.

Earlier transient-workspace execution files were lost before reconstruction.
They are not reused as acceptance evidence. Only retained, dated results from
the rebuilt source can support the current qualification.
