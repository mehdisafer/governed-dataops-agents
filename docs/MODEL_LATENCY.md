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
| `stack_startup_all_services` | Successful start-and-health command of the **active stack** (initial `start-stack` or restored `start-restored-stack`); an initial project's startup timing must not be attributed to inference on a restored project. If no successful active-stack start was observed, the field is null |
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

## Post-merge source-matched evidence — 17 November 2026

[PR #21's original hosted run #44161986053](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44161986053)
and the [merged-main run #44163668519](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44163668519)
used the **same executable Git tree** at an explicit **2-CPU** model quota.
The former returned within the **69.247-second gate**; the latter
**failed the 94.880-second gate** with client `Agent.run` timed out
at **90.003133 s**. This is observed variability, not a proven cause.

The original mainline ZIP was independently checked and its readback
recorded in [issue #16](https://github.com/mehdisafer/governed-dataops-agents/issues/16).
Its **process-wide** llama.cpp counters changed by **721 prompt tokens /
72.4677 cumulative seconds** and **65 predicted tokens /
17.8181 cumulative seconds**, with all four cumulative counters
available. The two boundary queue gauges were zero. These counters
do not prove that every recorded server microsecond belonged to this
client request, and two zero endpoint gauges do not exclude an
intervening queue. The measured client model-slot wait was
**0.000023 s**; typed-business validation was not reached on the
timeout and must remain null.

The independent full model-evaluation job on the merged main source
also failed strict **model quality/value**, despite ten completed
responses in that separate run (**8/10** strict agent cases versus
**10/10** for the runbook). Container model availability and frozen
business-value acceptance must not be conflated.

The [prospective 2-CPU trial protocol](MODEL_LATENCY_TRIAL_PROTOCOL.md)
preregisters four new source-frozen runs, the needed resource/CPU
probes, denominators, stop conditions and explicit authorization veto.
It has **not been executed**. No sample-level reliability distribution,
mitigation or completed V1 acceptance is claimed.

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

**Still unverified:** internal server queue time or transient queue peaks,
startup time specific to the model service, request-exclusive prefill and
token-generation durations, CPU throttling and memory pressure in the
model container, native structured-output validation alone, and whether
runner contention changes these stages. Process-wide server prompt/predict
counters are observed but are **not request-exclusive timing**.
The typed business-precondition validator has its own duration when reached
but does not cover the entire validation pipeline. A controlled,
prospectively specified and separately authorized investigation is required
before closing issue #16.
