# Publication regression checks

These checks ran after the clean native integration at `f1e6e2f3800242ec210145680261da8ab60f38b4`. They cover the later qualification-harness and secret-verifier corrections, subsequently committed as `062daaf419b419665729e4c63c1fa6ddfeb7d8d2`, and the integrity of prepared evidence. **They are not a new native service, model, browser or deployment qualification.**

[validation.json](validation.json) records the commands, results and exact SHA-256 values of the four changed implementation/test files while their parent was `f1e6e2f`. It does not falsely identify the modified worktree as the unchanged parent commit.

| Check | Observed result |
| --- | --- |
| Full local unit/boundary suite | **232 passed**, 0 failures, 0 errors, 0 skipped; original [JUnit](pytest.xml) and [console output](pytest.console.txt) retained |
| Qualification-specific subset | 61 synthetic boundary cases, including the seven original closure/cleanup cases retained unchanged; part of the full suite, not 61 additional native integrations |
| Ruff and authored-change whitespace | Passed; [console output](ruff-and-whitespace.console.txt). The staged original Terraform licence retains its upstream whitespace, as explained below. |
| JavaScript syntax | `node --check` passed |
| Contract regeneration | No difference in the versioned JSON contracts |
| Application input comparison | No change since `f1e6e2f` in `src/`, `data/`, `contracts/`, `pyproject.toml` or `uv.lock` |
| Archive integrity | All 192 native originals and 26 earlier histories reread from archives and compared byte-for-byte; [verification](archive-verification.json) |
| Documentation references | 149 relative references in 22 Markdown files checked at the report's recorded time, no missing paths/headings; [scope](documentation-links.json) |

The [prepared-worktree scan](secret-worktree-before-publication.json) retained 31 raw candidates, all independently proved with zero unresolved findings. It describes its recorded staged snapshot, before this report was copied into it. The [code-history scan](secret-code-history.json) covered all four reachable commits through `062daaf`, with 7 raw candidates, 7 proofs and zero unresolved findings. Their original scopes, raw counts and review records remain unchanged. Earlier frozen-source scans and the separate expanded-archive scans are under [security evidence](../security/) and the native/prior-history collections.

The upstream Terraform licence copy contains trailing whitespace on 19 lines. The complete staged `git diff --check` reports those original bytes. They are preserved to keep the artifact identical to its source; the same check passes for all other staged changes when only that exact file is excluded. This is a documented artifact-preservation exception, not a claim that the unfiltered staged check passed or a global whitespace waiver. The exact lines and file hash are in the validation report.

The full native result remains **14/18 selected checks passed, overall failed**, with **agent 2/10 versus runbook 10/10** on the reserved corpus. Local regression success does not change that result or close the target-partitioning, model-value, console and deployment acceptance gaps.
