# Native qualification at f1e6e2f

This evidence records the complete native integration run from clean commit
`f1e6e2f3800242ec210145680261da8ab60f38b4`. The run started on 2026-11-14 at
12:57:19 UTC and finished at 13:22:15 UTC. The source was clean and unchanged
at both boundaries. The original result is **18 gates: 14 passed and 4 failed**;
this is not full acceptance.

The failed gates are `five_agent_business_cases`, `heldout_agent`,
`measured_agent_advantage`, and `real_browser_console`. All attempted cases,
including the unsuccessful model diagnoses, remain in the original summaries and
archive. The console browser failed to launch under the host's socket restriction.
Container, infrastructure and GitHub Actions observations are separate evidence
sets. Later changes to assurance tooling do not retroactively rerun this source.

## Complete originals and readable copies

[full-originals.tar.gz](full-originals.tar.gz) contains **all 192 original files,
5,470,157 uncompressed bytes**, under `qualification-f1e6e2f/`. Every archive member
was read back and checked against the original SHA-256 and length. The
[artifact manifest](artifact-manifest.json) records the complete file list,
archive checksum, source dates, readable selections and expanded-scan identity.
Tar/gzip header metadata was normalized; file contents are unchanged.

All 18 original nonincident JSON files are also readable beside the archive:
the complete results, run/source manifests, development and heldout case summaries,
failed-case details, comparison, load/resources, runtime/provisioning/command data,
process exits and cleanup. Four trace/history/workflow-result sets illustrate:

| Incident | Observed case | Outcome |
| --- | --- | --- |
| `inc-831ee2124bcf46e48d` | Actual-agent transient fault with committed effect and lost-response reconciliation | resolved |
| `inc-b4c61670fcc145f191` | Actual-agent schema migration proposal refused | denied |
| `inc-434f101a571d403c82` | Tampered/stale approval rejected, no effect, then cancellation | cancelled |
| `inc-eabad319c86846f1ac` | Actual-agent heldout quality quarantine with approved containment | contained |

These selected examples do not replace the complete failed-case record. The
development-agent quality case, for example, did not reach its expected outcome.

## Secret review before archiving

The entire expanded original directory was scanned before compression. The
unchanged raw and reviewed reports retain **229 raw candidates**: 220 operation
identifiers independently derived from a validated Plan in the same artifact,
and 9 source digests recomputed from the retained clean Git commit. All 229 were
proved with exact artifact, line, rule and redacted-match bindings; **0 remain
unresolved**. This is not a claim of zero raw findings or a guarantee that pattern
scanning detects every possible credential.

For reproduction, from the repository root in a fresh checkout (or after checking
that the extraction destination does not already contain a run):

```bash
mkdir -p evidence/runs
tar -xzf evidence/qualification-f1e6e2f/full-originals.tar.gz -C evidence/runs
uv run python scripts/secret_scan.py \
  --directory evidence/runs/qualification-f1e6e2f \
  --reviews evidence/qualification-f1e6e2f/expanded-secret-review.json \
  --output evidence/runs/qualification-expanded-rescan.json
```

The extraction-specific review registry has 229 entries for those original paths.
The repository-wide registry separately binds the readable promoted copies.
Original reports retain their original paths, dates, raw findings and scope.
