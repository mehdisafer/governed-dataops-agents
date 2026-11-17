# Public source and remaining release qualification

**The repository is public according to GitHub (16 November 2026); the candidate is unreleased and not accepted.** [PR #2](https://github.com/mehdisafer/governed-dataops-agents/pull/2) records the implementation review and integration. [Issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) remains open. The maintainer explicitly selected Apache License 2.0 for this repository's original source; the decision is recorded in [LICENSE](../LICENSE). No visibility, billing or paid resource change is implicit in this implementation.

GitHub now reports the intended **public repository state**. The owner retains control of the About, security and protection settings, but no further visibility switch is required. The source, evidence, metadata proposal and review are prepared through the connected repository tools and isolated environment; access to the maintainer's account through a browser is unnecessary. Public visibility and full technical acceptance remain separate: the experimental model label, failed measurements and open requirements must stay visible after publication.

## Post-merge P0 security and partitioning readback — 17 November 2026

GitHub source `main` at
[`9635dbcc`](https://github.com/mehdisafer/governed-dataops-agents/commit/9635dbccfe8cfd168f14ee9380eeb1f03e105a0c)
includes the opt-in target partition router, the cross-partition
SQLite/Ed25519 refusal tests and an evidence-bound model diagnosis guard.
[GitHub Actions run 43988865699](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43988865699)
passed **core 272 tests**, actual governance/Temporal, isolated
containers and infrastructure. The overall run **FAILED**
`model-evaluation`: agent **7/10 strict** against runbook **10/10**,
three wrong proposals were rejected without business effects. The earlier
**2/10** native and **1/10** hosted results remain historical.
CircleCI `build-and-test` and `publication-security` passed on this SHA;
neither constitutes a green model-value gate.

The fixed two-queue reference has actual bounded real Temporal execution
([PR #14](https://github.com/mehdisafer/governed-dataops-agents/pull/14),
[PR #15](https://github.com/mehdisafer/governed-dataops-agents/pull/15)).
**Shared model latency/throughput under saturation**, changed topologies
and multi-host/hostile-tenant behavior remain open. No stable release is
accepted. GitHub still reports `main.protected=false` and zero rulesets;
owner-side protection, independently verified public access and a possible
future experimental tag remain separate.

## Concrete metadata proposal

**Description:** Governed incident response for a synthetic data platform: MCP, PydanticAI and Temporal with signed approvals, idempotent effects and reproducible evidence.

**Topics:** `dataops`, `data-engineering`, `temporal`, `mcp`, `pydantic-ai`, `python`, `observability`, `incident-response`.

**Candidate release identifier:** `v0.1.0a1`, currently unreleased. See [release notes](RELEASE_NOTES.md).

The description and all eight proposed topics were confirmed applied in the repository's GitHub metadata on 2026-11-15. The connected integration cannot change repository administration or visibility settings.

## Evidence and release decision

| Requirement | Retained state | Release consequence |
| --- | --- | --- |
| Exact native source | Clean, unchanged `f1e6e2f3800242ec210145680261da8ab60f38b4`; 192 original run files | Reproducible identity, with the run's failures preserved |
| Native integration | 14/18 requested checks passed; overall run failed | No full acceptance |
| Agent utility | Native 14 Nov agent 2/10, hosted 15 Nov 1/10, and guarded 17 Nov exact-main **7/10**, all versus competent runbook **10/10** | Different sources/host runs and denominators; no agent superiority or experimental label removal |
| Container / infrastructure | Original native attempt was blocked; later CircleCI `reference-containers` passed ten platform checks at `cad9cc6`; infrastructure job passed on `924dd24` | Single-host synthetic platform qualification, not agent quality or production Terraform apply |
| Operator console | Original native Chromium launch failed; later hosted CircleCI governance profile at `924dd24` passed its declared browser gate | Only that tested browser/environment is qualified; no general acceptance implied |
| Hosted CI | [GitHub Actions full run 43919667084](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43919667084): four platform jobs SUCCESS, **model-evaluation FAILED**; [docs-only 43924763001](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43924763001): `core` SUCCESS, runtime jobs SKIPPED. CircleCI unit and publication-security SUCCESS on `351817e` | Platform execution is observed; model utility is a genuine failed acceptance gate, not a runner issue |
| Publication scanning | GitHub Actions `core` on `351817e` reported 31 worktree / 62 history raw reviewed Gitleaks candidates, no unresolved Python licence metadata, and dependency audit with no known vulnerabilities at query time; CircleCI publication-security also SUCCESS | Scanner limitations and independent archive/PR/issue review persist; do not claim a zero-finding or comprehensive certification |
| Review | Automated review is labelled and anchored to the delivered PR revision | Does not substitute for an independent human approval |
| Project licence / repository settings | Source Public; Apache-2.0, wheel metadata, description and eight topics configured; `main.protected=false`, repository rulesets empty | Owner-side protections and any accepted stable release remain outstanding |

The exact source reference in the [qualification ledger](QUALIFICATION.md) and the [evidence index](../evidence/README.md) establish the observed scope. Post-run corrections to evidence verification or evaluation logic have their own regression checks; they do not rewrite the original native result. A green subset, a fixed harness, or a correct checksum cannot establish agent value.

For separated CI provider status, new full-history security gate, and run links, see [CI provenance](CI.md).

## Current CI and publication prerequisites

The original zero-runner failures are retained as historical evidence. GitHub Actions now allocates runners: [run 43919667084](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43919667084) passed four platform profiles but **failed the frozen model evaluation**. The later [docs-only run 43924763001](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43924763001) passed core and skipped runtime profiles. The repository is already public, so no further visibility switch is needed. Continue preserving source-specific logs, scans, original failures and the open evaluation criterion.

## Owner decisions and access limits

The owner explicitly selected **Apache License 2.0** for this repository, committed as [LICENSE](../LICENSE), before public publication. A licence used by another portfolio project or a dependency would not independently authorize this source. The decision does not replace the licences or notices of Python dependencies, Temporal, llama.cpp, Qwen, Terraform, the Docker provider or OCI base images. Component provenance is recorded in [THIRD_PARTY.md](THIRD_PARTY.md).

The GitHub connector can review and modify source, issues and PRs but cannot administer repository visibility or branch protections. The current public repository has no rulesets and reports `main.protected=false`; its classic protection endpoint requires elevated administration rights. Record actual protections after the owner configures them; do not purchase an upgrade or weaken model-value checks.

For an accepted release, protect `main` using the available review and required-check controls, prevent accidental force pushes/deletion, and use the exact observed CI check names. A failed model-quality or utility check is a substantive finding; do not rename or remove it to create a green release badge.

## Post-publication review and separate release decision

Since GitHub already reports the repository **public**, do not repeat the visibility change. Review the delivered commit, reachable Git history, issues, PR comments, original logs, traces, snapshots and artifact retention. Secret-scan findings must be explained or resolved against their actual source, not hidden by compression or broad exclusions. Keep private keys, role tokens, client data and live database files out of distributable evidence.

Verify the reviewed archive against its expanded artifact manifest. Preserve all original failure records and the source hashes used by each run. Verify the committed Apache-2.0 licence and already-applied description/topics, and apply supported protection settings. Reassess unresolved acceptance gates before creating an accepted release. The already-public default branch must preserve the failed results and open acceptance issue; do not claim an accepted release merely because the source is visible.

Verify anonymous access to the already-public repository and evidence links independently from the authenticated GitHub API result. This does not publish the console or any business service; their loopback/private-network exposure remains separate. No independently verified anonymous-access readback or accepted release/tag is claimed; the project remains an unaccepted experimental release candidate. Default-branch integration does not by itself satisfy those gates.
