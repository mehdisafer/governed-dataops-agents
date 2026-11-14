# Evidence retained with the source

The complete native integration run used clean, unchanged application source `f1e6e2f3800242ec210145680261da8ab60f38b4` on **2026-11-14**. It passed **14/18 requested checks** and returned a nonzero exit. The reserved comparison was **10/10 for the runbook and 2/10 for the local agent**. Every reserved case has an observed final business state; failures and incomplete model usage remain visible.

## Evidence index

| Collection | Contents | Scope |
| --- | --- | --- |
| [Native qualification](qualification-f1e6e2f/) | Readable run/results/comparison/load metadata; four correlated examples; complete 192-file archive and integrity manifest | Original clean-source real MCP/PydanticAI/Temporal execution, including failed model/browser cases |
| [Complete native originals](qualification-f1e6e2f/full-originals.tar.gz) | All 192 original files, including service logs, resource samples, 56 histories, correlated traces and workflow results | Expanded files scanned and exactly reviewed before compression; no selective success-only archive |
| [Earlier recovery development](recovery-development/) | Previously retained trace/history plus the separate 26-history selection archive, manifests and review records | Earlier worktree was dirty; current run replayed the concrete histories, not a certified release-to-release upgrade |
| [Development diagnostics](development/) | Two earlier original model trials with failures and usage measurements | Development data, separate from the clean integrated five-case run and the reserved comparison |
| [Security and inventories](security/) | Frozen-source scans, original JUnit, strict runtime dependency audit and component inventory | Dated, explicitly scoped checks; no OS/container/native-code certification |
| [Publication checks](publication-checks/) | Final 232-test local report, static/contract checks, exact changed-code identities and independent archive verification | Post-run harness/verifier checks; no new native/model/deployment result |
| [Container attempt](containers-f1e6e2f/) | Original run and cleanup metadata | Stopped before build because Docker was unavailable |
| [Infrastructure attempt](infrastructure-f1e6e2f/) | Terraform commands, original stdout/stderr/JSON, archive provenance and source inputs | Version/fmt/init succeeded; provider-schema load failed; no plan or apply |
| [Hosted CI attempts](github-actions-43597256488/) | Eight original API observations and retrieval errors | Both attempts failed before runner assignment; zero steps and no test artifacts |

The [qualification ledger](../docs/QUALIFICATION.md) is the consolidated interpretation. The [evaluation report](../docs/EVALUATION.md) distinguishes development, reserved scoring, output availability and timing. The [backlog](../docs/BACKLOG.md) records what remains to establish acceptance.

## Integrity and security review

A SHA-256 hash identifies bytes. It is not an independent audit, a security certification or proof of model correctness. Each collection retains an artifact manifest, source scope or both. Readable promoted originals remain byte-identical to their source files; complete archives preserve the original failures, not edited summaries.

The native expanded run contained 229 raw Gitleaks candidates: 220 Plan-derived operation identifiers and nine source-blob digests tied to the exact clean Git revision. Every occurrence has an exact artifact/line/rule/redacted-match record and a recomputed semantic proof. The separate 26-history selection contained 57 such operation-identifier candidates, all reviewed. These positive raw counts remain visible; they are not reported as zero raw findings. The exact registries are provided with the corresponding collections. [SECURITY.md](../docs/SECURITY.md) explains the scanner and its limits.

The earlier full development run also contained dirty-source manifest candidates that could not be proved against an exact clean source. Those dirty manifests are not included in the selected prior-history archive and are not silently waived. The archive's scope is explicitly the 26 original histories, whose contents can be independently replayed and reviewed. The clean native run archive includes every one of its 192 original files.

## Reproduction and retention boundaries

New qualification runs write original results, workflow histories, traces, source manifests and service logs under the ignored `evidence/runs/` directory. Credentials and live databases are created in a separate temporary directory and removed when the supervisor stops. Reviewed reports are promoted here or attached to CI; an untracked local file is not a durable published result.

Read each archive's README for extraction, manifest verification and exact-registry scanning. Scan the expanded directory, including ignored files, before any redistribution; a compressed file is not a substitute for expanded scanning. Reports must be written outside the directory being scanned.

The previous session's transient workspace was unavailable on 2026-11-14. Conversation-only historical results from that workspace are not reused to validate the reconstructed implementation. The earlier-development collection listed above consists of retained originals produced during the current reconstruction.

The frozen native run and later publication checks have separate source identities. Corrections to the qualification harness and semantic secret verifier after the native run are regression-tested separately; no fresh full native run is implied. Unit/boundary tests label fake Temporal/provider boundaries, and native/container evidence is reported separately.
