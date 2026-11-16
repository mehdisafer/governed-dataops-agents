# Third-party provenance and licences

This file identifies the pinned components used by the reference implementation.
The exact Python dependency graph and distribution hashes are in `uv.lock`.
`scripts/component_inventory.py` records the environment actually installed,
package licence metadata and licence-file checksums. These are provenance records,
not a legal compatibility opinion or a security certification.

The maintainer explicitly selected [Apache License 2.0](../LICENSE) for this
repository's original source.
The distributable Python project also declares the SPDX expression and the
exact `LICENSE` file under PEP 639. A separate CI wheel check inspects the
built package metadata and embedded licence bytes before distribution. Third-party components, dependencies and model
weights remain governed by their own licences and notices; do not infer those
rights from the project's licence or its eventual public visibility.

## Application dependencies

The declarations below were checked against the installed distribution metadata
on **2026-11-14**. Versioned PyPI pages identify the corresponding distributions;
their metadata links to the upstream project and source. Preserve the actual
third-party licence/notice files when distributing dependency artifacts.

| Component | Pin | Declared licence | Primary provenance |
| --- | --- | --- | --- |
| MCP Python SDK | `mcp==2.3.0` | MIT | [PyPI](https://pypi.org/project/mcp/2.3.0/), [upstream](https://github.com/modelcontextprotocol/python-sdk) |
| Pydantic AI slim, OpenAI extra | `pydantic-ai-slim==2.68.0` | MIT | [PyPI](https://pypi.org/project/pydantic-ai-slim/2.68.0/), [upstream](https://github.com/pydantic/pydantic-ai) |
| Temporal Python SDK, Pydantic extra | `temporalio==1.36.0` | MIT | [PyPI](https://pypi.org/project/temporalio/1.36.0/), [upstream](https://github.com/temporalio/sdk-python) |
| Pydantic | `2.14.3` | MIT | [PyPI](https://pypi.org/project/pydantic/2.14.3/) |
| FastAPI | `0.141.1` | MIT | [PyPI](https://pypi.org/project/fastapi/0.141.1/) |
| Uvicorn | `0.52.1` | BSD-3-Clause | [PyPI](https://pypi.org/project/uvicorn/0.52.1/) |
| HTTPX | `0.28.1` | BSD-3-Clause | [PyPI](https://pypi.org/project/httpx/0.28.1/) |
| HTTPX2 | `2.16.0` | BSD-3-Clause | [PyPI](https://pypi.org/project/httpx2/2.16.0/) |
| OpenAI Python client | `3.51.0` | Apache-2.0 | [PyPI](https://pypi.org/project/openai/3.51.0/) |
| cryptography | `50.0.2` | Apache-2.0 OR BSD-3-Clause | [PyPI](https://pypi.org/project/cryptography/50.0.2/) |

The OpenAI-compatible client is used with a local model route by default.
Installing it does not authorize sending data to an external provider. The
separate application setting and endpoint checks control that decision.

The development group pins pytest `9.2.0`, pytest-asyncio `1.5.0`, Ruff `0.17.5`
and Playwright `1.62.0`. The installed inventory contains their declarations and
the transitive packages. The first reconstruction inventory contained **61
installed distributions**, **64 lock entries**, and one unresolved licence
metadata entry: this project itself. Those counts describe that dated run;
regenerate the inventory when the environment changes. Platform-conditional lock
entries need not all be installed on Linux.

## Local model and runtime

`scripts/bootstrap_runtime.py` pins archive or model bytes, repository revisions,
sizes and checksums before installation. Its manifest records download/integrity
state; only a separate live qualification run can demonstrate successful service
execution and model behaviour. The following sources were selected for the
reference runtime; availability and successful download are recorded per run.

| Component | Selected pin | Licence/source |
| --- | --- | --- |
| Temporal CLI development server | `1.10.1`, Linux amd64 archive | MIT; [release](https://github.com/temporalio/cli/releases/tag/v1.10.1), [licence](https://github.com/temporalio/cli/blob/v1.10.1/LICENSE) |
| llama.cpp server | `b12368`, Ubuntu x64 archive | MIT; [release](https://github.com/ggml-org/llama.cpp/releases/tag/b12368), [licence](https://github.com/ggml-org/llama.cpp/blob/b12368/LICENSE) |
| Qwen base model | `Qwen/Qwen3-4B-Instruct-2507`, revision `cdbee75f17c01a7cc42f958dc650907174af0554` | Apache-2.0; [pinned licence](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/cdbee75f17c01a7cc42f958dc650907174af0554/LICENSE) |
| Community GGUF quantization | `unsloth/Qwen3-4B-Instruct-2507-GGUF`, revision `a06e946bb6b655725eafa393f4a9745d460374c9`, `Q2_K` | [Pinned quantizer model card](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/blob/a06e946bb6b655725eafa393f4a9745d460374c9/README.md); derived from the model above |

The selected GGUF is `Qwen3-4B-Instruct-2507-Q2_K.gguf`, SHA-256
`f7ed2f57713ad29e1a4ec093be0cdf3d7fd31e137e8fd4fc3edcfd04a5267862`.
The community quantization is a separate artifact from the upstream model
weights. Integrity of that artifact does not establish diagnostic accuracy,
resistance to prompt injection, or suitability for a real industrial system.
The bootstrap retains the upstream model licence and the base/quantizer model
cards alongside the local runtime artifacts.

The model's Apache licence and the runtime licences do not describe every native
library, operating-system package or OCI layer included in a built image. Those
layers need their own inventory and audit before redistribution or deployment
outside this isolated demonstration. Container/runtime verification status is
reported in the deployment and qualification documents, rather than inferred
from the presence of Dockerfiles.

## Security tools

Gitleaks `8.30.1` is MIT-licensed; the scanner verifies its bundled licence, version
and archive checksum from the [official release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1).
Its Linux x64 archive SHA-256 is
`551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb`.
The checksum-manifest SHA-256 is
`061476c21adaf5441516f96f185c1a4706a83cd6329b9b38762271b3d4a52fae`.

The isolated vulnerability audit uses [pip-audit `2.10.1`](https://pypi.org/project/pip-audit/2.10.1/),
licensed Apache-2.0 by the [PyPA project](https://github.com/pypa/pip-audit).
Audit results are tied to an input file, dependency lock and execution date. They
do not cover model semantics or all native/operating-system components. See
[SECURITY.md](SECURITY.md) for commands, coverage limits and reporting guidance.
