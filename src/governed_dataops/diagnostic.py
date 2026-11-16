"""PydanticAI diagnostics with no tools and no automatic provider fallback."""

import hashlib
import json
import re
import time
from dataclasses import asdict
from importlib.resources import files

import httpx2
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.output import NativeOutput
from pydantic_ai.profiles.openai import OpenAIJsonSchemaTransformer, OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import RunUsage, UsageLimits

from governed_dataops.contracts import Diagnosis, Evidence, Incident, Scenario, ToolName
from governed_dataops.policy import FRESHNESS_OBJECTIVE_SECONDS
from governed_dataops.settings import Settings, get_settings

PROMPT_VERSION = "diagnosis-v3"
MAX_CONTEXT_BYTES = 32_000
LOCAL_GENERATION_ORDER = ["summary", "evidence_refs", "rationale", "category", "proposed_action"]
_SECRET = re.compile(
    r"(?i)(\b(?:authorization|api[_-]?key|access[_-]?token|password|secret)\b\s*[:=]\s*)"
    r"(?:bearer\s+)?[^\s,;]+"
)


class DiagnosticError(RuntimeError):
    def __init__(self, message: str, trace: dict | None = None) -> None:
        super().__init__(message)
        self.trace = trace or {}


class LocalNativeSchema(OpenAIJsonSchemaTransformer):
    """Compact local decoding grammar; original Pydantic bounds still apply.

    Long bounded strings expand expensive llama.cpp grammars. Keep the native
    JSON shape, required fields, enums and additional-field prohibition while
    validating every original length and count constraint after decoding.
    """

    def transform(self, schema: dict) -> dict:
        for bound in ("minLength", "maxLength", "minItems", "maxItems"):
            schema.pop(bound, None)
        transformed = super().transform(schema)
        if set(transformed.get("properties", {})) == set(LOCAL_GENERATION_ORDER):
            # Generate factual fields before committing to a category/action.
            # This changes decoding order, not the accepted Diagnosis contract.
            transformed["properties"] = {
                name: transformed["properties"][name] for name in LOCAL_GENERATION_ORDER
            }
            transformed["required"] = LOCAL_GENERATION_ORDER.copy()
        return transformed


def evidence_schema_transformer(
    evidence_id: str, *, local: bool = True
) -> type[OpenAIJsonSchemaTransformer]:
    """Compile permitted citations before generation; never rewrite a response."""
    parent = LocalNativeSchema if local else OpenAIJsonSchemaTransformer

    class EvidenceBoundSchema(parent):
        def walk(self) -> dict:
            schema = super().walk()
            reference = schema["properties"]["evidence_refs"]
            reference["items"] = {"type": "string", "enum": [evidence_id]}
            reference["minItems"] = 1
            reference["maxItems"] = 1
            return schema

    return EvidenceBoundSchema


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sanitized_evidence(evidence: Evidence) -> Evidence:
    return evidence.model_copy(
        update={"logs": [_SECRET.sub(r"\1[REDACTED]", line) for line in evidence.logs]}
    )


def validate_evidence(incident: Incident, evidence: Evidence) -> None:
    if not evidence.complete:
        raise DiagnosticError("evidence is incomplete; diagnostic abstention is required")
    if (incident.target_id, incident.environment, incident.scope) != (
        evidence.snapshot.target_id,
        evidence.snapshot.environment,
        evidence.snapshot.scope,
    ):
        raise DiagnosticError("evidence target, environment or scope does not match the incident")


def validate_diagnosis(diagnosis: Diagnosis, evidence: Evidence) -> None:
    """Reject unsupported model proposals without substituting runbook results.

    Log text and model rationale are never authorization evidence. All
    deterministic business preconditions are checked on the typed snapshot
    *before* accepting a model proposal. This is not a model classifier or a
    runbook fallback; an unsupported proposal is rejected, never rewritten.
    The target/policy independently recheck live state before any effect.
    """
    if set(diagnosis.evidence_refs) != {evidence.evidence_id}:
        raise DiagnosticError("diagnosis cites evidence that was not collected")
    expected_actions = {
        Scenario.FRESHNESS: ToolName.REFRESH,
        Scenario.TRANSIENT: ToolName.RETRY,
        Scenario.SCHEMA: ToolName.MIGRATE,
        Scenario.QUALITY: ToolName.QUARANTINE,
        Scenario.DUPLICATE: ToolName.SUPPRESS,
        Scenario.UNKNOWN: ToolName.ESCALATE,
    }
    if diagnosis.proposed_action != expected_actions[diagnosis.category]:
        raise DiagnosticError("model category/action pair contradicts the fixed catalogue")
    s = evidence.snapshot
    schema_compatible = s.source_schema == s.accepted_schema
    # Mirror the policy's business preconditions, not its authorization roles.
    # In particular, a late *applied* batch may have high lag and backlog yet
    # cannot be a pending freshness refresh: reject it before plan creation.
    necessary_support = {
        Scenario.FRESHNESS: (
            schema_compatible
            and s.freshness_lag_seconds > FRESHNESS_OBJECTIVE_SECONDS
            and s.backlog_rows > 0
            and s.batch_status == "pending"
            and s.rejected_rows == 0
            and s.curated_rows == 0
            and s.duplicate_rows == 0
            and not s.transient_failure
        ),
        Scenario.TRANSIENT: (
            schema_compatible
            and s.transient_failure
            and s.batch_status == "failed"
            and s.backlog_rows > 0
            and s.rejected_rows == 0
            and s.curated_rows == 0
            and s.duplicate_rows == 0
        ),
        Scenario.SCHEMA: not schema_compatible,
        Scenario.QUALITY: (
            schema_compatible
            and s.rejected_rows > 0
            and s.batch_status == "rejected"
            and s.curated_rows == 0
            and s.duplicate_rows == 0
        ),
        Scenario.DUPLICATE: (
            schema_compatible
            and s.batch_status == "applied"
            and s.curated_rows > 0
            and s.backlog_rows > 0
            and s.duplicate_rows == 0
        ),
        Scenario.UNKNOWN: True,  # Explicit abstention always remains available.
    }
    if not necessary_support[diagnosis.category]:
        raise DiagnosticError(
            "model diagnosis contradicts necessary typed snapshot preconditions"
        )


def runbook_diagnose(incident: Incident, evidence: Evidence) -> tuple[Diagnosis, dict]:
    """Versioned deterministic comparison baseline; never an agent fallback."""
    validate_evidence(incident, evidence)
    snapshot = evidence.snapshot
    if snapshot.source_schema != snapshot.accepted_schema:
        category, action = Scenario.SCHEMA, ToolName.MIGRATE
        reason = f"Source schema {snapshot.source_schema} differs from accepted schema {snapshot.accepted_schema}."
    elif (
        snapshot.batch_status == "applied"
        and snapshot.curated_rows > 0
        and snapshot.backlog_rows > 0
    ):
        category, action = Scenario.DUPLICATE, ToolName.SUPPRESS
        reason = f"Already-applied batch has {snapshot.curated_rows} curated rows and a pending redelivery."
    elif snapshot.rejected_rows > 0:
        category, action = Scenario.QUALITY, ToolName.QUARANTINE
        reason = f"Batch has {snapshot.rejected_rows} rejected rows; isolate it from curated data."
    elif snapshot.transient_failure:
        category, action = Scenario.TRANSIENT, ToolName.RETRY
        reason = f"A transient failure left {snapshot.backlog_rows} unprocessed rows."
    elif snapshot.freshness_lag_seconds > 300 and snapshot.backlog_rows > 0:
        category, action = Scenario.FRESHNESS, ToolName.REFRESH
        reason = f"Freshness lag is {snapshot.freshness_lag_seconds}s with {snapshot.backlog_rows} pending rows."
    else:
        category, action = Scenario.UNKNOWN, ToolName.ESCALATE
        reason = "No baseline runbook condition establishes a justified corrective action."
    return Diagnosis(
        category=category,
        summary=reason,
        evidence_refs=[evidence.evidence_id],
        proposed_action=action,
        rationale=reason,
    ), {
        "mode": "runbook",
        "runbook_version": "1.0",
        "model_used": False,
        "request_attempted": False,
        "response_observed": False,
        "usage_complete": True,
        "provider_cost_usd": 0,
    }


async def diagnose(
    incident: Incident, evidence: Evidence, settings: Settings | None = None
) -> tuple[Diagnosis, dict]:
    """Run a bounded model diagnostic; invalid/unavailable output escalates."""
    settings = settings or get_settings()
    validate_evidence(incident, evidence)
    prompt = (
        files("governed_dataops").joinpath("prompts", f"{PROMPT_VERSION}.txt").read_text("utf-8")
    )
    context = json.dumps(
        {
            "incident": incident.model_copy(
                update={"symptom": _SECRET.sub(r"\1[REDACTED]", incident.symptom)}
            ).model_dump(mode="json"),
            "evidence": sanitized_evidence(evidence).model_dump(mode="json"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    for field in (
        "executor_token",
        "reader_token",
        "operator_token",
        "approver_token",
        "model_api_key",
    ):
        value = getattr(settings, field)
        if value and value != "local-only":
            context = context.replace(json.dumps(value)[1:-1], "[REDACTED]")
    if len(context.encode("utf-8")) > MAX_CONTEXT_BYTES:
        raise DiagnosticError(
            "evidence exceeds the bounded diagnostic context; no silent truncation"
        )
    parameters = {
        "temperature": 0.0,
        "max_tokens": settings.model_max_tokens,
        "timeout": settings.model_timeout_seconds,
    }
    transformer = evidence_schema_transformer(
        evidence.evidence_id, local=settings.model_provider == "local"
    )
    native_schema = transformer(Diagnosis.model_json_schema(), strict=True).walk()
    schema_hash = _hash(json.dumps(native_schema, separators=(",", ":")))
    request_descriptor = {
        "prompt_sha256": _hash(prompt),
        "context_sha256": _hash(context),
        "parameters": parameters,
        "native_schema_sha256": schema_hash,
        "model": settings.model_name,
        "model_revision": settings.model_revision,
    }
    trace = {
        "mode": "agent",
        "provider": settings.model_provider,
        "model": settings.model_name,
        "model_revision": settings.model_revision,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": _hash(prompt),
        "context_sha256": _hash(context),
        "request_sha256": _hash(json.dumps(request_descriptor, sort_keys=True)),
        "native_schema_sha256": schema_hash,
        "generation_property_order": list(native_schema["properties"]),
        "permitted_evidence_refs": [evidence.evidence_id],
        "citation_constraint": "native enum compiled from validated evidence; original post-validator retained",
        "parameters": parameters,
        "context": json.loads(context),
        "tools_available_to_model": [],
        "provider_cost_usd": 0.0 if settings.model_provider == "local" else None,
        "cost_basis": "local provider charge only; compute and energy unmeasured"
        if settings.model_provider == "local"
        else "provider price not configured; cost unknown",
        "model_used": False,
        "model_used_basis": "completed model response observed",
        "request_attempted": False,
        "response_observed": False,
        "diagnosis_valid": False,
    }
    usage = RunUsage()
    run_completed = False
    started = time.monotonic()
    try:
        async with httpx2.AsyncClient(
            timeout=settings.model_timeout_seconds, trust_env=False, follow_redirects=False
        ) as http_client:
            async with AsyncOpenAI(
                base_url=settings.model_base_url,
                api_key=settings.model_api_key,
                max_retries=0,
                http_client=http_client,
            ) as openai_client:
                model = OpenAIChatModel(
                    settings.model_name,
                    provider=OpenAIProvider(openai_client=openai_client),
                    profile=OpenAIModelProfile(
                        supports_json_schema_output=True,
                        supports_tools=False,
                        openai_chat_supports_max_completion_tokens=False,
                        json_schema_transformer=transformer,
                    ),
                )
                agent = Agent(
                    model,
                    output_type=NativeOutput(Diagnosis, strict=True),
                    instructions=prompt,
                    tools=[],
                    retries=1,
                    model_settings=parameters,
                )
                trace["request_attempted"] = True
                result = await agent.run(
                    context,
                    usage=usage,
                    usage_limits=UsageLimits(
                        request_limit=2,
                        tool_calls_limit=0,
                        output_tokens_limit=settings.model_max_tokens * 2,
                        input_tokens_limit=20_000,
                    ),
                    timeout=settings.model_timeout_seconds,
                )
                run_completed = True
                diagnosis = result.output
                trace["model_proposal"] = diagnosis.model_dump(mode="json")
                validate_diagnosis(diagnosis, evidence)
                trace["diagnosis_valid"] = True
                trace["response_sha256"] = _hash(diagnosis.model_dump_json())
                return diagnosis, trace
    except Exception as exc:
        trace["error_type"] = type(exc).__name__
        if isinstance(exc, DiagnosticError):
            trace["validation_failure"] = str(exc)
        raise DiagnosticError(
            f"diagnostic model did not provide a valid sourced proposal ({type(exc).__name__})",
            trace,
        ) from None
    finally:
        trace["response_observed"] = usage.requests > 0
        trace["model_used"] = trace["response_observed"]
        trace["usage_complete"] = run_completed and usage.unmeasured_requests == 0
        trace["usage_note"] = (
            "Reported usage for the completed diagnostic run; compute and energy are unmeasured"
            if trace["usage_complete"]
            else "Usage covers observed responses only; interrupted server work may be unreported"
        )
        trace["duration_seconds"] = round(time.monotonic() - started, 6)
        trace["usage"] = json.loads(json.dumps(asdict(usage), default=str))
