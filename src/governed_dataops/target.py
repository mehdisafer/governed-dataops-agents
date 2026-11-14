"""Real synthetic target HTTP service with scoped reads and fixed mutation handlers."""

import secrets
import sqlite3
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import Field

from governed_dataops.contracts import (
    Contract,
    EffectRequest,
    EffectResult,
    Environment,
    Evidence,
    Identifier,
    Principal,
    Scenario,
    Snapshot,
)
from governed_dataops.settings import Settings, get_settings
from governed_dataops.storage import Store


class SeedRequest(Contract):
    target_id: Identifier
    scenario: Scenario
    environment: Environment = "dev"
    scope: Identifier = "factory-a"
    inject_log: bool = False
    variant: int = Field(default=0, ge=0, le=9)


def create_target_app(store: Store | None = None, settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()
    database = store or Store(
        config.db_path, approval_verify_key_file=config.approval_verify_key_file
    )
    app = FastAPI(title="Synthetic industrial data target", version="0.1.0")
    app.state.store = database

    def authenticate(authorization: Annotated[str | None, Header()] = None) -> Principal:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "A role token is required")
        value = authorization[7:].encode("utf-8")
        for role in ("executor", "reader", "operator", "approver"):
            token = getattr(config, f"{role}_token")
            if token and secrets.compare_digest(value, token.encode("utf-8")):
                return config.principal(role)
        raise HTTPException(401, "Invalid role token")

    @app.exception_handler(KeyError)
    async def missing(_request: Request, _exc: KeyError):
        return JSONResponse(status_code=404, content={"detail": "Target not found"})

    @app.exception_handler(PermissionError)
    async def forbidden(_request: Request, _exc: PermissionError):
        return JSONResponse(status_code=403, content={"detail": "Target scope is not authorized"})

    @app.exception_handler(sqlite3.OperationalError)
    async def backpressure(_request: Request, _exc: sqlite3.OperationalError):
        return JSONResponse(
            status_code=503,
            content={"detail": "Target storage is unavailable; reconcile before retry"},
            headers={"Retry-After": "1"},
        )

    @app.get("/health")
    def health():
        try:
            return {"target": "synthetic", **database.health()}
        except (sqlite3.Error, OSError, RuntimeError):
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unavailable",
                    "target": "synthetic",
                    "persistence": "unavailable",
                },
                headers={"Retry-After": "1"},
            )

    @app.post("/seed", response_model=Snapshot)
    def seed(body: SeedRequest, principal: Annotated[Principal, Depends(authenticate)]):
        if principal.role != "operator" or not config.demo_mode or config.environment != "dev":
            raise HTTPException(403, "Fixture seeding requires a dev demo operator")
        if (body.environment, body.scope) != (principal.environment, principal.scope):
            raise HTTPException(403, "Fixture is outside the operator scope")
        try:
            return database.seed_target(
                body.target_id,
                body.scenario,
                body.environment,
                body.scope,
                body.inject_log,
                body.variant,
            )
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/targets/{target_id}", response_model=Evidence)
    def observe(target_id: str, principal: Annotated[Principal, Depends(authenticate)]):
        return database.observe(target_id, principal)

    @app.post("/effects", response_model=EffectResult)
    def effect(body: EffectRequest, principal: Annotated[Principal, Depends(authenticate)]):
        if principal.role != "executor" or body.executor != principal:
            raise HTTPException(403, "An executor token must match the submitted executor identity")
        if body.simulate_lost_response and not config.demo_mode:
            raise HTTPException(403, "Response-loss fault injection requires demo mode")
        result = database.apply(body)
        if body.simulate_lost_response and result.status == "applied" and not result.reconciled:
            return JSONResponse(status_code=503, content={"detail": "Effect response unavailable"})
        return result

    @app.get("/effects/{key}", response_model=EffectResult)
    def reconcile(key: str, target_id: str, principal: Annotated[Principal, Depends(authenticate)]):
        return database.reconcile(key, target_id, principal)

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_target_app(), host="127.0.0.1", port=8081)
