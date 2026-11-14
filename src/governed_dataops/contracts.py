"""Versioned wire contracts. Untrusted text never selects code or grants privileges."""

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

CONTRACT_VERSION = "1.0"
CATALOG_VERSION = "1.0"
POLICY_VERSION = "1.0"
Environment = Literal["dev", "staging", "prod"]
Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,95}$")]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Scenario(StrEnum):
    FRESHNESS = "freshness"
    TRANSIENT = "transient"
    SCHEMA = "schema"
    QUALITY = "quality"
    DUPLICATE = "duplicate"
    UNKNOWN = "unknown"


class ToolName(StrEnum):
    REFRESH = "refresh_partition"
    RETRY = "retry_batch"
    QUARANTINE = "quarantine_batch"
    SUPPRESS = "suppress_duplicate"
    MIGRATE = "apply_schema_migration"
    ESCALATE = "escalate"


class Principal(Contract):
    subject: Identifier
    role: Literal["operator", "approver", "executor", "reader"]
    environment: Environment = "dev"
    scope: Identifier = "factory-a"


class Incident(Contract):
    contract_version: Literal["1.0"] = "1.0"
    incident_id: Identifier
    event_id: Identifier
    target_id: Identifier
    environment: Environment = "dev"
    scope: Identifier = "factory-a"
    symptom: str = Field(min_length=1, max_length=2000)
    created_at: str = Field(default_factory=utc_now)


class Snapshot(Contract):
    target_id: Identifier
    environment: Environment
    scope: Identifier
    revision: int = Field(ge=0)
    source_schema: int
    accepted_schema: int
    backlog_rows: int = Field(ge=0)
    rejected_rows: int = Field(ge=0)
    curated_rows: int = Field(ge=0)
    duplicate_rows: int = Field(ge=0)
    transient_failure: bool
    freshness_lag_seconds: int = Field(ge=0)
    batch_id: Identifier
    batch_status: Literal["pending", "failed", "rejected", "applied", "quarantined", "suppressed"]
    policy_version: str = POLICY_VERSION


class Evidence(Contract):
    evidence_id: Identifier
    snapshot: Snapshot
    complete: bool
    logs: list[str] = Field(max_length=30)
    collected_at: str = Field(default_factory=utc_now)


class Diagnosis(Contract):
    category: Scenario
    summary: str = Field(min_length=1, max_length=2000)
    evidence_refs: list[str] = Field(min_length=1, max_length=10)
    proposed_action: ToolName
    rationale: str = Field(min_length=1, max_length=2000)


class Action(Contract):
    tool: ToolName


class Plan(Contract):
    contract_version: Literal["1.0"] = "1.0"
    catalog_version: str = CATALOG_VERSION
    policy_version: str = POLICY_VERSION
    incident_id: Identifier
    target_id: Identifier
    environment: Environment
    scope: Identifier
    evidence_id: Identifier
    expected_revision: int = Field(ge=0)
    actions: list[Action] = Field(min_length=1, max_length=3)
    action_budget: int = Field(default=1, ge=1, le=3)
    delegation_depth: int = Field(default=0, ge=0, le=8)
    rationale: str = Field(max_length=2000)

    def digest(self) -> str:
        canonical = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


class Approval(Contract):
    plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    incident_id: Identifier
    target_id: Identifier
    environment: Environment
    scope: Identifier
    expected_revision: int
    policy_version: str
    approver: Principal
    issued_at: str
    expires_at: str
    signature: str = Field(default="", max_length=256)


class PolicyDecision(Contract):
    allowed: bool
    approval_required: bool = False
    reasons: list[str]


class EffectRequest(Contract):
    idempotency_key: str = Field(pattern=r"^[a-f0-9]{64}$")
    plan: Plan
    action_index: int = Field(ge=0, le=2)
    executor: Principal
    approval: Approval | None = None
    simulate_lost_response: bool = False


class EffectResult(Contract):
    idempotency_key: str
    status: Literal["applied", "denied", "unknown", "not_found"]
    message: str
    before_revision: int | None = None
    after_revision: int | None = None
    snapshot: Snapshot | None = None
    reconciled: bool = False


class Verification(Contract):
    resolved: bool
    outcome: Literal["resolved", "contained", "escalated", "denied", "cancelled"]
    reasons: list[str]
    snapshot: Snapshot | None = None


class RunResult(Contract):
    incident_id: str
    status: Literal["resolved", "contained", "escalated", "denied", "cancelled"]
    reason: str
    plan_hash: str | None = None
    verification: Verification | None = None


def effect_key(plan: Plan, action_index: int) -> str:
    return hashlib.sha256(f"{plan.incident_id}:{plan.digest()}:{action_index}".encode()).hexdigest()


def build_plan(incident: Incident, evidence: Evidence, diagnosis: Diagnosis) -> Plan:
    if evidence.evidence_id not in diagnosis.evidence_refs:
        raise ValueError("diagnosis does not cite the collected evidence")
    if (incident.target_id, incident.environment, incident.scope) != (
        evidence.snapshot.target_id,
        evidence.snapshot.environment,
        evidence.snapshot.scope,
    ):
        raise ValueError("evidence target does not match the incident")
    return Plan(
        incident_id=incident.incident_id,
        target_id=incident.target_id,
        environment=incident.environment,
        scope=incident.scope,
        evidence_id=evidence.evidence_id,
        expected_revision=evidence.snapshot.revision,
        policy_version=evidence.snapshot.policy_version,
        actions=[Action(tool=diagnosis.proposed_action)],
        rationale=diagnosis.rationale,
    )
