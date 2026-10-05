"""Persisted guided execution contracts; sanitized trace data is never executable code."""

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from robotops.domain.models import Contract, OrderRequest, new_id, utc_now


class CreateSession(Contract):
    request: OrderRequest
    request_id: str = Field(min_length=1, max_length=160)
    mode: Literal["guided"] = "guided"
    fault: str | None = None


class AuthorizeStage(Contract):
    request_id: str = Field(min_length=1, max_length=160)
    expected_revision: int = Field(ge=0)
    stage: int = Field(ge=1, le=22)
    decision: Literal["approve"] = "approve"


class SourceReference(Contract):
    path: str
    symbol: str
    excerpt: str


class PendingAuthorization(Contract):
    stage: int
    title: str
    label: str
    expected_revision: int
    mandatory: bool


class ProtocolTrace(Contract):
    trace_id: str = Field(default_factory=new_id)
    protocol: str
    classification: str
    wire: dict[str, Any] = Field(default_factory=dict)


class ExecutionStep(Contract):
    step_id: str
    session_id: str
    execution_session_id: str
    order_id: str
    job_id: str | None
    command_id: str | None
    correlation_id: str
    stage: int
    sequence: int
    revision: int
    title: str
    summary: str
    status: str
    component: str
    protocol: str
    classification: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    state_before: str
    state_after: str
    persistence_effect: str
    wire: dict[str, Any] = Field(default_factory=dict)
    source: SourceReference
    invariant: str
    failure_semantics: str
    timestamp: datetime = Field(default_factory=utc_now)
    duration_ms: float = 0
    evidence_ids: tuple[str, ...] = ()
    authorization_required: bool = False


class AuthorizationDecision(Contract):
    authorization_id: str
    session_id: str
    request_id: str
    stage: int
    expected_revision: int
    decision: Literal["approve"]
    timestamp: datetime = Field(default_factory=utc_now)


class ExecutionSession(Contract):
    session_id: str
    execution_session_id: str
    correlation_id: str
    request: OrderRequest
    request_id: str
    order_id: str
    job_id: str | None = None
    command_id: str | None = None
    job_ids: tuple[str, ...] = ()
    revision: int = 0
    status: str = "WAITING_AUTHORIZATION"
    current_stage: int = 1
    mode: Literal["guided"] = "guided"
    profile: str = "local"
    fault: str | None = None
    steps: tuple[ExecutionStep, ...] = ()
    pending_authorization: PendingAuthorization | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
