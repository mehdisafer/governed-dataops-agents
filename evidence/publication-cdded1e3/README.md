# Post-merge publication receipt

This receipt records `main` after [PR #2](https://github.com/mehdisafer/governed-dataops-agents/pull/2):
commit `cdded1e3f54fd816ec1d4b323b93143417e722df`, tree
`582cfd0f391c20c662408e0ca13d9f2080d8fc71`. The tree is identical to reviewed
feature commit `7656622c68e1e74812f1c2cf02e512aad3795ce3`; that equality was checked
using the retained Git objects.

The six JSON reports beside this README are exact copies of the locally retained
captures. [manifest.json](manifest.json) records their source paths, lengths,
SHA-256 checksums, byte-equality verification and original dates. The four GitHub
files are **captured connector JSON strings**, not raw HTTP response bytes or
headers. Their formatting and content were not rewritten. The two scanner reports
retain their original redacted findings and separate content-bound proofs.

| Evidence | Captured observation |
| --- | --- |
| [History scan](secret-main-history.json) | All 6 reachable commits; 62 raw occurrences, 62 independently proved, 0 unresolved |
| [Working-tree scan](secret-main-worktree.json) | 193 files at the merged main commit; 31 raw occurrences, 31 proved, 0 unresolved |
| [Main ref](main-ref.json) | `refs/heads/main` points to the merge commit above |
| [Workflow run](main-workflow-run.json) and [jobs](main-workflow-jobs.json) | Run `43603386961`, attempt 1; core job `132472738198` failed with runner ID 0, an empty runner name and zero steps |
| [Artifacts](main-workflow-artifacts.json) | No workflow artifacts were returned |

The historical scan uses `--all --full-history -m`; merge-parent traversal counts
some identical content candidates again. Its 62 raw occurrences consist of 7 at
`f1e6e2f`, 24 at `7656622` and 31 at the merge commit. **This does not mean 62 unique
secrets.** The reports preserve those raw occurrences while separately proving
that they are the reviewed operation identifiers or source digests.

The remaining CI jobs—containers, model-evaluation, governance and
infrastructure—were skipped. The captured metadata provides no evidence that a
workflow step or project test executed. The underlying cause of the core failure
remains **unknown**; no billing, permissions, capacity or visibility explanation
is inferred. This receipt does not turn that CI result into a successful run.

Preparing this receipt did not edit application files, change Git references,
execute tests or services, or use a browser. Its expanded-directory secret scan
is recorded separately outside this directory so the scan does not contain its
own report. The earlier native qualification and its retained failed gates remain
unchanged. This receipt is intended for a separate evidence branch without a new
push to `main`.
