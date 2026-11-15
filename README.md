# Governed DataOps Agents

An incident-response console for a synthetic industrial data platform. It collects evidence, proposes a typed action, checks deterministic policy, obtains a bound approval when needed, executes through a durable workflow, and rereads the business state before reporting an outcome.

I built this project to make agent decisions inspectable. The console shows the incident, observations, diagnosis, proposed action, permission decision, approval and correlated execution trace. The target holds actual source, curated and quarantine rows. A successful tool response alone cannot close an incident as resolved.

**Current status (15 November 2026): CircleCI unit checks on `main`, real hosted governance/browser and a corrected Docker-container execution profile have successful reported checks on their named commits; full agent-quality and value acceptance remains open.** The historical 14 November native run passed 14/18 checks (agent 2/10 versus runbook 10/10). The separate 15 November hosted frozen evaluation yielded agent **1/10** versus runbook **10/10**. At `cad9cc6`, real container execution passed ten declared platform gates, but the local model's one-case diagnosis was incorrect and safely refused by policy. No model advantage, production-readiness or multi-host partitioning is claimed. [Issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) remains open.

## Latest hosted execution — 15 November 2026

These are separate executions, linked to their actual source commits. They do not rewrite the earlier native qualification or establish an accepted stable release.

| Gate | Evidence | Limit |
|---|---|---|
| CircleCI unit and lint on `main` | [`2460012` `build-and-test` success](https://app.circleci.com/workflow/9f31433c-2712-467c-89be-34ad2c3285c8/job/9d5fd2e8-3c67-4a35-861c-6feb9a735ea7) | Unit workflow, not container or model evaluation |
| Hosted governance and browser | [`924dd24` source/governance checks succeeded](https://github.com/mehdisafer/governed-dataops-agents/commit/924dd24780b332b13f24a5394a725ad2c55888ba) | Runbook-governed single-host reference, not agent advantage |
| Actual model, Temporal and Docker reference | [`cad9cc6` container workflow succeeded](https://app.circleci.com/workflow/15f6d873-dc0d-4e83-8d20-d3abf1ec20c9) | Ten platform gates; model diagnosis incorrect |
| Frozen hosted model comparison | [`924dd24` model-evaluation failed](https://github.com/mehdisafer/governed-dataops-agents/commit/924dd24780b332b13f24a5394a725ad2c55888ba) | Agent 1/10 versus runbook 10/10 |
| GitHub Actions | [Main run 43769325453 failed before runner allocation](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43769325453) | No steps executed, underlying cause unknown |

A wrong model proposal rejected by independent policy is a governance success, not a correct diagnosis. See the [complete qualification ledger](docs/QUALIFICATION.md) and [CI provenance](docs/CI.md) for source-specific evidence and limitations.

## Historical native results — 14 November 2026

These results describe the clean, unchanged application source at [`f1e6e2f`](https://github.com/mehdisafer/governed-dataops-agents/commit/f1e6e2f3800242ec210145680261da8ab60f38b4), executed on 2026-11-14. Later qualification-harness and evidence-verifier corrections have separate regression checks; they do not rewrite this native result.

| Area | Observed result | Limit |
| --- | --- | --- |
| Business paths | All five runbook cases matched the expected row-based outcome | A containment or refusal is not a resolution |
| Governance and recovery | Tampered/stale/expired approval refusal, worker restart, model outage, contention and admission recovery exercised | Trusted single-host application processes and synthetic targets |
| Persistence | Paired application/Temporal restore executed; 56 closed current histories and 26 earlier development histories replayed | Earlier development source was dirty; replay covered a query-only workflow change |
| Frozen comparison | Runbook 10/10; agent 2/10; all twenty final business states observed | Two accepted model proposals were correct; eight absent responses failed the operational criterion |
| Bounded load | Twelve runbook incidents, concurrency four, p95 6.150 s, zero errors | This does not measure model throughput or multi-host scalability |
| Deployment and console on that original native host | Container, Terraform and rendered browser execution could not complete in the original environment | Later hosted results above supersede those environmental gaps only for their separate tested scopes |

The [qualification ledger](docs/QUALIFICATION.md) explains each result, the [evaluation report](docs/EVALUATION.md) preserves denominators and usage uncertainty, and the [evidence index](evidence/README.md) links the original artifacts. The [prioritized backlog](docs/BACKLOG.md) records the remaining work without changing the acceptance criteria.

## What the system does

| Incident | Observed business state | Governed response | Expected outcome |
|---|---|---|---|
| Freshness objective exceeded | Pending valid rows and an overdue freshness watermark | Load the reviewed partition once | Resolved after fresh row and watermark checks |
| Transient ingestion failure | Failed batch with a recorded transient interruption | Retry the fixed batch handler once | Resolved; lost responses reconcile against the receipt |
| Incompatible schema | Source schema differs from the accepted version | Refuse automated schema migration | Denied and referred to engineering |
| Rejected quality batch | Invalid source row in a rejected batch | Require separate approval, then quarantine the batch | Contained; source quality still requires repair |
| Duplicate delivery risk | The batch is already present in curated data but delivery remains pending | Prove row equivalence, then suppress redelivery | Resolved without inserting duplicate rows |

The model has no shell, SQL connection or write tool. Its category and action are proposals. The policy and target independently verify scope, environment, catalogue version, revision, preconditions and budgets. A changed plan or changed state invalidates an approval.

## Architecture

```mermaid
flowchart TD
    O["Operator console / API"] --> T["Temporal workflow"]
    T --> C["MCP evidence collection"]
    C --> D["PydanticAI diagnosis"]
    D --> P["Typed plan and deterministic policy"]
    P -->|Approval required| A["Signed approver decision"]
    A --> P
    P -->|Authorized| E["MCP effect gateway"]
    P -->|Denied| X["Escalation and trace"]
    E --> S["Transactional target and receipt"]
    S --> V["Fresh business verification"]
    V --> O
```

Temporal owns durable ordering, signals, timeouts and retries. MCP is the narrow capability transport. PydanticAI calls the configured model and validates its structured response. SQLite WAL stores the single-host synthetic business state, approvals, observations and effect receipts. The model is local llama.cpp serving a pinned community Qwen quantization through an OpenAI-compatible protocol; it is not an OpenAI-hosted deployment.

See [architecture and decisions](docs/ARCHITECTURE.md), [SDK compatibility](docs/COMPATIBILITY.md), the [versioned catalogue](src/governed_dataops/catalogue-v1.json) and [JSON contracts](contracts/v1).

## Start the private console

The reference profile is Linux amd64, Python 3.12, uv 0.13.6, Docker Engine and Docker Compose. Allow 12 GiB RAM, eight CPU threads and 15 GiB disk for the full demonstration. These are deployment allowances, not measured throughput claims.

The reference container was subsequently exercised in an isolated hosted Linux VM at `cad9cc6`; its ten platform checks passed while the diagnostic quality check failed. The commands below are reproducible starting steps for an authorized host, not a production deployment certificate. Follow the [deployment guide](docs/DEPLOYMENT.md) for evidence and resource limits.

```bash
uv sync --frozen
uv run dataops init
export DATAOPS_UID="$(id -u)"
export DATAOPS_GID="$(id -g)"
docker compose build
docker compose up -d --wait --wait-timeout 240
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080). Enter the value from your local `.secrets/operator-token` file. Select an incident class and a diagnostic engine. The deterministic runbook is the explicit baseline; the local model remains experimental. A quality incident requires the separate `.secrets/approver-token` credential before quarantine. The console clears credential inputs and keeps credentials only in the current tab's memory.

Initialization refuses to overwrite existing credentials. Only the API port is published, on loopback. Worker, target, model and Temporal use an internal network. The signing private key is mounted only into the API; the worker receives public verification material and reader/executor credentials. Follow the full [deployment instructions](docs/DEPLOYMENT.md) for permissions, secrets, resource limits, optional Terraform ownership and cleanup.

### API example

This creates an isolated synthetic target and submits a runbook incident. The response contains the stable incident and workflow identifiers.

```bash
uv run python - <<'PY'
from pathlib import Path
import httpx

token = Path('.secrets/operator-token').read_text().strip()
response = httpx.post(
    'http://127.0.0.1:8080/api/demo/incidents',
    headers={'Authorization': f'Bearer {token}'},
    json={'scenario': 'transient', 'mode': 'runbook', 'simulate_lost_response': True},
    timeout=30,
)
response.raise_for_status()
print(response.json())
PY
```

`POST /api/incidents` accepts an explicit versioned incident and an execution mode. Incident content and execution intent are admitted in one transaction. Duplicate event submissions reuse the durable workflow ID; rebinding an event to different content or mode is rejected. `GET /api/incidents/{id}` exposes the scoped trace. `POST /api/incidents/{id}/approval` requires the reviewed plan fingerprint and an approver credential. `POST /api/incidents/{id}/cancel` requests cancellation without promising rollback of an already dispatched effect. The runtime exposes its OpenAPI contract at `/openapi.json`.

## Reproduce the evidence

Fast checks use real SQLite and cryptography. Tests that use fake Temporal/provider boundaries label that scope; they do not establish service integration.

```bash
uv sync --frozen
uv run ruff check .
uv run pytest -q
uv run python scripts/export_contracts.py
git diff --exit-code -- contracts
```

For native real-service qualification, download the pinned runtime assets and run the supervisor from a clean source commit:

```bash
python scripts/bootstrap_runtime.py --destination var/runtime
uv run playwright install chromium
uv run python scripts/qualify.py \
  --manifest var/runtime/provisioning.json \
  --output evidence/runs/local-integration \
  --profile integration \
  --source-commit "$(git rev-parse HEAD)"
```

The supervisor runs communicating services and clients in one network namespace. It generates temporary role credentials outside the evidence directory, records the source/input/runtime identities, executes the scenarios, retains original histories and traces, and shuts down its processes. It refuses to overwrite an existing result directory. Any failed requested gate results in a nonzero exit; independent checks continue so a model failure does not hide a recovery failure.

Profiles are `smoke`, `integration`, `governance`, `evaluation` and `load`. `governance` exercises the platform with the explicitly selected runbook and does not start a model. `evaluation` runs the frozen held-out corpus in both modes. `load --count 12 --concurrency 4` measures bounded runbook throughput, not model scalability. Exact thresholds, denominators and limitations are described in [EVALUATION.md](docs/EVALUATION.md).

For isolated real-container qualification against a clean source commit:

```bash
uv run python scripts/qualify_container.py \
  --source-commit "$(git rev-parse HEAD)" \
  --output evidence/runs/container-current --model-cpus 4
```

The container platform gate separately records `diagnostic_quality_passed`. A real model response can be incorrect even when the container execution succeeds. Always use a fresh output directory and preserve unsuccessful original records.

## Operations and limitations

- [CI provenance](docs/CI.md): CircleCI unit execution, separate manual container qualification and GitHub Actions limitations.
- [Operations](docs/OPERATIONS.md): readiness, metrics, actionable alerts, bounded queues, recovery, paired backup/restore, migration and rollback.
- [Security](docs/SECURITY.md): role boundaries, signed approvals, injection assumptions, scan coverage and disclosure.
- [Third-party components](docs/THIRD_PARTY.md): pinned provenance, inventories and unresolved licence decisions.
- [Evidence](evidence/README.md): retained original results and their scope.
- [Delivery plan](docs/PLAN.md): implementation milestones, acceptance status and reconstruction history.
- [Backlog](docs/BACKLOG.md): model/runtime investigation, evaluation design and remaining deployment gates.

This is a private single-host demonstration over synthetic data. The Temporal development server, shared SQLite volume and trusted application processes do not provide hostile-tenant isolation or an HA production deployment. The local model can be wrong even when its JSON and citations are valid. Atomic effect/receipt behavior is specific to the provided target; it is not a generic exactly-once guarantee for external APIs. A paired backup is only considered exercised when a restore is executed and its business state checked.

The maintainer has explicitly selected the [Apache License, Version 2.0](LICENSE) for this repository's original source. The repository remains private until the owner completes the separate visibility and publication review steps. Third-party software and weights retain their own licences. The reproducible incident fixtures use synthetic data; the reference does not require access to a personal workstation, a client environment or an external paid inference provider.
