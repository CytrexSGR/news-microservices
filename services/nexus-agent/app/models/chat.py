"""Chat Request/Response Models."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    session_id: Optional[str] = Field(
        default="default",
        description="Session identifier for conversation tracking",
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str = Field(..., description="Agent response")
    intent: str = Field(default="unknown", description="Classified intent")
    tokens_used: int = Field(default=0, description="Tokens consumed")
    latency_ms: int = Field(default=0, description="Response latency in milliseconds")
    confidence: float = Field(default=0.0, description="Response confidence score")
    error: Optional[str] = Field(default=None, description="Error message if any")

    # Phase 3 additions
    awaiting_confirmation: bool = Field(
        default=False,
        description="True if awaiting user confirmation of a plan"
    )
    pending_plan: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Pending execution plan awaiting confirmation"
    )
    execution_progress: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current execution progress for multi-step plans"
    )
    structured_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured output data from synthesis"
    )


class PlanConfirmation(BaseModel):
    """Request model for plan confirmation."""

    action: str = Field(
        ...,
        description="Confirmation action: 'confirm', 'modify', or 'cancel'"
    )
    session_id: str = Field(
        default="default",
        description="Session identifier"
    )
    modifications: Optional[List[str]] = Field(
        default=None,
        description="List of modifications if action is 'modify'"
    )


class HealthResponse(BaseModel):
    """Response model for health endpoint."""

    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(default="nexus-agent", description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
