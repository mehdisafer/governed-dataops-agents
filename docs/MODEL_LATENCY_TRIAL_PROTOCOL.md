# P05 / issue #16 — preregistered investigation of 2-CPU model latency

**Status: PROTOCOL ONLY — NOT EXECUTED, NOT APPROVED FOR RUNTIME SPEND.**
Prepared 17 November 2026 against public `main` source
`540bb25dd9ce1df0c779d9d0e5ef1be1fabb5790`.
This file fixes the initial design *before any new manual repetition*. It does not
authorize a CI rerun, a paid resource, a model/prompt change or a V1 PASS.
See [issue #16](https://github.com/mehdisafer/governed-dataops-agents/issues/16)
and the separate [model-value issue #20](https://github.com/mehdisafer/governed-dataops-agents/issues/20).

The status above refers to the prospective **B01–B04** matrix. The later
PR #25 and merged-source qualification records in [MODEL_LATENCY.md](MODEL_LATENCY.md)
are independent source qualifications, not retrospective substitutions for
any of those four predeclared trials.

## 1. Already-observed evidence is retrospective, not a trial in this design

| Source-bound run | Real container response gate | Distinct outcome |
| --- | --- | --- |
| [PR #21 / run 44161986053](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44161986053), tree `ce5653be` | **PASS 69.247 s**; 2 CPU; 4/4 cumulative server counters present | Platform passed; diagnostic quality false |
| [Merged main / run 44163668519](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44163668519), same tree | **FAIL 94.880 s**; 2 CPU; 4/4 counters present | Client `Agent.run` timed out at 90.003133 s; quality false |

The independently inspected original **main** artifact, linked and hashed
in [issue #16](https://github.com/mehdisafer/governed-dataops-agents/issues/16),
reports client diagnostic duration 90.256592 s, client semaphore wait
0.000023 s, process-wide server prompt **721 tokens / 72.4677 s** and
generation **65 tokens / 17.8181 s**. These counters are **not proven
request-exclusive**. They suggest substantial server-side processing time,
but do not prove whether CPU scheduling, prefill, contention, queuing,
initialization or other factors caused the timeout. The two endpoint queue
gauges were both zero; transient peaks remain unknown.

The independent mainline frozen model-evaluation run also **FAILED**:
8/10 strict agent cases and four verified resolutions, versus a competent
10/10 and six resolutions for the runbook. Quality, availability and
business effects must remain separately scored. Do not pool these results
with the earlier or proposed trials, and do not retroactively call them
pre-registered observations.

## 2. Required instrumentation and freeze — before B01

The real **restored** Docker Compose stack is the measurement target, not
the earlier stack removed before restoration. A qualifying observation must
retain the exact executable Git commit and tree, job/attempt identity, UTC
time, runner image/class, relevant image/container digests, GGUF digest,
llama.cpp `b12368` identity, config, model CPU quota and memory limit.
Do not introduce a secondary model or external provider.

Record, with original redacted files, the following bounded stages:

- Active-stack start-and-health wall time, and **model-only** readiness
  if independently instrumented. An existing all-service startup value
  must never be relabeled model-only startup.
- Admission HTTP, worker semaphore wait, full `Agent.run`, typed business
  validation when reached, workflow poll, and total container gate.
- Before/after `llama.cpp` process-wide prompt/prediction
  tokens/seconds and boundary processing/deferred gauges.
- Before/after model-container cgroup `cpu.stat` usage, periods,
  throttled periods, and throttled time; visible `cpu.max` quota and
  bounded memory/current/events when available. **The bounded cgroup-v2
  probe is implemented and has produced source-bound hosted observations.**
  Its exact-container/lifetime checks, unsupported-v1 behavior,
  quota visibility limits and separate qualification records are documented in
  [MODEL_LATENCY.md](MODEL_LATENCY.md#implemented-resource-probe-and-observed-hosted-qualification).
  Visible container limits are not proof of every ancestor's effective limit.
- Each probe's overhead, collection error type, stage and availability;
  immutable failure artifacts, service logs, final target state, effect
  ledger, durable workflow history and cleanup receipts.

Values not directly measured must be JSON `null` / **unknown**, not
zero. Counter resets, missing process identities, exporter changes and
non-finite values invalidate that specific delta. Cgroup throttling
correlation is not proof of causality. Process-wide inference counters
must not be subtracted from client wall time and called exclusive queue
latency. Only allowlisted numeric fields may enter public summaries;
never publish token strings, untrusted log content or secrets.

**Preflight veto:** do not start the repeated trial until the resource
probe has a source-qualified unit/security check, the source is frozen,
original evidence storage/retention is confirmed, and the operator has
separately authorized CI/runtime consumption. If any requirement is
unmet, the matrix remains **NOT EXECUTED**.

## 3. Fixed baseline matrix (not launched)

Four **separate** real hosted container qualifications are planned under
one identical frozen executable source, with the existing restored-stack
freshness agent probe, explicit **2 CPU**, original model digest, all
other service quotas unchanged and unaltered **90-second** diagnostic
deadline. No artificial warm-up request, retry, source change or
selective rerun between planned attempts. Each new hosted job starts
an independent isolated stack as in the existing qualifier.

| Trial ID | CPU | New independent qualification | Denominator |
| --- | ---: | --- | --- |
| B01 | 2 | Original full restored-stack scenario | 1/4 |
| B02 | 2 | Original full restored-stack scenario | 2/4 |
| B03 | 2 | Original full restored-stack scenario | 3/4 |
| B04 | 2 | Original full restored-stack scenario | 4/4 |

All four trials count even if they timeout, fail before the model,
return invalid JSON, produce a safe escalation, or cannot collect
metrics. Infrastructure failures are classified separately but remain
in the scheduled denominator; a replacement run would be a **new**
explicit protocol version, not a silent omission. Do not infer
independence from identical source trees alone: GitHub-hosted runner
contention, cache, image downloads and runtime initialization vary.

There is **no authorized 4-CPU arm**. Any comparison would require
an explicit new frozen protocol with symmetric workload design and
separate approval; it must not be smuggled into the baseline.

## 4. Analysis rules and vetoes

The analysis joins each original `run.json`, `commands.json`,
`model-latency.json`, `model-quality.json`, `checks.json`, cgroup
observations when available, service logs, business receipts and
`cleanup.json` by run and source. Publish the number **scheduled,
executed, responded, timed out, invalid, correctly diagnosed, safely
denied, verified resolved and with complete evidence**, including
unknown outcomes. Preserve SHA-256 identities and all failed attempts.

For these **four** samples, report individual durations and at most
descriptive median/range, plus response counts with the small
denominator. **Do not claim a statistically stable p95, production SLA,
failure probability or causal attribution.** Describe stage-level
correlations and confounders. A single successful retry is not
mitigation evidence. A completed response is not necessarily a correct
diagnosis. Safety requires observed target state/effects, not merely
an API status.

If any baseline run fails the 90-second response requirement, retain
the reliability failure. If all four pass, the history remains variable
and reliability is still **unproven**; four successes do not close #16.
If any observed effects or cleanup are unsafe/unknown, preserve that
separate blocker regardless of timing.

## 5. Subsequent mitigation and separate validation

Only after baseline readback, propose one bounded change at a time on
**development** fixtures. Examples to investigate, not to assume or
silently apply: CPU throttling, prompt-processing cost, container
readiness and queueing. Any changed prompt, model, compute quota,
concurrency or runtime must be clearly attributed to a new source
and cannot inherit earlier model-evaluation success. The original
90-second limit and independent approval/effect barriers remain.

An eventual post-mitigation repetition protocol must be frozen and
reviewed separately *before* using it, with success criteria and
uncertainty appropriate for its sample size. Close
[issue #16](https://github.com/mehdisafer/governed-dataops-agents/issues/16)
only once the unstable stage is established with source-correlated
evidence, a bounded mitigation is verified across repeated trials,
and observed failures remain reported. The independent V1 model-value
gate in [issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1)
remains **FAILED** until separately satisfied.
