# Infrastructure gate — complete original evidence

All original files from `evidence/runs/infrastructure-f1e6e2f` are preserved byte
for byte for frozen source commit `f1e6e2f3800242ec210145680261da8ab60f38b4`.
They include command records, original stdout/stderr, tool provenance, the
upstream checksum manifest and licence, and the gate result.

The gate recorded a validation failure (exit 1). Terraform apply was not executed,
resource changes were not applied, and the source snapshot remained unchanged.
The original diagnostic outputs retain the details. A successful infrastructure
application or deployment is not established by this evidence.

`selection-manifest.json` records each copied artifact, its original dates,
checksum and byte equality, plus the recomputation of every declared source input
against the retained commit. `secret-scan-prescan.json` preserves the actual scan
of the complete expanded original directory: **0 raw candidates**. The native
process integration and container gate are separate evidence sets.

The full original directory is preserved without compression, omission or
alteration. Preparation of this evidence does not execute Terraform apply.
