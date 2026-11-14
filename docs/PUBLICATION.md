# Publication preparation

The repository is private. Its own licence has not been selected. No visibility, billing, paid resource or licence change is implicit in this implementation.

## Concrete metadata proposal

**Description:** Governed incident response for a synthetic data platform: MCP, PydanticAI and Temporal with signed approvals, idempotent effects and reproducible evidence.

**Topics:** `dataops`, `data-engineering`, `temporal`, `mcp`, `pydantic-ai`, `python`, `observability`, `incident-response`.

**Candidate release identifier:** `v0.1.0a1`, currently unreleased. See [release notes](RELEASE_NOTES.md).

## Owner decisions and access limits

The owner must explicitly select a repository licence before public publication. This choice does not replace the licences or notices of Python dependencies, Temporal, llama.cpp, Qwen, Terraform, the Docker provider or OCI base images. Component rights and provenance are recorded in [THIRD_PARTY.md](THIRD_PARTY.md).

The connected repository integration can read/write source, issues and pull requests but does not expose repository metadata/visibility administration. Initial inspection of branch protections returned an integration-permission error; ruleset inspection additionally reported the private-plan availability restriction. Do not purchase an upgrade or make the repository public as a workaround. Record the actual available protections when the owner performs the administration step.

For an accepted release, protect `main` using the available review and required-check controls, prevent accidental force pushes/deletion, and use the exact observed CI check names. A failed model-quality or utility check is a substantive finding; do not rename or remove it to create a green release badge.

Before an explicitly authorized public switch, review the delivered commit, reachable Git history, issues, PR comments, original logs, traces, snapshots and artifact retention. Secret-scan findings must be explained or resolved against their actual source, not hidden by compression or broad exclusions. Do not upload private keys, role tokens, client data or live database files.

After an authorized visibility change, verify anonymous access to the intended repository and evidence links. This does not publish the console or any business service; their loopback/private-network exposure remains separate. No anonymous-access verification is claimed while the repository is private.
