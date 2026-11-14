"""Bounded official MCP v2 client; each call crosses a real stdio process."""

import sys
from pathlib import Path

from mcp import Client, StdioServerParameters
from pydantic import ValidationError

from governed_dataops.contracts import EffectRequest, EffectResult, Evidence
from governed_dataops.settings import Settings, get_settings


class MCPBoundaryError(RuntimeError):
    """The MCP response is absent, erroneous, or violates the wire contract."""


class MCPGateway:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _parameters(self) -> StdioServerParameters:
        settings = self.settings
        # No model key, approval key, operator token or arbitrary launch string.
        env = {
            "PYTHONPATH": str(Path(__file__).resolve().parent.parent),
            "DATAOPS_TARGET_URL": settings.target_url,
            "DATAOPS_TARGET_TIMEOUT_SECONDS": str(settings.target_timeout_seconds),
            "DATAOPS_READER_TOKEN": settings.reader_token,
            "DATAOPS_EXECUTOR_TOKEN": settings.executor_token,
        }
        return StdioServerParameters(
            command=sys.executable, args=["-m", "governed_dataops.mcp_server"], env=env
        )

    async def _call(self, tool: str, arguments: dict) -> dict:
        try:
            async with Client(
                self._parameters(), read_timeout_seconds=self.settings.target_timeout_seconds + 10
            ) as client:
                result = await client.call_tool(tool, arguments)
        except Exception as exc:
            raise MCPBoundaryError(f"MCP {tool} failed ({type(exc).__name__})") from None
        if result.is_error or not isinstance(result.structured_content, dict):
            raise MCPBoundaryError(f"MCP {tool} returned an error or incomplete structured result")
        return result.structured_content

    async def collect(self, target_id: str) -> Evidence:
        try:
            evidence = Evidence.model_validate(
                await self._call("collect_evidence", {"target_id": target_id})
            )
        except ValidationError:
            raise MCPBoundaryError("MCP evidence contract is invalid") from None
        if evidence.snapshot.target_id != target_id:
            raise MCPBoundaryError("MCP evidence belongs to another target")
        return evidence

    async def execute(self, request: EffectRequest) -> EffectResult:
        try:
            result = EffectResult.model_validate(
                await self._call("execute_action", {"request": request.model_dump(mode="json")})
            )
            if result.idempotency_key != request.idempotency_key:
                raise MCPBoundaryError("MCP execution returned another operation key")
            return result
        except (MCPBoundaryError, ValidationError):
            return EffectResult(
                idempotency_key=request.idempotency_key,
                status="unknown",
                message="MCP execution outcome is uncertain; target reconciliation is required",
            )

    async def reconcile(self, key: str, target_id: str) -> EffectResult:
        try:
            result = EffectResult.model_validate(
                await self._call("reconcile_effect", {"key": key, "target_id": target_id})
            )
            if result.idempotency_key != key:
                raise MCPBoundaryError("MCP reconciliation returned another operation key")
            if result.snapshot is not None and result.snapshot.target_id != target_id:
                raise MCPBoundaryError("MCP reconciliation returned another target")
            return result
        except (MCPBoundaryError, ValidationError):
            return EffectResult(
                idempotency_key=key,
                status="unknown",
                message="MCP could not establish the durable target outcome",
                reconciled=True,
            )
