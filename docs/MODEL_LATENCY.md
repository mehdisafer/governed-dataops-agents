# Bounded local-model latency evidence

**Scope:** synthetic, single-host reference. This instrumentation addresses
[issue #16](https://github.com/mehdisafer/governed-dataops-agents/issues/16)
without changing model weights, prompt, the 90-second diagnostic budget,
retry policy, inference provider or deterministic authorization.

## Observed background (separate original sources)

Three hosted container cases at an explicit two-CPU model quota had mixed
outcomes: 76.514 seconds (response gate passed), 94.253 seconds (failed),
and 70.876 seconds (successful targeted retry). These values are original
**full gate wall durations**, not isolated inference times. Two executions
share a source and one was a retry. The sample cannot establish a latency
distribution, root cause or semantic quality improvement.

Real container platform success may occur with
`diagnostic_quality_passed=false`; a model response that is wrong or whose
business effects fail the intended outcome is **not** an accepted diagnosis.

## New source-bound evidence

The real-container harness writes `model-latency.json` on both completed
and failed model probes and adds command wall durations to `commands.json`.
A timed-out/incomplete model probe also leaves a minimal
`model-quality.json` reporting `quality_assessed=false` and the exception
**type**, without silently marking a result PASS. The client worker records
`client_model_slot_wait_seconds` in both successful diagnosis and
`diagnostic_failed` traces. This measures the local worker semaphore,
**not** queueing inside llama.cpp.

| Field in `model-latency.json` | What is actually measured |
| --- | --- |
| `stack_startup_all_services` | Docker Compose start-and-health command, including all containers |
| `api_admission_http` | Demo incident admission HTTP request wall time |
| `workflow_poll_until_terminal_or_failure` | Polling elapsed until durable closure or an exception |
| `client_model_slot_wait` | Worker-side semaphore acquisition; null if unobserved |
| `diagnostic_call_including_validation` | Existing PydanticAI call duration; includes generation, transport and validation |
| `agent_run_including_native_output_validation` | Duration of `Agent.run`, including transport, inference and native structured-output checks; not inference-only |
| `typed_business_validation` | Duration of the independent typed-snapshot business-precondition guard, when reached |
| `full_agent_gate` | Harness model-probe wall time |
| `model_only_startup_readiness`, `server_internal_queue_wait`, `inference_only`, `semantic_validation_only` | **Null / not separately observed** |

A null measurement is unknown, **not zero**. The JSON report includes the
model CPU override and only whitelisted numeric/Boolean trace fields; it does
not duplicate raw prompt, untrusted logs, credentials, model proposals or
tokens. The separate original trace remains available in the scoped
`model-quality.json` and incident records where collected.

## Qualification protocol

- Build from a clean recorded commit, run the existing bounded container
  qualification, retain `run.json`, `commands.json`, `checks.json`,
  `model-latency.json`, `model-quality.json`, original service logs and
  cleanup proof. The branch is not qualified until its own CI executes.
- Use development fixtures for investigation. Reserve a repetition matrix
  **before** running it; do not relabel previously inspected held-out cases
  as unseen or exclude failures from denominators.
- Preserve original 90-second diagnostic timeout during baseline measurement.
  Keep all resource/CPU counts and runner identities with source SHA.
- Treat missing/cancelled/incomplete or server-nonresponse traces as failures
  with stage values marked unknown. Never substitute the deterministic runbook
  or external inference behind the same case identifier.
- Do not compute p95 from a few anecdotes or claim an inferred model-server
  queue time from the total elapsed and client-side wait.

**Still unverified:** internal server queue time, startup time specific to the
model service, separate model prefill/token generation and native structured-
output validation, and whether variation comes from runner contention, model
service execution or other stages. The typed business-precondition validator
now has its own duration but does not cover the entire validation pipeline. A controlled repeated source-correlated investigation is required
before closing issue #16.
