# Security model and reporting

This repository is a demonstration over synthetic industrial pipeline data. Its
security boundary is an untrusted model and untrusted incident/log text operating
through reviewed application code. It is not a hostile multi-tenant execution
platform, and its local Temporal development server is not an authenticated
production cluster.

## Trust boundaries

| Boundary | Implemented control | Remaining assumption |
| --- | --- | --- |
| Incident/log text → diagnosis | Typed output, bounded context, verified evidence references, **necessary typed-snapshot precondition and category/action checks** (P0 fix candidate), enumerated actions | The model can still make an incorrect or incomplete diagnosis. These guards reject unsupported proposals but never replace them with a runbook result; target policy rechecks facts independently |
| Diagnosis → execution | Canonical plan hash, fixed catalogue, live target preconditions, one action, delegation depth at most one | Application, policy and catalogue source are trusted and reviewed |
| Executor → approved action | Approver role distinct from executor; exact plan, target, environment, scope, revision and policy binding; bounded expiry; Ed25519 signature and persisted approval envelope | The API's configured approver credential identifies a trusted human operator; there is no external identity provider |
| HTTP caller → target | Distinct configured bearer credentials; identity derived from target configuration; scope checks on reads, effects and reconciliation | Credential secrecy and the surrounding host/network remain trusted |
| Business mutation → receipt | Actual source/curated/quarantine rows and the effect ledger commit together in one SQLite transaction | This atomicity applies to this target; it is not a general exactly-once guarantee for arbitrary APIs |
| Runtime → inference provider | Local route by default; explicit configuration, HTTPS and a credential required for external inference | Local process identity, host DNS and network administration are trusted |
| API/UI → browser | Data rendered as text; same-origin assets and a restrictive content security policy | The static frontend and browser remain trusted |

The worker is trusted code. It has access to the shared SQLite application volume
for audit persistence, and a malicious replacement worker could bypass these
application-level controls by writing that volume directly. The demo does not
claim database-user separation, row-level database access control, or protection
from a malicious host administrator. Separate processes and container mounts
reduce accidental credential exposure but do not establish that stronger boundary.

The model has no arbitrary shell, filesystem, network, SQL, or credential tool.
The MCP server exposes the bounded evidence/effect/reconciliation operations. The
model's rationale is data; it cannot grant a role, add a catalogue operation,
increase a budget, or turn a log instruction into a permission. Schema migration
is always refused by the executable policy. Quality quarantine requires approval
and is reported as containment, not as restored data quality. Every mutable
production-labelled plan also requires approval. The production label is a policy
test in a synthetic target, not a deployment into a real production system.

## Approvals and credentials

The API signs an exact approval envelope with an Ed25519 private key. The worker
and target receive only the public verification key. In the supplied Compose
configuration, only the API mounts `approval-private.pem`; the worker receives
reader/executor credentials and the target receives the credentials needed to
authenticate its endpoints. The worker does not receive the approver credential.
The target verifies both the signature and the exact persisted envelope before
performing an approved mutation. Merely inserting an asserted approver identity
into SQLite is insufficient to pass that execution check.

The API reuses the same persisted, unexpired signed envelope after ambiguous
approval-signal delivery. An expired envelope fails authorization; a new approval
request must pass the API's fresh target checks. The target rereads state inside its write transaction, so a revision,
policy, evidence or scope change invalidates stale authorization. The idempotency
key binds the canonical plan and action index; it cannot be reused for another
plan. Reconciliation returns the previously committed receipt without repeating
the mutation.

Role credentials have no working defaults. Configured credentials must be distinct
and at least 24 characters long. Prefer the documented `*_TOKEN_FILE` settings and
the supplied secret-generation command over secrets in shell arguments. Setting
both the raw value and its corresponding file is rejected. Keys are generated
without overwriting existing files; the private key is created with mode `0600`.
Do not commit credentials, private keys, live database backups, or private incident
data. Git ignores are an accident-prevention measure, not access control.

The local native qualification supervisor uses one operating-system user. That
user can access process configuration and state, so its tests do not demonstrate
isolation against a malicious user on the host. The reference Compose network is
private and the review API is bound to loopback. Do not expose the development
Temporal, target or model endpoints to an untrusted network. A deployment outside
that boundary needs authenticated infrastructure, transport security, access
control, rotation and operational ownership appropriate to that environment.

## Failures and audit state

An unavailable or incomplete observation, unsupported version, changed target,
exhausted budget, invalid approval or disallowed action prevents mutation. A lost
HTTP response after a committed effect triggers receipt reconciliation. Denied
requests do not consume an effect-ledger row or change business data.

Incident admission is transactional and bounded. A duplicate event with the same
content returns the existing incident; reuse of an event identifier for different
content is rejected. Terminal incident status is monotonic even if delayed
activity, approval or cancellation audit events arrive later. Backup uses SQLite's
backup interface and verifies the resulting database's integrity; application and
Temporal state have separate recovery responsibilities described in
[OPERATIONS.md](OPERATIONS.md).

Audit redaction handles known credential-shaped fields. This is not a substitute
for treating arbitrary incident text and Temporal history as potentially sensitive.
Use only synthetic data for distributable examples and review the exact artifacts
before publication. Stable event, plan and idempotency identifiers may be needed
to replay evidence; they should not be removed simply to make a scanner quiet.

## Reproduce security checks

The secret scanner downloads Gitleaks **8.30.1** from its
[official release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1),
verifies both its pinned SHA-256 archive and the pinned upstream checksum
manifest, compares installed bytes with the verified archive, then checks the
reported version. Its bundled licence is MIT. The install remains under ignored
`var/tools/`. Verification binds the bytes to that reviewed release; it is not an
independent audit of Gitleaks or its upstream supply chain.

```bash
uv run python scripts/secret_scan.py --working-tree --output evidence/runs/security-current/worktree.json
uv run python scripts/secret_scan.py --output evidence/runs/security-current/history.json
uv run python scripts/secret_scan.py --directory evidence/runs/RUN_ID --output evidence/runs/security-current/expanded-run.json
uv run python scripts/component_inventory.py --output evidence/runs/security-current/component-inventory.json
uv export --frozen --no-dev --no-emit-project --format requirements-txt --output-file evidence/runs/security-current/requirements.txt
uvx --from pip-audit==2.10.1 pip-audit --disable-pip --strict --format json --output evidence/runs/security-current/pip-audit.json -r evidence/runs/security-current/requirements.txt
```

Working-tree mode snapshots every tracked file plus untracked files not ignored
by Git. A tracked credential path is still included even if a later `.gitignore`
rule matches it. Symlinks are scanned as link text and are not followed outside
the authorized repository. History mode scans all reachable refs with full
history, including merge-parent differences. It refuses a shallow clone or an
empty history. It does not inspect unreachable dangling objects or a private
remote's un-fetched refs. Fetch the intended complete history before claiming its
coverage, and rerun after the implementation commit exists.

Expanded-directory mode includes all files inside the explicitly named repository
directory, including Git-ignored files. Use it on the original expanded run before
creating a distribution archive. A compressed archive is not a replacement for
that scan. The report must be written outside the directory being scanned.

The scanner forces upstream default rules, disables local ignore files and inline
waivers, and emits native findings with full secret redaction. Upstream built-in
rule allowlists still apply. It retains the raw finding count and reports any
unreviewed candidate as a failure. There is no blanket exception for hexadecimal
strings, model/source hashes, API-key-shaped fields, or evidence directories.

The explicit registry `evidence/secret-review.json` records individual reviewed
occurrences: repository-relative file, rule, line, full artifact SHA-256 and exact
redacted-match SHA-256. `--reviews` can select a separate registry for a local run.
An entry is insufficient on its own: every scan recomputes its semantic proof.
An `idempotency_key` must equal the canonical `effect_key(Plan, 0)` for a complete
validated Plan inside the same artifact. Only actual Temporal JSON/plain payload
envelopes are base64-decoded; arbitrary log strings are not treated as proof.
API-key fields, invented hashes, changed plans, duplicate JSON keys and changed
artifact bytes do not satisfy that check. The native redacted match must correspond
to the exact value on the recorded source line or in its decoded payload.

A source-manifest candidate must be the digest of the exact blob fetched from its
named retained Git commit and source path, and its manifest must record a clean
source state. Dirty development manifests remain unresolved when that provenance
is unavailable. Historical findings are checked against the artifact bytes at the
finding's commit, not just the current working file. The report retains all native
findings, puts proved occurrences in `reviewed_non_secret_candidates`, and returns
failure if any occurrence remains unresolved. A successful reviewed report says
`reviewed_non_secret_findings`; it never changes a positive raw count to zero.

`pip-audit` **2.10.1** is run in an isolated tool environment against the frozen
runtime requirements, with strict mode and no broad vulnerability exclusions. Its
primary sources are the [PyPA tool](https://github.com/pypa/pip-audit) and the
[versioned distribution](https://pypi.org/project/pip-audit/2.10.1/). Preserve its
original JSON, stdout/stderr, command, input checksum and execution date. It does
not audit OCI base images, native model binaries, the operating system, or model
behaviour. A report with no known findings is a dated result, not a certification
or proof that a dependency has no vulnerability.

The component inventory includes installed development packages as well as the
runtime lock, and retains missing licence metadata. Runtime artifacts are marked
verified only when present and their bytes match the declared pins; a provisioning
manifest alone is not proof of execution. Third-party provenance and the unresolved
project-licence decision are recorded in [THIRD_PARTY.md](THIRD_PARTY.md).

## Report a vulnerability

Do not put a live credential, private incident export, database backup or exploitable
private endpoint into a public issue. If GitHub shows a private **Report a
vulnerability** option for this repository, use that channel. Otherwise contact
the maintainer through an already established private channel to arrange secure
disclosure. No private email address or guaranteed response time is asserted here.

A useful report includes the affected commit, the violated boundary, a minimal
synthetic reproduction and the observed effect. For a leaked credential, revoke
or rotate it through its owner; deleting a file or closing an issue does not make
an exposed credential safe. General, non-sensitive implementation questions can
use the repository's public issue tracker.
