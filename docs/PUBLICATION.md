# Publication preparation

**The candidate is private, unreleased and not accepted.** [PR #2](https://github.com/mehdisafer/governed-dataops-agents/pull/2) records the implementation review and integration. [Issue #1](https://github.com/mehdisafer/governed-dataops-agents/issues/1) remains open. The maintainer explicitly selected Apache License 2.0 for this repository's original source; the decision is recorded in [LICENSE](../LICENSE). No visibility, billing or paid resource change is implicit in this implementation.

The maintainer's intended next destination is a **public repository** and the maintainer will handle the required GitHub interface operations. The source, evidence, metadata proposal and review are prepared through the connected repository tools and isolated environment; access to the maintainer's account through a browser is unnecessary. Public visibility and full technical acceptance remain separate: the experimental model label, failed measurements and open requirements must stay visible after publication.

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
| Agent utility | Original 14 Nov agent 2/10 vs runbook 10/10; later hosted frozen agent 1/10 vs runbook 10/10 | Experimental model; no superiority claim |
| Container / infrastructure | Original native attempt was blocked; later CircleCI `reference-containers` passed ten platform checks at `cad9cc6`; infrastructure job passed on `924dd24` | Single-host synthetic platform qualification, not agent quality or production Terraform apply |
| Operator console | Original native Chromium launch failed; later hosted CircleCI governance profile at `924dd24` passed its declared browser gate | Only that tested browser/environment is qualified; no general acceptance implied |
| Hosted CI | CircleCI unit passed on `main` at `2460012`, platform containers passed at `cad9cc6`, and hosted frozen model evaluation failed at `924dd24`. GitHub Actions run 43769325453 still failed before runner assignment | Distinct CI providers, source identities and scopes; full agent-value acceptance withheld |
| Publication scanning | Historical expanded archives have content-bound reviews; GitHub reports the new CircleCI `publication-security` job **successful** at PR source `10f1510` (16 Nov 2026), distinct from final `main` | Inspect retained refs, findings, component inventory and dependency-audit artifacts; recheck final `main` before public visibility; a green status alone is insufficient |
| Review | Automated review is labelled and anchored to the delivered PR revision | Does not substitute for an independent human approval |
| Project licence / repository settings | Apache License 2.0 explicitly selected and committed; description and topics applied; visibility remains private | Owner still controls visibility and supported protection settings |

The exact source reference in the [qualification ledger](QUALIFICATION.md) and the [evidence index](../evidence/README.md) establish the observed scope. Post-run corrections to evidence verification or evaluation logic have their own regression checks; they do not rewrite the original native result. A green subset, a fixed harness, or a correct checksum cannot establish agent value.

For separated CI provider status, new full-history security gate, and run links, see [CI provenance](CI.md).

## Precise CI prerequisite

Inspect the annotation on [the latest failed main core job](https://github.com/mehdisafer/governed-dataops-agents/actions/runs/43769325453/job/132981467752) in the owner's authenticated GitHub session. The original two attempts and subsequent PR and main runs report runner ID zero, no runner name and no executed steps in core. Log retrieval returned 404, and the connected API did not expose the annotation endpoint. The isolated cloud-browser session was logged out. The [original API observations](../evidence/github-actions-43597256488/) preserve these limitations.

The cause must be established before changing account settings or selecting another runner. No billing diagnosis, purchase, visibility workaround or third blind retry is justified by these records. Once an authorized runner is available, execute the existing `core`, `governance`, `model-evaluation`, `containers` and `infrastructure` jobs and retain the resulting source identity and artifacts. A newly triggered run requires its own inspection; its existence is not successful qualification.

## Owner decisions and access limits

The owner explicitly selected **Apache License 2.0** for this repository, committed as [LICENSE](../LICENSE), before public publication. A licence used by another portfolio project or a dependency would not independently authorize this source. The decision does not replace the licences or notices of Python dependencies, Temporal, llama.cpp, Qwen, Terraform, the Docker provider or OCI base images. Component provenance is recorded in [THIRD_PARTY.md](THIRD_PARTY.md).

The connected repository integration can read/write source, issues and pull requests but does not expose repository metadata/visibility administration. Initial inspection of branch protections returned an integration-permission error; ruleset inspection additionally reported the private-plan availability restriction. Do not purchase an upgrade or make the repository public as a workaround. Record the protections actually available when the owner performs the administration step.

For an accepted release, protect `main` using the available review and required-check controls, prevent accidental force pushes/deletion, and use the exact observed CI check names. A failed model-quality or utility check is a substantive finding; do not rename or remove it to create a green release badge.

## Authorized public-release procedure

Before an explicitly authorized public switch, review the delivered commit, reachable Git history, issues, PR comments, original logs, traces, snapshots and artifact retention. Secret-scan findings must be explained or resolved against their actual source, not hidden by compression or broad exclusions. Keep private keys, role tokens, client data and live database files out of distributable evidence.

Verify the reviewed archive against its expanded artifact manifest. Preserve all original failure records and the source hashes used by each run. Verify the committed Apache-2.0 licence and already-applied description/topics, and apply supported protection settings. Reassess unresolved acceptance gates before creating an accepted release. Integrating the reviewed experimental implementation into the default branch prepares the public repository; it must keep the failed results and open acceptance issue visible.

After an authorized visibility change, verify anonymous access to the intended repository and evidence links. This does not publish the console or any business service; their loopback/private-network exposure remains separate. No anonymous-access verification or accepted release/tag is claimed while the current candidate remains private and unaccepted. Default-branch integration does not by itself satisfy those gates.
