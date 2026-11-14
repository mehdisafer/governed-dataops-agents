"""Validated environment configuration; no implicit credentials or external inference."""

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from governed_dataops.contracts import Environment, Identifier


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    db_path: str = "state/dataops.sqlite"
    environment: Environment = "dev"
    scope: Identifier = "factory-a"
    demo_mode: bool = False
    target_url: str = "http://127.0.0.1:8081"
    target_timeout_seconds: float = Field(default=10, gt=0, le=120)
    temporal_address: str = "127.0.0.1:7233"
    temporal_namespace: str = "default"
    task_queue: str = "governed-dataops-v1"
    reader_token: str = Field(default="", repr=False)
    executor_token: str = Field(default="", repr=False)
    operator_token: str = Field(default="", repr=False)
    approver_token: str = Field(default="", repr=False)
    reader_subject: Identifier = "dataops-reader"
    executor_subject: Identifier = "dataops-executor"
    operator_subject: Identifier = "dataops-operator"
    approver_subject: Identifier = "dataops-approver"
    approval_signing_key_file: str = ""
    approval_verify_key_file: str = ""
    model_provider: str = "local"
    model_base_url: str = "http://127.0.0.1:8090/v1"
    model_name: str = "governed-qwen"
    model_revision: str = "unconfigured"
    model_api_key: str = Field(default="local-only", repr=False)
    external_llm_authorized: bool = False
    model_timeout_seconds: float = Field(default=90, ge=1, le=180)
    model_max_tokens: int = Field(default=300, ge=32, le=2048)
    model_concurrency: int = Field(default=1, ge=1, le=4)
    worker_concurrency: int = Field(default=4, ge=1, le=16)
    max_pending_incidents: int = Field(default=32, ge=1, le=256)
    approval_timeout_seconds: int = Field(default=300, ge=1, le=3600)

    @model_validator(mode="after")
    def check_boundaries(self):
        if self.model_provider not in {"local", "external"}:
            raise ValueError("model_provider must be local or external")
        parsed = urlsplit(self.model_base_url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("model_base_url must not embed credentials, query or fragment")
        if not parsed.hostname or parsed.scheme not in {"http", "https"}:
            raise ValueError("model_base_url must be an absolute HTTP(S) URL")
        local_hosts = {"localhost", "127.0.0.1", "::1", "model"}
        if self.model_provider == "local" and parsed.hostname not in local_hosts:
            raise ValueError("local model route must use localhost or the model service")
        if self.model_provider == "local" and not self.model_name.startswith("governed-"):
            raise ValueError("local inference requires an explicit governed model alias")
        if self.model_provider == "external" and (
            not self.external_llm_authorized
            or parsed.scheme != "https"
            or self.model_api_key in {"", "local-only"}
        ):
            raise ValueError("external inference requires explicit authorization, HTTPS and key")
        tokens = [getattr(self, f"{r}_token") for r in ("reader", "executor", "operator", "approver")]
        populated = [t for t in tokens if t]
        if any(len(t) < 24 for t in populated):
            raise ValueError("role tokens must contain at least 24 characters")
        if len(populated) != len(set(populated)):
            raise ValueError("role tokens must be distinct")
        subjects = [getattr(self, f"{r}_subject") for r in ("reader", "executor", "operator", "approver")]
        if len(subjects) != len(set(subjects)):
            raise ValueError("role identities must be distinct")
        if not self.environment.strip() or not self.scope.strip():
            raise ValueError("environment and scope are required")
        return self

    def principal(self, role: str):
        from governed_dataops.contracts import Principal

        if role not in {"reader", "executor", "operator", "approver"}:
            raise ValueError("unknown role")
        return Principal(
            subject=getattr(self, f"{role}_subject"),
            role=role,
            environment=self.environment,
            scope=self.scope,
        )


@lru_cache
def get_settings() -> Settings:
    values = {}
    for name in Settings.model_fields:
        key = f"DATAOPS_{name.upper()}"
        if key in os.environ:
            values[name] = os.environ[key]
        if name.endswith("_token") or name == "model_api_key":
            file_key = key + "_FILE"
            if file_key in os.environ:
                if key in os.environ:
                    raise ValueError(f"set either {name} or its file, not both")
                values[name] = Path(os.environ[file_key]).read_text().strip()
    return Settings.model_validate(values)
