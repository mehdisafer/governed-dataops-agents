# Private single-host deployment

## Reference profile

The reference configuration targets a private Linux amd64 host running Docker Engine and Docker Compose. It contains one synthetic target, one application SQLite database, one persistent Temporal development server and one local CPU model. Temporal is the workflow authority. SQLite WAL coordinates transactions on a local filesystem; network filesystems and multiple hosts are outside this profile.

Use a non-root deployment account. Allow 8 CPU threads, 12 GiB RAM and at least 15 GiB free disk for images, downloads, state and evidence. These are provisioning allowances, not measured throughput guarantees. Record the actual execution environment with every qualification run.

**Validation boundary:** download verification, native execution, container build, container execution and Terraform validation are separate gates. `docker compose config` checks structure; it does not build or start an image. The reference container deployment remains unverified. This is a single-host demonstration with no HA or production acceptance. The [Temporal CLI development server](https://docs.temporal.io/cli/server#start-dev) is intended for development.

## Observed qualification status

The retained qualification on **2026-11-14** used clean, unchanged source commit `f1e6e2f3800242ec210145680261da8ab60f38b4`. Its native integration run passed **14 of 18 gates** and finished with overall status **failed**. The failed gates cover the five agent business cases, heldout agent evaluation, demonstrated agent advantage and the browser console. The supervisor stopped its direct child services at the end. These results describe an executed test, not a service left running. See the [native qualification evidence](../evidence/qualification-f1e6e2f/).

| Area | Observed result | Remaining boundary |
| --- | --- | --- |
| Native governance and recovery | Runbook business cases, approval checks, worker outage/restart, contention, admission recovery, model outage handling and paired database restore passed | Bounded synthetic single-host exercises; no availability or multi-host guarantee |
| Native history replay | 56 closed workflow histories from the frozen run and 26 from an earlier development revision replayed | The earlier source was dirty; this is concrete history compatibility evidence, not a clean release-to-release upgrade certification |
| Native runbook load | 12 incidents, concurrency 4, p95 6.150 seconds, zero errors | Runbook measurement only; no model throughput or service-level guarantee |
| Agent quality | 2/10 strict heldout successes, versus 10/10 for the runbook; agent advantage was not established | Diagnostic quality acceptance failed; retain failed and timed-out attempts in the denominator |
| Containers | The [frozen-commit attempt](../evidence/containers-f1e6e2f/) stopped because Docker was unavailable | No image build, container startup, isolation check or container restore executed |
| Terraform | [Version, formatting and readonly initialization](../evidence/infrastructure-f1e6e2f/) succeeded; validation failed while loading the provider schema | No Docker resource plan or Terraform apply executed |
| Browser console | Chromium launch failed with `socket() failed: Operation not permitted` in the [native results](../evidence/qualification-f1e6e2f/) | Browser interaction and visual verification remain unexecuted because of the local Unix-domain socket restriction |
| GitHub Actions | [Run 43597256488](../evidence/github-actions-43597256488/) failed on both attempts before runner assignment, with zero executed steps | The available evidence does not establish the cause; neither attempt supplies CI qualification results |

End-to-end heldout agent latency was median **91.425 seconds** and p95 **210.917 seconds**. The run also recorded delayed workflow completion, worker heartbeat timeouts and RPC errors. Their cause remains unestablished. The configured 90-second model-call deadline is not an end-to-end incident deadline. Diagnose those timing layers before changing budgets or attributing the delay to a particular component. Detailed model results and scope are in [evaluation](EVALUATION.md) and the [retained comparison and logs](../evidence/qualification-f1e6e2f/).

## Versions and provenance

| Component | Pin and verification |
| --- | --- |
| Python image | `3.12.14-slim-trixie`, OCI manifest digest pinned in every Dockerfile |
| uv build tool | `0.13.6`, OCI manifest digest pinned in the application Dockerfile |
| Python packages | Exact direct versions and distribution hashes in `uv.lock`; build uses `uv sync --frozen --no-dev --no-editable` |
| Temporal | CLI `1.10.1`, embedded server `1.32.2`; release archive SHA-256 checked |
| Local inference | llama.cpp `b12368`, commit `9daa0aa22`; CPU archive SHA-256 checked |
| Model | Exact weight revision, size, licence and SHA-256 in `scripts/bootstrap_runtime.py` |
| Compose validation tool | Official Compose `5.7.1` |
| Optional Terraform | Terraform `1.17.2`, `kreuzwerker/docker` `4.7.0`, generated provider lock file |

The model image installs Debian runtime libraries from the fixed [2026-11-13 snapshot](https://snapshot.debian.org/archive/debian/20261113T000000Z/dists/trixie/Release). Package-signature verification remains enabled; only the historical release-expiry check is disabled. Record the resolved package inventory and final image digest during the build. Pinned inputs do not establish successful execution.

Temporal and llama.cpp retain the licences included in their archives. The model image retains its Apache-2.0 licence at `/models/LICENSE`. Optional [Terraform is distributed under BUSL-1.1](https://github.com/hashicorp/terraform/blob/v1.17.2/LICENSE), and the [Docker provider uses MPL-2.0](https://github.com/kreuzwerker/terraform-provider-docker/blob/v4.7.0/LICENSE). These component licences do not select a licence for this repository.

### Experimental model profile

The model is **Qwen3-4B-Instruct-2507, Q2_K**, a community quantization published by Unsloth. The official Qwen base model and the community GGUF have separate pinned revisions. The image keeps both source cards and the asset manifest alongside the licence. The community file is not described as an official Qwen GGUF release.

| Asset | Exact identity |
| --- | --- |
| Official base model | `Qwen/Qwen3-4B-Instruct-2507` at `cdbee75f17c01a7cc42f958dc650907174af0554` |
| Community GGUF | `unsloth/Qwen3-4B-Instruct-2507-GGUF` at `a06e946bb6b655725eafa393f4a9745d460374c9` |
| Weight file | `Qwen3-4B-Instruct-2507-Q2_K.gguf`, 1,669,500,000 bytes |
| SHA-256 | `f7ed2f57713ad29e1a4ec093be0cdf3d7fd31e137e8fd4fc3edcfd04a5267862` |

The CPU profile uses four inference threads, one slot, a 2,048-token context, `q8_0` KV cache, flash attention, batch size 128 and microbatch size 64. Weight repacking, host prompt cache and context checkpoints are disabled to bound extra host buffers. Each diagnostic run has one overall 90-second deadline, at most two provider requests and a 300-token output cap per request. Changing those bounds needs fresh latency and memory evidence.

The selected asset is an **experimental diagnostic candidate whose current quality gate failed**. A correct checksum establishes the selected bytes. It does not establish diagnostic accuracy, prompt-injection resistance or value over the deterministic runbook. Record invalid diagnoses, timeouts and process exits alongside successful responses. Historical results whose raw evidence was lost are contextual notes, not retained acceptance proof. See [evaluation](EVALUATION.md), [qualification](QUALIFICATION.md) and the [frozen-commit comparison](../evidence/qualification-f1e6e2f/) for current results.

## Install and start

From a clean checkout with Python 3.12 and uv 0.13.6 installed:

```bash
uv sync --frozen
uv run dataops init
export DATAOPS_UID="$(id -u)"
export DATAOPS_GID="$(id -g)"
test "$DATAOPS_UID" -ne 0
docker compose config --quiet
docker compose build
docker compose up -d --wait --wait-timeout 180
docker compose ps
```

`dataops init` refuses to overwrite existing configuration. It creates `.env`, separate role-token files and an Ed25519 approval key pair under `.secrets/`. Keep these files outside Git and outside the build context. Enter the appropriate local operator or approver token in the console; initialization must not print tokens.

Open `http://127.0.0.1:8080`. The API is the only published port. The target, model, Temporal gRPC service and metrics stay on an internal Docker network without an external runtime route. There is no paid provider fallback. Image construction needs network access to retrieve verified artifacts and dependencies.

The `init-state` container only initializes volume ownership, then exits. Long-running services use the configured non-root UID/GID, a read-only root filesystem, temporary `/tmp`, dropped capabilities, process/memory limits and a 45-second stop grace period. Do not set `DATAOPS_UID=0`.

Compose file-based secrets are bind mounts whose host ownership is retained. Set the container UID/GID to the owner of `.secrets/`, as above. This profile assumes a conventional Linux Docker Engine; rootless UID mapping and Windows containers need separate validation. See [Docker's secret model](https://docs.docker.com/compose/how-tos/use-secrets/) and [service secret attributes](https://docs.docker.com/reference/compose-file/services/#secrets).

## Credentials and approval authority

| Service | Role credentials | Approval key access |
| --- | --- | --- |
| API | Operator, approver, reader | Private signing key and public verification key |
| Worker | Reader, executor | Public verification key only |
| Target | Operator for synthetic seeding, reader, executor | Public verification key only |
| Model, Temporal, volume initializer | None | None |

There is no blanket `env_file` on the worker. Application containers receive explicit `_TOKEN_FILE` paths, and only the API mounts the private signing key. The worker must pass an explicitly restricted environment to its MCP subprocess. Neither the model nor Temporal receives application credentials.

API, worker and target share one writable application database. They are trusted processes, not mutually hostile tenants. Signed approvals prevent an executor from inventing a valid envelope. This topology does not defend against a compromised Docker host, an administrator reading secret files, or arbitrary database modification by trusted process code. Separate persistence authorities, service identities and an independently managed approval authority would be needed for a stronger deployment boundary.

## Container qualification gate

The [attempt against `f1e6e2f`](../evidence/containers-f1e6e2f/) returned exit code 1 before any Docker command ran. Its cleanup list is empty because no stack was created. The procedures below remain to be executed on a host with Docker; the successful native recovery exercise does not verify their container equivalents.

Run the gate on a normal Linux Docker host or a CI runner with sufficient measured resources. Retain the source commit, resolved Compose configuration, image IDs, versions, health output, business API results, raw service logs and cleanup status. Do not upload tokens, private keys or live databases.

The executable harness targets only `unix:///var/run/docker.sock`, clears inherited Docker context variables and supplies that endpoint to every Docker invocation. When Docker is available, it builds the actual images and creates its own synthetic stack, private credentials and fresh volumes:

```bash
uv run python scripts/qualify_container.py \
  --source-commit "$(git rev-parse HEAD)" \
  --output evidence/runs/container-01
```

It checks container isolation, installed asset identity, all five runbook cases, response-loss reconciliation, worker restart, a stopped paired backup and restore, retained Temporal history, and an actual local-agent request. It removes only its uniquely named stacks and image tags; it never prunes shared Docker resources. On a smaller CI runner, an explicit `--model-cpus 2` override records the different CPU budget. It is not the reference host's throughput measurement.

The local-agent request always runs. The harness requires an observed model response and independently enforces safe effects; its semantic diagnosis result is recorded in `model-quality.json`. Add `--require-model-quality` to make correctness on that case an exit-status gate. Without that flag, a passed container-execution gate can coexist with a failed diagnostic-quality result. Neither outcome establishes the separate full-corpus acceptance gate.

The build/start sequence above is necessary but insufficient. Submit a synthetic freshness incident, observe a real MCP/model/Temporal path, approve a quality quarantine using the separate approver credential, and verify target rows and effect receipts. Exercise a worker restart and a stopped application/Temporal backup and restore. Confirm that only loopback API port 8080 is published, the worker cannot read the signing key, and the private target/model/Temporal ports are not published.

Use `docker compose logs --no-color` and `docker compose ps --format json` to retain original runtime evidence. Capture `docker image inspect` and an installed OS/package inventory for the built images. A CI job that only parses YAML, skips the model, replaces services with mocks or never reaches the business postconditions cannot mark the container gate as passed. Always stop the job's containers in cleanup. Keep or remove only that job's explicitly named synthetic volumes according to its retention policy.

## Optional local Temporal UI

The Temporal UI is private in the base configuration. An operator-owned override can publish it on loopback:

```yaml
services:
  temporal:
    ports:
      - "127.0.0.1:8233:8233"
```

Run `docker compose -f compose.yaml -f /absolute/path/to/ui-override.yaml up -d temporal` and open `http://127.0.0.1:8233`. Do not expose the development server on a public host interface. Remove the override after inspection; the same restriction applies to SSH tunnels.

## Optional Terraform ownership

Terraform manages exactly three Docker resources: the private bridge network and two named persistent volumes. Compose manages the application services. There are no cloud resources, remote daemons, billing changes or external accounts in this profile.

Choose ownership before first deployment:

| Mode | Network/volume owner | Compose invocation |
| --- | --- | --- |
| Default | Compose | `docker compose -f compose.yaml up -d` |
| Optional | Terraform | `docker compose -f compose.yaml -f compose.terraform.yaml up -d` |

First execute the verification-only gate against a clean source commit on the local Docker host:

```bash
uv run python scripts/validate_infra.py \
  --source-commit "$(git rev-parse HEAD)" \
  --output evidence/runs/infrastructure-01
```

The harness verifies the pinned Terraform archive against its retained official checksum manifest, copies the configuration and committed provider lock into a temporary directory, and runs formatting, readonly initialization, validation and an isolated create-only plan. It uses only the local Docker socket, retains original output and JSON, and never applies the plan. A failed stage stops later stages.

For a subsequent deployment into a fresh Terraform-managed namespace, inspect the plan before applying. These are operator procedures; no Terraform apply has been qualified by the retained run:

```bash
terraform -chdir=infra/terraform init -lockfile=readonly
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform plan -out=deployment.tfplan
terraform -chdir=infra/terraform apply deployment.tfplan
docker compose -f compose.yaml -f compose.terraform.yaml config --quiet
docker compose -f compose.yaml -f compose.terraform.yaml up -d
```

Keep `.terraform.lock.hcl` in Git; keep working state, plans and provider caches outside Git. Provider installation, static validation, planning and applying are distinct operations. A lock file records package selection and hashes, not an applied deployment. The project does not claim a successful Terraform apply without the corresponding execution evidence.

The [attempt against `f1e6e2f`](../evidence/infrastructure-f1e6e2f/) verified Terraform 1.17.2 and passed `fmt -check` and `init -lockfile=readonly`, installing Docker provider 4.7.0 from the committed lock. `validate -json` returned exit code 1 with `valid: false`, `Failed to load plugin schemas` and no provider handshake output. That retained output does not establish the lower-level cause. The attempt stopped before Docker access or planning; no resources were applied, and its temporary workspace was removed. Repeat the gate on a normal local Docker host or a functioning CI runner.

Set Terraform's `stack_name` and Compose's `DATAOPS_STACK` to the same value. Do not silently adopt existing Compose-owned resources into Terraform. Use a separate namespace or a reviewed import procedure. The external override removes Compose's internal-network attribute because Terraform owns it. All three Terraform resources have `prevent_destroy` protection.

## Native qualification without Docker

The standalone bootstrap retrieves the same assets used by the image builds:

```bash
python scripts/bootstrap_runtime.py --destination var/runtime
uv run python scripts/qualify.py \
  --runtime-config var/runtime/provisioning.json \
  --output evidence/runs/local-smoke \
  --profile smoke
```

Bootstrap verifies size and SHA-256, rejects modified cache/extracted files and records provenance. Cache and installation paths on the same filesystem share verified assets through hard links; treat both paths as immutable. Bootstrap starts no service. The qualifier must supervise all real services and clean up its children. On hosts where each command has a separate network namespace, run services and clients inside one supervisor invocation.

The smoke profile covers a subset of the checks. The retained [full native integration run](../evidence/qualification-f1e6e2f/) contains its original commands, source hashes, runtime identities, business observations, histories, failures and cleanup result. A future run must retain its own evidence and source identity; the current native results do not close the container, infrastructure, browser or model-quality gates.

## Sources

- [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/)
- [Temporal CLI 1.10.1](https://github.com/temporalio/cli/releases/tag/v1.10.1)
- [llama.cpp b12368](https://github.com/ggml-org/llama.cpp/releases/tag/b12368)
- [Official Qwen base-model source card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/cdbee75f17c01a7cc42f958dc650907174af0554/README.md)
- [Unsloth community-quantization source card](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/blob/a06e946bb6b655725eafa393f4a9745d460374c9/README.md)
- [Docker Compose 5.7.1](https://github.com/docker/compose/releases/tag/v5.7.1)
- [Terraform 1.17.2 release files](https://releases.hashicorp.com/terraform/1.17.2/)
- [Docker provider 4.7.0](https://registry.terraform.io/providers/kreuzwerker/docker/4.7.0/docs)
