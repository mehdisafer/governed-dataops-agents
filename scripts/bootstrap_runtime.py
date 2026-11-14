#!/usr/bin/env python3
"""Fetch pinned Linux amd64 runtimes and model assets; verify bytes before use.

This installs isolated demonstration assets, not a system service. It never starts
services, installs global packages, fetches credentials or provisions paid resources.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import tarfile
import tempfile
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

TEMPORAL = {
    "name": "temporal_cli_1.10.1_linux_amd64.tar.gz",
    "url": "https://github.com/temporalio/cli/releases/download/v1.10.1/temporal_cli_1.10.1_linux_amd64.tar.gz",
    "sha256": "4c1500e2ce2d4de136e5fe8852d9b7f82eb62f19b6b383b3e0c040519a9d20b1",
    "bytes": 38357804,
    "licence": "MIT",
    "version": "1.10.1",
}
LLAMA = {
    "name": "llama-b12368-bin-ubuntu-x64.tar.gz",
    "url": "https://github.com/ggml-org/llama.cpp/releases/download/b12368/llama-b12368-bin-ubuntu-x64.tar.gz",
    "sha256": "4162c124bf89feb9096bd69689d69afc303473b6024db6e0e8c41cbd53f52ab4",
    "bytes": 23332342,
    "licence": "MIT",
    "version": "b12368",
}
MODEL = {
    "name": "Qwen3-4B-Instruct-2507-Q2_K.gguf",
    "url": "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/"
    "a06e946bb6b655725eafa393f4a9745d460374c9/Qwen3-4B-Instruct-2507-Q2_K.gguf",
    "sha256": "f7ed2f57713ad29e1a4ec093be0cdf3d7fd31e137e8fd4fc3edcfd04a5267862",
    "bytes": 1669500000,
    "licence": "Apache-2.0",
    "revision": "a06e946bb6b655725eafa393f4a9745d460374c9",
    "quantization": "Q2_K",
    "quantizer": "Unsloth (community quantization)",
    "base_model": "Qwen/Qwen3-4B-Instruct-2507",
    "base_model_revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
}
MODEL_LICENCE = {
    "name": "qwen3-4b.LICENSE",
    "url": "https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/resolve/"
    "cdbee75f17c01a7cc42f958dc650907174af0554/LICENSE",
    "sha256": "832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e",
    "bytes": 11343,
    "licence": "Apache-2.0",
}
MODEL_SOURCE_CARDS = [
    {
        "name": "qwen3-4b-quantizer-README.md",
        "url": "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/"
        "a06e946bb6b655725eafa393f4a9745d460374c9/README.md",
        "sha256": "c18c2d01645e709fcc0bfd593291d3dc43e51873f5af170a082c36ccd95988c3",
        "bytes": 11207,
    },
    {
        "name": "qwen3-4b-base-README.md",
        "url": "https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/resolve/"
        "cdbee75f17c01a7cc42f958dc650907174af0554/README.md",
        "sha256": "8e3dd0c3b5b11897cc71092ccfe517bb7a9783479baa3665aad73c8d1a2041cd",
        "bytes": 8168,
    },
]


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def verify(path: Path, asset: dict) -> None:
    if path.stat().st_size != asset["bytes"] or digest(path) != asset["sha256"]:
        raise RuntimeError(f"Asset failed size/SHA-256 verification: {path}")


def download(asset: dict, cache: Path) -> Path:
    destination = cache / asset["name"]
    if destination.exists():
        verify(destination, asset)
        print(f"Verified cached asset: {asset['name']}", flush=True)
        return destination
    descriptor, temporary = tempfile.mkstemp(prefix="download-", suffix=".part", dir=cache)
    try:
        print(f"Downloading: {asset['name']}", flush=True)
        with (
            os.fdopen(descriptor, "wb") as output,
            urllib.request.urlopen(asset["url"], timeout=60) as response,
        ):
            shutil.copyfileobj(response, output, length=1024 * 1024)
        candidate = Path(temporary)
        verify(candidate, asset)
        candidate.replace(destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
    print(f"Downloaded and verified: {asset['name']}", flush=True)
    return destination


def extract(archive: Path, destination: Path) -> None:
    """Reject drift in an existing extraction; never silently replace local files."""
    if destination.exists():
        with tarfile.open(archive) as source:
            for member in source.getmembers():
                target = destination / member.name
                if member.isfile():
                    expected = source.extractfile(member)
                    if expected is None or not target.is_file():
                        raise RuntimeError(f"Incomplete extraction: {target}")
                    if hashlib.file_digest(expected, "sha256").hexdigest() != digest(target):
                        raise RuntimeError(f"Existing extracted file changed: {target}")
                elif member.issym() and (
                    not target.is_symlink() or os.readlink(target) != member.linkname
                ):
                    raise RuntimeError(f"Existing extracted link changed: {target}")
        return
    staging = Path(tempfile.mkdtemp(prefix="extract-", dir=destination.parent))
    try:
        with tarfile.open(archive) as source:
            source.extractall(staging, filter="data")
        staging.replace(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def install_asset(source: Path, destination: Path, asset: dict) -> None:
    """Keep one immutable copy when the cache and installation share a filesystem."""
    if destination.exists():
        verify(destination, asset)
        return
    try:
        os.link(source, destination)
    except OSError:
        with source.open("rb") as original, destination.open("xb") as installed:
            shutil.copyfileobj(original, installed, length=1024 * 1024)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=Path("var/runtime"))
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--component", choices=["all", "temporal", "model"], default="all")
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
        parser.error("This pinned reference runtime supports Linux amd64 only")
    destination = args.destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    cache = args.cache.resolve() if args.cache else destination / "downloads"
    cache.mkdir(parents=True, exist_ok=True)
    assets, services = [], {}
    if args.component in {"all", "temporal"}:
        extract(download(TEMPORAL, cache), destination / "temporal")
        assets.append(TEMPORAL)
        services["temporal"] = {
            "command": [
                str(destination / "temporal/temporal"),
                "server",
                "start-dev",
                "--ip",
                "127.0.0.1",
                "--port",
                "7233",
                "--ui-ip",
                "127.0.0.1",
                "--ui-port",
                "8233",
                "--ui-disable-news-fetch",
                "--metrics-port",
                "8234",
                "--db-filename",
                str(destination / "temporal.db"),
            ]
        }
    if args.component in {"all", "model"}:
        extract(download(LLAMA, cache), destination / "llama")
        target = destination / MODEL["name"]
        install_asset(download(MODEL, cache), target, MODEL)
        install_asset(download(MODEL_LICENCE, cache), destination / "QWEN-LICENSE", MODEL_LICENCE)
        for card in MODEL_SOURCE_CARDS:
            install_asset(download(card, cache), destination / card["name"], card)
        # Qualification records identify the selected model by the final asset.
        assets.extend([LLAMA, MODEL_LICENCE, *MODEL_SOURCE_CARDS, MODEL])
        services["model"] = {
            "command": [
                str(destination / "llama/llama-b12368/llama-server"),
                "--model",
                str(target),
                "--host",
                "127.0.0.1",
                "--port",
                "8090",
                "--alias",
                "governed-qwen",
                "--threads",
                "4",
                "--threads-batch",
                "4",
                "--threads-http",
                "4",
                "--ctx-size",
                "2048",
                "--parallel",
                "1",
                "--gpu-layers",
                "0",
                "--metrics",
                "--no-webui",
                "--no-agent",
                "--jinja",
                "--n-predict",
                "768",
                "--batch-size",
                "128",
                "--ubatch-size",
                "64",
                "--cache-type-k",
                "q8_0",
                "--cache-type-v",
                "q8_0",
                "--flash-attn",
                "on",
                "--no-repack",
                "--cache-ram",
                "0",
                "--ctx-checkpoints",
                "0",
            ]
        }
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "assets": assets,
        "services": services,
        "services_running": False,
        "execution_status": "downloaded; not executed by bootstrap",
        "model_qualification_status": "experimental; integrity is not diagnostic qualification",
        "platform": "linux/amd64",
        "model_repo_revision": MODEL["revision"],
        "recommended_environment": {
            "DATAOPS_MODEL_PROVIDER": "local",
            "DATAOPS_MODEL_BASE_URL": "http://127.0.0.1:8090/v1",
            "DATAOPS_MODEL_NAME": "governed-qwen",
            "DATAOPS_MODEL_REVISION": "sha256:" + MODEL["sha256"],
            "DATAOPS_MODEL_MAX_TOKENS": "300",
            "DATAOPS_MODEL_TIMEOUT_SECONDS": "90",
            "DATAOPS_MODEL_CONCURRENCY": "1",
        },
        "licence_sources": {
            "Temporal": "https://github.com/temporalio/cli/blob/v1.10.1/LICENSE",
            "llama.cpp": "https://github.com/ggml-org/llama.cpp/blob/b12368/LICENSE",
            "Qwen": "https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/"
            "cdbee75f17c01a7cc42f958dc650907174af0554/LICENSE",
        },
    }
    (destination / "provisioning.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Runtime manifest: {destination / 'provisioning.json'}", flush=True)


if __name__ == "__main__":
    main()
