# Bounded local-model latency evidence

**Scope:** synthetic, single-host reference. This instrumentation addresses
[issue #16](https://github.com/mehdisafer/governed-dataops-agents/issues/16)
without changing model weights, prompt, the 90-second diagnostic budget,
retry policy, inference provider or deterministic authorization.

## Source-qualified resource observations — 23 November 2026

[PR #25](https://github.com/mehdisafer/governed-dataops-agents/pull/25) was
qualified in [run 45082434901](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/45082434901)
on actual preview `87da59dd4e7989bb7a830867557e165af608f3aa`; its head
`29a377efc7cf7f85c6b4f48803d8f2634701172c` has the same Git tree
`60d4a8049a1cb02cc770ed4dc2c832c65c0e3ac4`.
The independent [main run 45083502058](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/45083502058)
used exact merged commit `ea80f2524060fcba745c23e85b344a9ad010b782` and that
same tree. These are two source qualifications, each attempt 1; they are
**not** B01–B04, a controlled mitigation trial or new model-value acceptance.

Both original container ZIPs were downloaded, SHA-256 checked and ZIP-CRC
checked. Their source manifests were clean; their restored model containers
reported cgroup v2 `private`, stable container/process/cgroup identity,
stable visible quota **200000/100000 microseconds (2 CPU)** and memory limit
**3221225472 bytes** at both boundaries. All **12/12** resource counters and
**4/4** llama.cpp counters were observed, with no counter reset.

| Original measurement | PR preview `87da59dd` | Independent main `ea80f252` |
| --- | ---: | ---: |
| Full model gate, including probes | 79.382866 s | 54.662328 s |
| `Agent.run`, including transport and output validation | 75.396471 s | 50.784687 s |
| Diagnostic call, including business validation | 75.579379 s | 50.962546 s |
| Client model-slot wait | 0.000022 s | 0.000020 s |
| Resource probe wall, before / after | 0.150582 / 0.153035 s | 0.151713 / 0.179025 s |
| CPU usage delta | 151365779 microseconds | 102153195 microseconds |
| Cgroup periods / throttled periods | 764 / 754 | 518 / 507 |
| `throttled_usec` delta | 126651562 | 95537522 |
| Memory current, before / after (bytes) | 231108608 / 267706368 | 231374848 / 267476992 |
| All six `memory.events` counter deltas | 0 | 0 |
| Server prompt / generated token deltas | 714 / 119 | 722 / 109 |
| Server prompt / generation seconds | 41.3861 / 33.9822 | 29.5188 / 21.2348 |

A completed response was observed in both container cases, but both returned
an invalid diagnosis: `DiagnosticError`, escalation, `quality_passed=false`,
zero effect receipts, target revision zero and no curated/quarantine rows.
Both pairs of stacks were removed with no inspection error. The independent
frozen model evaluations remain a separate gate in [EVALUATION.md](EVALUATION.md).

The different token counts and independently initialized runners/stacks
are observed confounders. The shorter main duration is **not** a measured
optimization benefit. Cgroup throttling is now directly observed during
these intervals; its causal contribution to earlier timeouts or run-to-run
variability remains unproven. Zero endpoint memory-event deltas do not
establish absence of all memory pressure or a measured peak. No historical
failure, including the 90.003133-second timeout below, is superseded.

| Original container archive | Members | SHA-256 independently recalculated |
| --- | ---: | --- |
| [PR 14777472758](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/45082434901/artifacts/14777472758) | 162 | `db1e050bb9aa96a889e93710aa58a78cb72b44be614418780dee99c89994807d` |
| [Main 14778337823](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/45083502058/artifacts/14778337823) | 162 | `03cbb6fe657c55aa97e2808f0a603da33ff87b35feffda26fd541fa7f185e9ae` |

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

## Recorded stages and provenance

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

### Implemented resource probe and observed hosted qualification

`model-latency.json.model_container_resources` now retains two bounded
observations of the **exact active model container**. The qualifier resolves
one complete container ID from its own Compose project, verifies its
Docker `HostConfig.CgroupnsMode` is `private`, and uses that ID for
`docker exec`; it does not read the host's cgroup or mount its filesystem.
An empty/default or host namespace mode is unavailable, never assumed private.
The stdlib-only observation script reads cgroup **v2** `cpu.stat`, `cpu.max`,
`memory.current`, `memory.max` and `memory.events`. Cgroup v1, a non-private
namespace, inaccessible files and unsupported metrics remain explicitly
unavailable. No compatibility path is guessed.

CPU counters retain their original microsecond/count units. Quota and memory
limits distinguish the kernel's `max` value from a missing measurement.
Before/after deltas require the same container ID, kernel boot identity,
PID-1 start ticks and cgroup device/inode; a restart/replacement, missing
identity or decreased counter yields null deltas. `visible_limits_match`
separately flags changed or unverified visible quotas. Probe wall duration
and bounded error types are retained on either outcome; probe failures do
not suppress the original model/effect failure.
An incomplete counter, limit or lifetime observation marks the snapshot
partial; delta completeness is reported separately from lifetime verification.

These are container-wide observations, including collection overhead and
other work. Boundary memory readings do not measure peaks. The visible
CPU quota and bandwidth counters do not expose every ancestor's limits or
exclude host contention; see the [Linux cgroup v2 CPU interface](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html#cpu-interface-files).
No causal attribution, request-exclusive CPU duration or performance gain
follows from a nonzero throttling counter. The complete gate duration now
includes these extra probes; its historical values are not directly
comparable without that overhead.

This implements one prerequisite of the prospective trial. The source-bound
hosted observations above are separate from the local synthetic boundary tests;
neither launches B01–B04 or accepts model reliability/value. The model, prompt,
weights, 90-second budget, retries, CPU quota and authorization policy are
unchanged. New hosted evidence must retain its exact new source identity.

### Execution and reporting

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

**Still unverified:** a causal explanation of variable response times,
mitigation effectiveness, internal server queue time or transient queue peaks,
startup time specific to the model service, request-exclusive prefill and
token-generation durations, native structured-output validation alone, and whether
runner contention changes these stages. Process-wide server prompt/predict
counters are observed but are **not request-exclusive timing**.
The typed business-precondition validator has its own duration when reached
but does not cover the entire validation pipeline. A controlled,
prospectively specified and separately authorized investigation is required
before closing issue #16.
