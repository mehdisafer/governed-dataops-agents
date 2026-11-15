# Qualification ledger

Updated 15 November 2026. **Platform execution is qualified; full agent-value acceptance is withheld.** A green container workflow verifies its declared infrastructure/effect gates, not comparative diagnosis quality. The original [acceptance issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) remains open. No accepted stable V1 or production-readiness claim follows from the passing subset.

## Latest actual container qualification

Source: `cad9cc6eb28a70f24e9bf02774a7614cc4cb9631`.
Pipeline: `3cfa3d77-80dc-4d4f-a8b8-f8d0005f9b34`.
[Workflow](https://app.circleci.com/workflow/15f6d873-dc0d-4e83-8d20-d3abf1ec20c9).
Job: `e2a33e1e-cd66-4b3b-bd36-a5efeb5f8698`.

The native Linux VM `.circleci/reference.yml` built and ran the actual application, Temporal and pinned model images. Its ten checks passed. The recorded source files remained unchanged during execution; the credential scan passed and owned-stack cleanup was verified.

| Actual check | Observation |
|---|---|
| Network, identities, secrets and resource limits | Non-root/read-only services, exact role-secret mounts, realized loopback port and backend isolation checked |
| Installed runtime asset identity | Actual model digest/size and installed package/runtime versions verified |
| Freshness | Real target rows and watermark corrected exactly once |
| Transient write ambiguity | Original effect receipt reconciled before fresh business verification |
| Schema incompatibility | Migration refused; no unauthorized effect |
| Quality | Separately authorized quarantine, reported as containment |
| Duplicate delivery | One equivalent business result, without duplicate output |
| Worker restart | Queued durable work completed after restart |
| Paired application/Temporal restoration | Fresh volumes restored; business rows and workflow history equal; duplicate delivery still deduplicated; new incident completed |
| Real model response | Actual local response observed within the unchanged diagnostic budget; this check alone does not require correct diagnosis |

The final report explicitly contains:

```json
{
  "status": "passed",
  "gate": "container_execution",
  "diagnostic_quality_passed": false,
  "model_cpu_override": 4.0,
  "full_acceptance_claimed": false
}
```

The freshness model case proposed a schema migration even though the observed schema versions agreed. Policy denied that wrong proposal. There was a real response and safe enforcement, **not a correct diagnosis or demonstrated model value**. The container script's optional `--require-model-quality` would make that one-case quality failure fatal; the separate frozen comparison remains the stronger mandatory full-acceptance gate.

### Original artifact integrity

SHA-256 values computed from downloaded, unmodified artifacts:

| File under `container/` | SHA-256 |
|---|---|
| `checks.json` | `11f77acc18d775b5bdce7832dc250bbbbfcc020790801c7be9d8b9a58142a196` |
| `cleanup.json` | `e57c8d58ba3ae360554294c3d41c44b8bc7d768f9429bfd59fd2eee19be75e5d` |
| `model-quality.json` | `a4c512881cba680dd04064349dd85bfc113a62eb6449219f3e7042c3df9ab95c` |
| `run.json` | `7d364645d3074e4ff3842ad45b89b16dbc23672effce1a7cbd6c54a713efc907` |

The downloaded set includes 87 original artifacts: source/runtime identities, command logs, business receipts, model trace, before/after histories and cleanup observations. Runtime secrets stayed outside the publishable proof. CircleCI retention is finite; this versioned ledger does not fabricate replacement execution outputs.

## Latest hosted governance and frozen evaluation

Separate source `924dd24780b332b13f24a5394a725ad2c55888ba` executed in pipeline `2c9ce775-ea93-476c-b770-a28020d4d763`. The full source profile passed 232 tests and its static/security checks. The governance profile passed eight requested checks: actual governance integration; policy/clock/key negative cases; two-worker load/idempotence; ambiguous-write recovery; pending workflow after restart; paired restoration; real browser console; and durable checkpoint. Terraform/provider-schema and isolated local Docker infrastructure checks executed separately without a production apply.

Those governance gates deliberately exercise the deterministic runbook. They do not imply that an inference engine performed those business diagnoses. Subsequent container ownership/network corrections do not retroactively change this earlier source receipt.

The **frozen comparative evaluation failed**. Both engines attempted the reserved cases; incorrect/unavailable diagnoses remain in the original denominator:

| Metric | Runbook | Local agent |
|---|---:|---:|
| Reserved cases | 10 | 10 |
| Strict correct diagnosis/business outcomes | 10/10 | 1/10 |
| Actual model requests attempted | 0 | 10 |
| Actual model responses observed | Not applicable | 8 |
| Observed unauthorized/unsafe effects | 0 | 0 |
| Agent advantage | Baseline | Not demonstrated |

The hosted result is a separate run from the historical 2/10 agent result. It is not evidence of statistically established degradation, nor an opportunity to select only the better run. The corpus is small and within known families. Safe denial of a wrong diagnosis is an authority-control success, but still a diagnostic failure. Zero returned usage on missing responses is not zero compute. Compute, energy and human effort were not monetized.

The existing post-native harness correction separated baseline competence from the held-out comparison, resolving the formerly contradictory requirement that a perfect baseline must also be exceeded on the same ten cases. Strict superiority and exact paired denominators remain required. No prompt/model was retuned against these reserved outcomes during this CI work, no weaker baseline substituted, and parity is not redefined as added value. Any future value claim needs a prospectively specified evaluation and fresh reserved data; see [EVALUATION.md](EVALUATION.md).

## Deployment defects corrected and re-executed

- Manual CircleCI Actions runs may have no GitHub event file. Unknown scope now requests full qualification instead of crashing or suppressing runtime checks.
- Downloaded model files were private to the build user. Immutable assets now have explicit read permissions and a traversable directory; the non-root image build checks actual GGUF/license/provenance access.
- Temporal's runtime resource detector needed a valid execution identity. The image defines the non-root user and its environment rather than running the service as root.
- A configured host port on an internal-only network was not a realized reachable endpoint. Only the API now joins a separate ingress bridge; the exact realized loopback mapping and internal-only backend memberships are asserted.
- Fresh restore volumes could have ownership changed by image copy-up. Explicit `nocopy` mounts preserve the UID established by the scoped initialization service. The paired restore subsequently passed without world-writable permissions or a privileged application.
- The two-CPU model trial timed out and remains retained as failed. The final trial used the documented four-CPU allowance, with the same ninety-second model deadline. A real response was observed, but its quality still failed.

**Network consequence:** model, Temporal, worker and target have no published ports and remain on the internal network. Only API ingress is published to `127.0.0.1:8080`. The API can initiate egress; the whole stack is not air-gapped. There was no `0.0.0.0` host exposure or disabled browser sandbox added to obtain success.

## Historical evidence remains historical

The 14 November native integration at `f1e6e2f3800242ec210145680261da8ab60f38b4` returned nonzero with 14/18 checks. Its agent achieved 2/10 strict reserved successes versus 10/10 runbook; browser/socket and deployment prerequisites were blocked. The [192 original files](../evidence/qualification-f1e6e2f/full-originals.tar.gz), [run metadata](../evidence/qualification-f1e6e2f/run.json), [checks](../evidence/qualification-f1e6e2f/results.json), [comparison](../evidence/qualification-f1e6e2f/comparison.json), [load](../evidence/qualification-f1e6e2f/load.json) and [retained replay development evidence](../evidence/recovery-development/README.md) remain unchanged.

The prior 172-test source and later 232-test publication checks have separate sources. Original GitHub Actions run 43597256488 failed before runner assignment; its account-level cause remains unknown. These historical failures are not relabeled as passing. The new actual CircleCI browser/container results supersede the current execution gaps, not the historical records.

Replay acceptance concerns the concrete observed histories and unchanged workflow commands, not arbitrary future migrations. Single-host SQLite, limited admission and bounded workload results do not prove multi-host partitioning, hostile-tenant isolation or exactly-once behavior for arbitrary external APIs.

## Acceptance decision and remaining work

The reference's implemented governance, business effects, operator console, runtime packaging, restart and paired restoration now have passing execution evidence. **The project's central agent-quality/value criterion still fails and blocks full V1 acceptance.** A platform release may be documented as experimental; it must not claim that the model is superior to the runbook.

A stable full acceptance requires a defensible prospective model/value result, plus explicit target-specific operational acceptance for any production deployment. Public visibility and protections are separate maintainer choices. Original project code has the selected Apache-2.0 licence; dependency/weight rights remain separate. Earlier wording that the project licence was undecided applies only to the original pre-selection history.

The [backlog](BACKLOG.md), [publication instructions](PUBLICATION.md), [security](SECURITY.md) and [third-party inventory](THIRD_PARTY.md) remain relevant. Read this ledger as the current state wherever a dated historical document says browser or container execution was unavailable. No paid plan, real client system, external inference provider or production environment was modified by this work.
