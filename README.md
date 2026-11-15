# Governed DataOps Agents

**Collect evidence, authorize a bounded action, and verify the business state.**

This synthetic industrial incident-response platform uses MCP for narrow capabilities, PydanticAI for structured diagnosis, Temporal for durable orchestration, and actual transactional source/curated/quarantine rows. The operator console exposes observations, diagnosis, policy, signed approval, effects and fresh verification. A successful tool call alone cannot mark an incident resolved.

## Current delivery status — 15 November 2026

**The reference platform is qualified; full agent-value acceptance remains open.** Real hosted container, governance, restore and browser execution are now evidenced. The local model still fails the frozen quality/value gate. Publishing or merging the experimental implementation must not imply that it improves on the runbook.

| Gate | Current observation |
|---|---|
| Core unit/boundary suite | 232 tests passed in the hosted source profile |
| Real native governance profile | Eight requested checks passed, including MCP/Temporal business effects, recovery, paired restore and real browser console |
| Actual container platform | Ten checks passed at `cad9cc6eb28a70f24e9bf02774a7614cc4cb9631`, including five business scenarios, worker restart, paired restoration and real local-model response |
| Frozen ten-case comparison | Deterministic runbook 10/10; local agent 1/10 strict successes in the latest hosted evaluation |
| One-case container model quality | Failed: actual response observed, but wrong diagnosis was safely denied by policy |
| Added agent value | Not demonstrated; the original acceptance issue remains open |

[Qualification ledger and evidence](docs/QUALIFICATION.md) · [Successful container platform run](https://app.circleci.com/workflow/15f6d873-dc0d-4e83-8d20-d3abf1ec20c9) · [Open acceptance issue](https://github.com/mehdisafer/governed-dataops-agents/issues/1)

The earlier 14/18 native integration result, including 2/10 on its reserved evaluation, remains an immutable historical result in [evidence](evidence/qualification-f1e6e2f/). The later 1/10 evaluation is a separate execution, not a rewrite of that history. Neither demonstrates an advantage over the competent runbook.

## Business response and authority

| Incident | Governed action | Verified outcome |
|---|---|---|
| Freshness exceeded | Load the reviewed partition once | Resolved after row/watermark checks |
| Transient ingestion failure | Retry the bounded handler and reconcile uncertain writes | Resolved with one receipt/effect |
| Incompatible schema | Refuse automatic migration | Denied and escalated to engineering |
| Invalid quality batch | Separate signed approval, then quarantine | Contained, not falsely resolved |
| Duplicate delivery | Prove equivalence and suppress redelivery | Resolved without duplicate rows |

The model has no shell, SQL connection or write capability. Its diagnosis is a proposal. Deterministic policy and the target verify scope, environment, catalogue revision, state, approval and budgets. Changed plans or target revisions invalidate approval. SQLite WAL is a trusted single-host reference, not a general exactly-once guarantee for external systems or hostile-tenant isolation.

## Run the private reference

Requirements: Linux amd64, Python 3.12, uv 0.13.6, Docker Engine and Compose. The documented allowance is 12 GiB RAM, eight CPU threads and 15 GiB disk; this is not a throughput claim. The model uses a four-CPU limit in the qualified container profile.

```bash
uv sync --frozen --python 3.12.14
uv run dataops init
export DATAOPS_UID="$(id -u)"
export DATAOPS_GID="$(id -g)"
docker compose build
docker compose up -d --wait --wait-timeout 240
```

Open `http://127.0.0.1:8080` and use the local `.secrets/operator-token`. The runbook is the explicit baseline. A quality incident requires the distinct approver credential. Initialization refuses to overwrite credentials. Keep `.secrets/` private; never publish its tokens or private signing key.

Only the API publishes a host port, bound to loopback, and joins a separate ingress bridge. Model, Temporal, worker and target remain on the internal network without published ports. **The API can initiate egress; the entire stack is not air-gapped.** The API alone receives the private approval-signing key. Worker mounts are limited to public verification and reader/executor credentials.

Volume initialization assigns the selected non-root deployment UID. Explicit `nocopy` volume mounts prevent image copy-up from changing ownership during restoration. Model assets are immutable/readable by the non-root process, and the Temporal image defines its execution identity. These are tested deployment corrections, not a relaxation to world-writable files or root application execution.

## Reproduce checks and full integration

```bash
uv sync --frozen --python 3.12.14
uv run ruff check .
uv run pytest -q
uv run python scripts/export_contracts.py
git diff --exit-code -- contracts
```

For real native services, use a clean source and a new output directory:

```bash
uv run python scripts/bootstrap_runtime.py --destination var/runtime
uv run playwright install --with-deps chromium
uv run python scripts/qualify.py --manifest var/runtime/provisioning.json \
  --output evidence/runs/new-governance --profile governance \
  --source-commit "$(git rev-parse HEAD)"
uv run python scripts/qualify.py --manifest var/runtime/provisioning.json \
  --output evidence/runs/new-evaluation --profile evaluation \
  --source-commit "$(git rev-parse HEAD)"
```

The governance profile deliberately uses the runbook and does not claim inference quality. Evaluation compares both engines on the frozen corpus and fails when its criteria are unmet. A new output directory is required; failed results are not overwritten.

For the complete actual container reference:

```bash
uv run python scripts/qualify_container.py \
  --source-commit "$(git rev-parse HEAD)" \
  --output evidence/runs/new-container --model-cpus 4
```

The container gate measures infrastructure, effects, restoration and receipt of a real model response. Its report separately records `diagnostic_quality_passed`; platform success does not imply that field is true. Use `--require-model-quality` to require the one-case quality check as well, but even that single case does not replace frozen comparative evaluation.

`.circleci/config.yml` remains the fast Smarter Testing suite. `.circleci/reference.yml` is a manually triggered native Linux VM container qualification. `.github/workflows/ci.yaml` retains the full source, governance, frozen model evaluation, container and infrastructure profiles. No hidden provider fallback or automatically weakened baseline is used.

## Model result, limitations and publication

The latest frozen ten-case run obtained one strict agent success versus ten for the runbook. Eight real responses were observed; absent/incorrect outcomes remain in the denominator. Policy prevented unsafe effects in the observed cases, but safe refusal is not correct diagnosis. The four-CPU container trial returned a response within the unchanged ninety-second budget and still diagnosed its freshness case incorrectly. The failed two-CPU timeout run is retained.

The pinned Qwen quantization is served locally by llama.cpp through an OpenAI-compatible protocol, not an external hosted model. Compute, energy and human effort are not measured as zero merely because provider charges are zero. General attack resistance, multi-host scale and production availability are not established by these small synthetic runs.

[Architecture](docs/ARCHITECTURE.md), [deployment](docs/DEPLOYMENT.md), [operations](docs/OPERATIONS.md), [evaluation](docs/EVALUATION.md), [security](docs/SECURITY.md), [third-party components](docs/THIRD_PARTY.md) and the [backlog](docs/BACKLOG.md) describe the system boundaries. The current [qualification ledger](docs/QUALIFICATION.md) supersedes old statements that container/browser execution was unavailable, without altering their dated evidence.

Original project source uses the maintainer-selected [Apache-2.0 licence](LICENSE); dependencies and weights retain their own terms. Public visibility and protections remain separate maintainer settings. PC-Mehdi was used with task-specific permission for CI control and artifact retention; application qualification ran on isolated CI workers with synthetic data. No client environment or paid external provider was used. Full V1 agent acceptance and a stable production release remain withheld while the quality/value criterion fails.
