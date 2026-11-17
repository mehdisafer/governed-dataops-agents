# Prospective evaluation V2 — feasibility gate and preregistration proposal

**Status: DRAFT PROTOCOL, NOT A FROZEN DATASET OR AN ACCEPTANCE RESULT.**
Prepared on 17 November 2026 from public source at 540bb25dd9ce1df0c779d9d0e5ef1be1fabb5790. Related issues:
[#20](https://github.com/mehdisafer/governed-dataops-agents/issues/20) (false migrations and prospective V2),
[#16](https://github.com/mehdisafer/governed-dataops-agents/issues/16) (2-CPU latency),
and [#1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) (V1 acceptance).
This document does not authorize a provider call, CI rerun, paid resource, model/prompt/policy change, release or deployment.

## 1. Why a feasibility decision must precede model tuning

The executable V1 reference provides **one trusted typed Snapshot**, untrusted incident/log text,
a finite Scenario/ToolName catalogue, the independent [diagnosis validator](../src/governed_dataops/diagnostic.py),
and the [policy evaluator](../src/governed_dataops/policy.py). The current
[diagnosis-v3 prompt](../src/governed_dataops/prompts/diagnosis-v3.txt)
requests essentially the same ordered observable conditions as the
deterministic [runbook_diagnose](../src/governed_dataops/diagnostic.py).
The two implementations are **not proven equivalent for every possible Snapshot**;
their predicates and error handling must be checked separately before any
"better than baseline" claim.

On the original ten inspected heldout cases the runbook was already **10/10**.
A strictly greater *number* of correct cases on these same ten is mathematically
impossible. Historical model runs were not all equal: an original
[source-qualified mainline](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43992090061)
measured **6/10 versus 10/10**; the distinct later
[mainline run](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/44163668519)
recorded **8/10 versus 10/10**, with a separate 90-second container response timeout.
Those are failed, independent observations, not evidence of improvement.

A model may generate explanations, but the existing policy can only authorize
actions for typed business preconditions. Unsupported proposals must remain
rejected; untrusted logs are never authorization. A synthetic case designed to
make a competent runbook artificially lose is **not** evidence of model value.

### Mandatory feasibility veto — before manufacturing a V2 holdout

For every proposed new incident family, write down all of the following **before**
tuning or running inference:

| Test | Evidence required | If it cannot be shown |
| --- | --- | --- |
| Additional information | Identify an independently verifiable, authorized signal or task that the current runbook does not already handle correctly | Do not claim operational added value |
| Legitimate decision | Exhibit a safe model-favored decision supported by trusted evidence and the unchanged policy/catalogue, not by log instructions | Exclude the claimed resolution; permit safe abstention only |
| Fair comparator | Show the competent unchanged runbook's complete behavior on the **same** observations, permissions and clock | Do not downgrade or sabotage the comparator |
| Verifiable benefit | Predefine a result beyond a nicer explanation: e.g. a separately authorized, objectively verifiable additional resolution under the same conditions | Treat explanation quality as a separate product question, not V1 effect success |
| Blind adjudication | Specify a truth source independent of either model/runbook output, with a predeclared rubric | Do not label a case as an unseen quantitative acceptance case |

**Veto rule:** if no feasible additional authorized outcome can be demonstrated,
do not execute an expensive V2 superiority benchmark under the existing
contracts. Record the architectural limitation and request a *separate product
decision* on revised scope and acceptance; do not silently alter the baseline,
effect policy, catalogue or original V1 criterion. This veto is a proposed
engineering gate, not a claim that impossibility has been formally proved for
every conceivable input.

## 2. Prospective cohort specification — only after the feasibility veto passes

Prepare an independently authored, wholly synthetic source-disjoint
development set and an unused evaluation holdout. A candidate starting design
is **at least 20 development cases and 30 heldout cases**. These counts are
a planning proposal, **not** created fixtures, a power calculation or a final
acceptance denominator. Final counts, class mix and statistical acceptance
thresholds must be committed before the first holdout run.

The frozen protocol manifest must enumerate:

- Versioned case IDs, authoring method, data provenance, generation source SHA,
  deterministic generator seed (if any), and content SHA-256 for every fixture;
  synthetic identity and target scope, without real secrets or client data.
- Independently adjudicated expected category, action, effect, final business
  snapshot and admissibility; distinguish **resolved**, **contained**,
  **safely escalated**, **denied**, **timeout**, **invalid response** and
  **unknown/unobserved**. Missing outcomes never disappear from denominators.
- Separate source-disjoint families covering typed-schema equality/mismatch,
  freshness, transient failures, rejected batches, duplicate redelivery,
  policy denials, incomplete evidence, and any genuinely *new* authorized
  added-value family justified by Section 1.
- Paired counterfactuals in which the trusted Snapshot and permitted actions
  stay fixed but the untrusted log changes: benign wording, forged schema
  migration, claimed elevated permission, misleading user symptom and
  irrelevant log noise. Other pairs may vary **one trusted input at a time**,
  with independently changed truth.
- Explicit development/holdout separation, freeze timestamp and Git tree/hash,
  reviewer identity or role, permitted development feedback and a rule
  forbidding prompt, model, comparator or threshold edits after holdout exposure.

Any prior inspected V1 case is **historical analysis only**, not newly unseen
V2 evidence. Dataset-generation independence and semantic novelty must be
reviewed; a different random seed by itself is insufficient.

## 3. Exact paired execution protocol

Before execution, commit a *machine-readable* finalized protocol containing
all case IDs and hashes, model GGUF digest, llama.cpp binary identity,
prompt/native-schema SHA-256, settings, runbook source SHA, policy/catalogue
versions, 2-CPU quota, 90-second diagnostic budget and the intended number
of attempts. Keep the current no-model-tools/no-provider-fallback policy.
Measure paired runbook and model on **the same immutable pre-admission evidence**;
avoid cross-arm target mutation by isolating/restoring state between attempts.

- Predeclare execution order and how warm/cold starts are balanced; retain
  source SHA, workflow/job run IDs, fixture version, immutable trial ID and
  exact timestamps for every attempt.
- Retain original redacted requests, responses, validator decisions, approvals,
  effect receipts, final snapshots, failure types, latency traces and cleanup
  receipts in separately versioned immutable artifacts. Do not overwrite the
  original or a failed partial run.
- Count request non-response, timeout and invalid structured output as model
  failures within the original scheduled denominator. A safe escalation is
  valuable **safety evidence**, never a verified remediation success.
- Measure completion, category/action correctness, verified resolution,
  containment, safety, abstention precision, wall and internal stage timings,
  p50/p95 where sample size permits, and uncertainty. The server's process-wide
  token/time deltas cannot be equated to request-exclusive inference time;
  boundary queue gauges do not reveal transient peaks.
- Retain every failed iteration; no silent selective retry, case exclusion,
  deadline extension, CPU upgrade or external/paid provider substitution.

## 4. Separate gates — no synthetic all-green shortcut

| Gate | Pass condition to preregister | Current state |
| --- | --- | --- |
| **Feasibility** | A documented legitimate additional task/outcome survives the veto in Section 1 | NOT DEMONSTRATED |
| **Integrity** | Every scheduled case and original trace is accounted for with valid provenance/hash and complete, independently observed business outcome | NOT EXECUTED |
| **Safety** | Zero unauthorized/unknown effects, no unreviewed evidence citation or cross-scope action, and unchanged trusted policy/approval barriers | NOT EXECUTED |
| **Comparative quality** | A prospectively defined non-inferiority criterion against the capable unchanged runbook on cases it already solves, with timeouts in denominator | NOT DEFINED/TESTED |
| **Added value** | A separately defined, objectively scored additional result on a legitimate new condition relative to the same competent runbook; predefine minimum effect and uncertainty requirement before seeing holdout | NOT DEFINED/TESTED |
| **Reliability** | A preregistered completion/latency objective at existing 2-CPU/90-second constraints, including all failures and repeated-run uncertainty | NOT TESTED |

Do **not** set permissive thresholds after looking at V2 responses. The current
historical 10/10 runbook benchmark remains a perfect reference on its own ten
cases, not an artificially lowered baseline. If the only observable improvement
is explanation preference or human triage assistance, evaluate that with a
separate blinded human protocol and a **new, explicitly approved** product
acceptance criterion; it does not prove autonomous remediation advantage.

## 5. Ordered next decisions and evidence

1. Review the complete [diagnostic](../src/governed_dataops/diagnostic.py),
   [policy](../src/governed_dataops/policy.py) and
   [contract](../src/governed_dataops/contracts.py) code to classify all
   **policy-authorized effect types** and where a capable runbook could abstain.
   The present documentation is a scoped preliminary analysis, not exhaustive
   model-checking or a proof of impossibility.
2. Decide and document whether a genuinely additional *authorized* model task
   exists without changing frozen permissions. If no: fail the feasibility
   gate, stop prospective runtime spend and keep [#1](https://github.com/mehdisafer/governed-dataops-agents/issues/1)
   open pending an explicit product decision.
3. If yes: approve and freeze a V2 protocol/manifest **before** any prompt,
   parameter or model adaptation; generate development and holdout independently.
4. Inspect development perturbations, qualify changes only there, then perform
   one source-bound unseen holdout execution with all scheduled trials counted.
5. Publish an auditable comparison and independently inspect artifacts; close
   [#20](https://github.com/mehdisafer/governed-dataops-agents/issues/20) only
   for evidenced criteria, and keep the unrelated latency [#16](https://github.com/mehdisafer/governed-dataops-agents/issues/16)
   open until it has a demonstrated mitigation and repeated-run validation.

**Non-changes in this proposal:** no model/prompt/schema changes, comparator
downgrade, policy relaxation, real provider calls, CI reruns, hidden failures,
release/tag or V1 acceptance claim.
