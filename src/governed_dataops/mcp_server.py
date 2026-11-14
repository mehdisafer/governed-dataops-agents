"""Real MCP boundary exposing only three fixed synthetic-target operations."""

import re

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import TypeAdapter

from governed_dataops.contracts import EffectRequest, EffectResult, Evidence, Identifier
from governed_dataops.settings import get_settings

server = MCPServer("governed-dataops", version="1.0.0", log_level="WARNING")
_identifier = TypeAdapter(Identifier)


def _client(role: str) -> httpx.AsyncClient:
    settings = get_settings()
    token = getattr(settings, f"{role}_token")
    if not token:
        raise ToolError(f"{role} credential is not configured")
    return httpx.AsyncClient(
        base_url=settings.target_url.rstrip("/"),
        headers={"Authorization": f"Bearer {token}"},
        timeout=settings.target_timeout_seconds,
        follow_redirects=False,
        trust_env=False,
    )


@server.tool()
async def collect_evidence(target_id: str) -> Evidence:
    """Read a typed observation for one authorized target."""
    target_id = _identifier.validate_python(target_id)
    try:
        async with _client("reader") as client:
            response = await client.get(f"/targets/{target_id}")
            response.raise_for_status()
            evidence = Evidence.model_validate(response.json())
    except (httpx.HTTPError, ValueError) as exc:
        raise ToolError(f"evidence collection failed ({type(exc).__name__})") from None
    if evidence.snapshot.target_id != target_id:
        raise ToolError("target returned evidence for a different target")
    return evidence


@server.tool()
async def execute_action(request: dict) -> EffectResult:
    """Submit one catalog action; the target independently enforces authorization."""
    effect = EffectRequest.model_validate(request)
    try:
        async with _client("executor") as client:
            response = await client.post("/effects", json=effect.model_dump(mode="json"))
    except httpx.HTTPError as exc:
        return EffectResult(
            idempotency_key=effect.idempotency_key,
            status="unknown",
            message=f"target response unavailable ({type(exc).__name__}); reconcile before retry",
        )
    if response.status_code >= 500:
        return EffectResult(
            idempotency_key=effect.idempotency_key,
            status="unknown",
            message=f"target returned HTTP {response.status_code}; effect may already be committed",
        )
    if response.status_code in {401, 403, 409, 422}:
        return EffectResult(
            idempotency_key=effect.idempotency_key,
            status="denied",
            message=f"target denied request (HTTP {response.status_code})",
        )
    try:
        response.raise_for_status()
        result = EffectResult.model_validate(response.json())
    except (httpx.HTTPError, ValueError):
        return EffectResult(
            idempotency_key=effect.idempotency_key,
            status="unknown",
            message="target returned an incomplete or invalid effect result; reconcile before retry",
        )
    if result.idempotency_key != effect.idempotency_key:
        return EffectResult(
            idempotency_key=effect.idempotency_key,
            status="unknown",
            message="target returned another operation key; reconciliation is required",
        )
    return result


@server.tool()
async def reconcile_effect(key: str, target_id: str) -> EffectResult:
    """Read the durable effect journal without repeating a mutation."""
    target_id = _identifier.validate_python(target_id)
    if not re.fullmatch(r"[a-f0-9]{64}", key):
        raise ToolError("invalid operation key")
    try:
        async with _client("executor") as client:
            response = await client.get(f"/effects/{key}", params={"target_id": target_id})
        if response.status_code == 404:
            return EffectResult(
                idempotency_key=key,
                status="not_found",
                message="target journal has no completed effect for this key",
                reconciled=True,
            )
        response.raise_for_status()
        result = EffectResult.model_validate(response.json())
        if result.idempotency_key != key:
            raise ValueError("mismatched operation key")
        if result.snapshot is not None and result.snapshot.target_id != target_id:
            raise ValueError("mismatched target")
        return result.model_copy(update={"reconciled": True})
    except (httpx.HTTPError, ValueError):
        return EffectResult(
            idempotency_key=key,
            status="unknown",
            message="target journal could not establish the operation outcome",
            reconciled=True,
        )


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
