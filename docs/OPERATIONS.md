# Operations, recovery and change management

## Objectives and observed limits

The primary objective is business correctness: every committed effect must have a durable target ledger entry and fresh scoped verification. An unavailable model, incomplete observation or invalid approval must produce an explicit refusal or escalation. Quarantine is containment, not repaired data.

The following thresholds are operating choices, not measured availability guarantees:

| Signal | Initial threshold | Operator response |
| --- | --- | --- |
| Unjustified committed effect | Any occurrence | Stop admission and workers, preserve state and investigate |
| Unknown effect outcome | Any unreconciled occurrence | Inspect the exact idempotency key in the target ledger; do not force a repeat with another key |
| Admission queue | 32 pending incidents | Honour HTTP 429 and Retry-After; inspect worker/model capacity, retry the same event identity |
| Local model request | 90 seconds, 300 output tokens | Inspect model health, prompt revision, usage and context size; retain failed cases in the evaluation denominator |
| Application/Temporal disk | 80% host volume usage | Plan retention or storage expansion before writes fail; preserve live histories and effect receipts |
| Service health | Three consecutive failed checks | Inspect service dependencies; a restart alone is not verified recovery |

The queue limit, worker activities, target transactions and model slots are different constraints. The reference worker has four concurrent activity slots; the local model has one inference slot. A model-call semaphore is local to its worker process, so adding workers does not add inference capacity. SQLite serializes writes on one host. Revision checks and effect receipts protect conflicting operations; they do not demonstrate multi-host scalability.

Model resource settings and failure history are documented in [deployment](DEPLOYMENT.md). Native service evidence, container execution evidence and historical observations that no longer have retained raw files must remain clearly distinguished. Use the current run artifacts, not an old completion claim, to judge the state of the system.

## Routine inspection

Run `docker compose ps` and `docker compose logs --since=10m api worker target temporal model`. Process logs are rotated to three 10 MiB files per service. Decision events in the transactional store identify incidents, plans and effects. Raw service stdout is not uniformly structured telemetry.

The authenticated API `/metrics` endpoint exposes scoped incident counts and configured capacities. Configured worker slots do not measure live utilization. Temporal's metrics stay private on port 8234 and llama.cpp's `/metrics` stays private on port 8090. There is no unvalidated monitoring stack or public metrics endpoint. An approved collector can join the private network.

For an incident, inspect the received event, evidence, model or runbook decision, immutable plan hash, policy result, approval envelope if needed, effect key and final target observation. A confidence score is not an acceptance criterion. Keep unsuccessful diagnostic attempts and incomplete usage measurements visible.

## Incident runbooks

| Incident | Permitted path | Verified business result |
| --- | --- | --- |
| Freshness breach | Refresh a compatible, valid, unprocessed pending batch | Curated rows present, backlog and duplicates absent, freshness objective met |
| Transient technical failure | Retry the known failed batch | Actual rows loaded once and transient flag cleared |
| Incompatible schema | Refuse automatic migration and escalate | No mutation; evidence identifies the schema mismatch |
| Quality rejection | Separate signed approval, then quarantine | Rejected rows isolated from curated storage; outcome is contained |
| Duplicate delivery | Suppress an already-applied redelivery | Existing curated rows preserved without a second application |

### Invalid or expired approval

Compare the plan hash, incident, target, environment, scope, expected revision and policy version. An approval must be signed, registered, unexpired and issued by the separate approver identity. The API re-reads target state before signing; execution rechecks it again. A changed plan, expired envelope or changed state requires a new decision. Never edit an existing approval row or reuse its signature for another plan.

If approval delivery to Temporal is unconfirmed, retry the same plan identity through the API and retain the original envelope. An HTTP timeout does not prove that a durable signal failed. Do not invent a second decision simply to hide uncertainty.

### Response lost after an external effect

An HTTP timeout, broken MCP connection or activity timeout does not establish write failure. Look up the original idempotency key in the target ledger. If a committed effect is recorded, collect fresh target evidence and verify the postconditions. Escalate if reconciliation is unavailable or ambiguous. Another key identifies another operation and can defeat deduplication.

This synthetic target commits its business change and effect receipt in one SQLite transaction. That supports reconciliation for this target; it is not an exactly-once guarantee for arbitrary third-party APIs.

### Worker stops or becomes saturated

Stop admission if the queue is exhausted. Restart the same worker version with the same Temporal namespace and task queue. Pending work remains in Temporal; do not create replacement incidents merely to trigger execution. Action activities must reconcile before a new write attempt. Review final business-state verification even if the workflow completed.

Use bounded restart, contention and replay evidence from the current qualifier. A small successful contention test is not a scale guarantee. Target-partitioned queues and additional workers need new invariant and load tests before they are described as supported capacity.

### Cancellation

An operator requests cancellation through the API. Cancellation is a durable request, not a rollback primitive. A committed target effect still requires reconciliation and verification. Preserve its outcome and escalate when compensation needs a separate reviewed action.

## Backup scope

Back up the application and Temporal databases as a consistent stopped pair. The application snapshot contains incidents, evidence, approvals and effect receipts; Temporal contains workflow histories. Restoring only one can make the system disagree about effects that already happened.

An application-only SQLite snapshot is useful for inspection but is not a complete workflow-system recovery point. Never copy a live SQLite main file while ignoring its WAL. The procedure below uses SQLite's backup API after writers stop.

The CLI supports an application-only snapshot with `uv run dataops --env-file .env backup --output var/backups/application.db`. Label that output accordingly; it does not include the Temporal database or secret material.

Store the approval key pair and role credentials in a separate encrypted backup controlled by the deployment owner. Never include secrets in published evidence. Retain the public key that validates restored approval envelopes. Rotation can invalidate pending approvals and requires an explicit operational decision.

## Create a stopped, consistent backup

These commands use Compose-owned resources. If Terraform owns them, use the same external-resource override on every Compose invocation. Run as the non-root deployment account, with UID/GID matching secret-file ownership.

```bash
mkdir -p var/backups
export DATAOPS_BACKUP="$PWD/var/backups/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -m 700 "$DATAOPS_BACKUP"
docker compose stop api
docker compose stop -t 45 worker target
docker compose stop -t 45 temporal
docker compose run --rm --no-deps -T \
  --user "$(id -u):$(id -g)" \
  -v "$DATAOPS_BACKUP:/backup" --entrypoint python init-state - <<'PY'
import hashlib, json, pathlib, sqlite3
from contextlib import closing
out = pathlib.Path('/backup')
manifest = {'files': {}, 'scope': 'stopped application and Temporal pair'}
for name, source in [('dataops.db', '/data/dataops.db'), ('temporal.db', '/temporal/temporal.db')]:
    destination = out / name
    if destination.exists():
        raise RuntimeError(f'Refusing to replace {destination}')
    with closing(sqlite3.connect(f'file:{source}?mode=ro', uri=True)) as src:
        with closing(sqlite3.connect(destination)) as dst:
            src.backup(dst)
            if dst.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                raise RuntimeError(f'Integrity check failed for {name}')
    destination.chmod(0o600)
    with destination.open('rb') as f:
        manifest['files'][name] = hashlib.file_digest(f, 'sha256').hexdigest()
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
PY
docker compose up -d --wait --wait-timeout 180
```

Record the source commit, image IDs, `uv.lock` hash, runtime versions, backup timestamp and secret-key identifiers alongside the manifest. Hashes detect changed bytes; they do not prove that restoration works. If the backup fails, inspect the failure before resuming ordinary admission.

## Restore into a new namespace

Use fresh named volumes so the original state remains available for investigation. Restore with the same application version and runtime assets as the recovery point. Stop the original services first; this also avoids running two model servers on one host during recovery.

```bash
docker compose stop -t 45
export DATAOPS_STACK=governed-dataops-restore
docker compose -p "$DATAOPS_STACK" run --rm init-state
docker compose -p "$DATAOPS_STACK" run --rm --no-deps -T \
  --user "$(id -u):$(id -g)" \
  -v "$DATAOPS_BACKUP:/backup:ro" --entrypoint python init-state - <<'PY'
import hashlib, json, pathlib, shutil, sqlite3
root = pathlib.Path('/backup')
manifest = json.loads((root / 'manifest.json').read_text())
for name, target in [('dataops.db', '/data/dataops.db'), ('temporal.db', '/temporal/temporal.db')]:
    source, destination = root / name, pathlib.Path(target)
    if destination.exists():
        raise RuntimeError(f'Refusing to overwrite restore target {destination}')
    with source.open('rb') as f:
        if hashlib.file_digest(f, 'sha256').hexdigest() != manifest['files'][name]:
            raise RuntimeError(f'Backup hash mismatch: {name}')
    with source.open('rb') as src, destination.open('xb') as dst:
        shutil.copyfileobj(src, dst)
    destination.chmod(0o600)
    with sqlite3.connect(f'file:{destination}?mode=ro', uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise RuntimeError(f'Restored integrity check failed: {name}')
PY
docker compose -p "$DATAOPS_STACK" up -d --wait --wait-timeout 180
```

Before reopening admission, check health, incident histories, target revisions, curated row counts and effect keys. Demonstrate that replay/reconciliation adds no second effect. Check pending approvals for expiry. Record command output and observed invariants, including failures. Only an executed restoration exercise supports a restore claim. A documented container procedure and an executed native recovery test are separate evidence.

## Migrations and rollback

Packaged migrations must be numbered and applied transactionally. Before changing a database schema or workflow, stop admission, take the consistent recovery point, retain the previous image and replay saved histories against the proposed workflow code.

Do not generate migration SQL from model output or edit migration history in place. Apply the project's packaged migration entry point with services stopped. Restart only after migration results and compatibility checks are satisfactory.

For Compose, the explicit command is `docker compose run --rm --no-deps api migrate`. For a native instance, use `uv run dataops --env-file .env migrate` with the intended configuration file.

Reverting an image is safe only when its database schema and retained Temporal histories are compatible. A forward-only migration has no automatic inverse. Otherwise restore the stopped pair into fresh volumes using the matching older application version. Never restore only the application database to undo an effect whose Temporal history already records completion. Changes in workflow execution order require replay and appropriate Temporal versioning or patching.

## Retention and release gates

This release has no automatic database retention or archival service. Monitor disk use and preserve unresolved incidents, effect receipts and retained histories. Do not delete receipts merely to free disk while retries remain possible.

Before publication, inspect Git history, issue/PR text, raw logs and exported artifacts for secrets and private data. Synthetic inputs do not replace that check. Keep visibility and project-licence decisions explicit. Container startup, a checksum match, a backup setting or an implementation flag cannot substitute for its corresponding acceptance evidence.
