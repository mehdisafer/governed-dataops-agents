# Frozen-source security evidence — original reports

These are byte-identical copies of the original reports selected for source commit
`f1e6e2f3800242ec210145680261da8ab60f38b4`. `selection-manifest.json` records each
original path, SHA-256, byte count and source dates. The selection preserves the actual report scope; no compressed content is used
to bypass the expanded evidence scan. Original reports are not rewritten to change their
scope, raw findings or timestamps.

| Evidence | Observed scope and result |
| --- | --- |
| `source-freeze-history.json` | All three reachable commits through the frozen source commit; 7 raw candidates, 7 content-bound non-secret proofs, 0 unresolved candidates |
| `source-f1e6e2f-worktree.json` | Fresh scan at that commit of all 86 committed files; 7 raw candidates, 7 proofs, 0 unresolved candidates |
| `pre-freeze-pytest.xml` | Original JUnit report: 172 tests, 0 failures, 0 errors, 0 skipped; unit/boundary tests are separate from the live integration run |
| `pip-audit.json`, stdout/stderr, summary and `requirements.txt` | Original strict pip-audit 2.10.1 result for 50 frozen runtime dependencies: 0 known vulnerabilities reported and 0 skipped dependencies |
| `component-inventory-f1e6e2f.json` | 61 installed distributions, 64 lock entries and 6 local runtime artifacts whose size/SHA-256 match their pins |
| `synthetic-scanner-probe-summary.json` and redacted probe report | Earlier standalone Gitleaks detection probe: both generated noncredential candidates were detected; one was in a tracked file covered by a Git-ignore rule |

The dependency audit was not rerun during model integration: its recorded input
lock and exported requirements hashes still match the frozen inputs. Preserve
its original execution/recording dates; this is a dated known-vulnerability query,
not a certification of the operating system, OCI layers, native binaries or model.
The inventory includes development dependencies and retains the unresolved
project-licence choice.

The seven raw findings in the frozen-source scans are legitimate operation
identifiers in the retained development recovery trace/history. The reports retain
each native redacted finding and its exact artifact-bound mathematical proof;
these scans do not claim zero raw findings. The earlier synthetic detection probe
is a separate fixture check, not the frozen-source integration run. Its intentional
fake-secret source files are not included here.

Live model, workflow and business-effect qualification is represented by the
separate completed `../qualification-f1e6e2f/` evidence. Nothing in this selection promotes unit
test results or a checksum match into proof of that live run.

`post-scanner-pytest.xml` is the later original unit report: **178 tests, 0 failures,
0 errors, 0 skipped**. It follows six additional security-tool regression cases
for exact clean container-manifest proofs and rejection of dirty/forged/ambiguous
variants. It is separate from the frozen 172-test report and predates the later
qualifier correction; it is not a rerun of the native integration.

The six [promoted-evidence scan reports](selected-evidence-scans/README.md) retain
their exact snapshots. [Archive verification](archive-verification.json) also
recomputes all 229 native and 57 earlier-history proofs directly from archive
member bytes, using the portable extraction-path registries. This supplements
the complete member hashes without altering the original expanded scans.
