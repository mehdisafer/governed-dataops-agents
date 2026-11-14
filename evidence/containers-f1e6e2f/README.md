# Container gate — complete original evidence

The two original run files are preserved byte for byte for frozen source commit
`f1e6e2f3800242ec210145680261da8ab60f38b4`. The gate recorded failure because the
Docker CLI/daemon was unavailable. Container execution and full container
acceptance remain unverified; the native process run is separate.

`selection-manifest.json` records copy equality, original dates, checksums and
independent recomputation of all 38 declared source inputs against the retained
commit. No original manifest has been omitted or rewritten.

`secret-scan-prescan.json` retains the original expanded scan: 2 raw candidates
were initially unresolved because the frozen proof helper did not recognize
`source.tracked_and_clean`. `source-digest-provenance.json` retains the independent
Git-blob check. After the integration run closed, the helper gained exact support
for the three-key `{commit, tracked_and_clean, files}` manifest; tests continue to
reject dirty flags, forged digests, extra or ambiguous schema keys and arbitrary
API-key-shaped values.

`secret-scan-reviewed.json` is the actual subsequent expanded scan: **2 raw
candidates, 2 independently recomputed source-digest proofs, 0 unresolved**. The
values are SHA-256 digests of `scripts/secret_scan.py` and
`src/governed_dataops/api.py` read from the named immutable Git commit. The raw
findings remain present. `expanded-secret-review.json` reproduces that check
against the original `evidence/runs/container-f1e6e2f` paths; the repository-wide
registry separately binds the unchanged readable copies here.

Successful secret review is not successful container execution.
