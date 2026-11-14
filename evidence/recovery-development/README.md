# Development recovery evidence

These files are unchanged copies from `evidence/runs/governance-development-01`,
recorded on 2026-11-14 against a development worktree. The recorded source manifest
identifies commit `78a46751f69cc719c85aee123b58a7f86810df97` plus local changes;
this is not evidence of the later clean-source qualification.

The selected incident is the transient-failure case `development-02`. It uses the
explicit deterministic runbook mode, not the language model. The supervisor
requested the response-loss fault: the target committed its bounded effect and
receipt, then returned an unavailable response; the workflow reconciled that
receipt and subsequently checked freshly observed business state.

- [Original trace](trace-inc-e2934f1e29ba4032bf.json) contains the durable incident events.
- [Original Temporal history](history-inc-e2934f1e29ba4032bf.json) retains the native event data and stable operation identifiers.
The developmental source manifest is deliberately omitted from this published selection. Its three scanner candidates do not match source bytes at the commit it names; one also differed from the worktree at review time, so immutable provenance could not be reconstructed. The untouched original remains in the local development run. This omission is not an adjudication of those candidates and does not affect the two unchanged incident artifacts. The completed [f1e6e2f qualification](../qualification-f1e6e2f/README.md) separately binds its evidence to a clean, retained source commit.

The JSON content is not rewritten to remove legitimate operation identifiers or
to silence secret detection. The expanded original run and these selected files
are scanned before any archive is considered for publication. Redacted scanner
findings and any exact content-bound non-secret proofs are retained separately.
A claim of zero raw candidates must never replace a report of reviewed candidates.

The selected trace/history produce **7 raw generic-api-key candidates**. Each is
reviewed through an exact artifact checksum, source line, rule and redacted match,
then independently recomputed from a full Plan stored in that artifact. Temporal
JSON/plain payloads are base64-decoded for that proof. The review registry is
[secret-review.json](../secret-review.json); no arbitrary API-key-shaped hash is
waived. The raw count remains 7 after successful semantic review.

## Scan coverage and unresolved development provenance

[The expanded-original-run report](secret-scan-original-run.json) preserves all
**124 raw candidates**, **115 independently recomputed operation identifiers**,
and **9 unresolved source-digest occurrences**. Three are in the original
`source-manifest.json`; six repeat those source snapshots inside the original
`run.json`. Neither of those original files is included in this published
selection, and the complete development run is not distributed as a hidden
compressed archive. Both originals remain untouched in the local development run.

[The first selected-files report](secret-scan-before-review.json) retains the
initial 10 raw candidates before the developmental manifest was omitted. This
historical report intentionally remains an unreviewed snapshot; the selected
trace/history have seven mathematically verified operation identifiers. The
separate completed [f1e6e2f qualification](../qualification-f1e6e2f/README.md)
binds its expanded artifacts to a clean source commit and retains its four failed
gates. It does not resolve the earlier development manifest's provenance gaps.

## Complete earlier-history selection for replay

[prior-histories.tar.gz](prior-histories.tar.gz) preserves all **26 original
Temporal histories** from `governance-development-01`, totaling **1,264,384
uncompressed bytes**. The clean f1e6e2f qualification replayed these histories;
the separate [manifest](prior-histories-manifest.json) records their exact hashes,
archive members and verified byte equality. No event payload was rewritten.

This archive contains histories only. It does not include the dirty development
`run.json` or `source-manifest.json`, and it does not establish that the earlier
whole source tree was clean. The earlier workflow file itself is independently
recoverable from commit `78a46751f69cc719c85aee123b58a7f86810df97` and has SHA-256
`92739ffdd0b9508707229e3f55d9841712a64da74a54142e729510617a52a67c`.

The expanded 26-file selection was scanned before archiving: **57 raw candidates,
57 exact Plan-derived operation-key proofs, 0 unresolved candidates**. Both the
unreviewed and reviewed original redacted reports are retained. The copied report
paths name the staging selection actually scanned; the separate review registry
maps the same immutable file/line/match bindings to the original extraction paths.

From a fresh checkout, after checking the destination does not already contain
a development run:

```bash
mkdir -p evidence/runs
tar -xzf evidence/recovery-development/prior-histories.tar.gz -C evidence/runs
uv run python scripts/secret_scan.py \
  --directory evidence/runs/governance-development-01 \
  --reviews evidence/recovery-development/prior-histories-secret-review.json \
  --output evidence/runs/prior-histories-expanded-rescan.json
```

The original complete-development scan and its nine unresolved dirty-source
occurrences remain reported above. The history-only selection does not waive
those excluded occurrences or turn the earlier whole-run scan into a pass.
