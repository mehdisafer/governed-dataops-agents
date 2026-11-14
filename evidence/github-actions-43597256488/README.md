# GitHub Actions run 43597256488 — original responses

These eight JSON files are unchanged copies of the captured GitHub API responses
and retrieval errors for source commit `f1e6e2f3800242ec210145680261da8ab60f38b4`.
`selection-manifest.json` records their original paths, byte counts, SHA-256
checksums and available dates. Original responses retain their captured content and scope.

| Attempt | Core job observation | Downstream jobs |
| --- | --- | --- |
| 1 | Completed with failure; runner ID 0, empty runner name, zero steps | Infrastructure, governance, containers and model evaluation skipped |
| 2, one bounded retry | Completed with failure; runner ID 0, empty runner name, zero steps | Infrastructure, governance, containers and model evaluation skipped |

These responses show that the core job failed before a runner was assigned and
before any workflow step executed. They do not show a failing project test or a
successful CI validation. The failed-check annotation endpoint was unavailable
through the available connector; the attempted log retrieval returned HTTP 404.
Both retrieval errors are retained unchanged. The underlying cause remains
unknown. No billing, account, capacity or repository-visibility explanation is
inferred from the missing diagnostics.

The run coordinator also reported a read-only check of the exact failed-job URL
in the isolated cloud browser. With no authenticated GitHub session, the page
displayed a logged-out HTTP 404 and provided no further diagnostic evidence. This
is a supplemental observed limitation, not an additional API response; no JSON
artifact has been invented for it. That check involved no login, credential,
billing or permission change and no access to a personal computer.

The native test and integration evidence is separate. The skipped GitHub jobs
provide no execution evidence for those checks, and the retry does not change
that limit. Only one retry is represented here.
