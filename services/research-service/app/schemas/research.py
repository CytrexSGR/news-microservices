"""Pydantic schemas for Research Service."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator


# Research Task Schemas
class ResearchTaskCreate(BaseModel):
    """Schema for creating a research task."""
    query: str = Field(..., min_length=10, max_length=2000)
    model_name: str = Field(default="sonar", pattern="^(sonar|sonar-pro|sonar-reasoning-pro)$")
    depth: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    feed_id: Optional[UUID] = None
    legacy_feed_id: Optional[int] = None
    article_id: Optional[UUID] = None
    legacy_article_id: Optional[int] = None
    research_function: Optional[str] = None
    function_parameters: Optional[Dict[str, Any]] = None


class ResearchTaskBatchCreate(BaseModel):
    """Schema for batch research tasks."""
    queries: List[str] = Field(..., min_items=1, max_items=10)
    model_name: str = Field(default="sonar", pattern="^(sonar|sonar-pro|sonar-reasoning-pro)$")
    depth: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    feed_id: Optional[UUID] = None
    legacy_feed_id: Optional[int] = None


class ResearchTaskResponse(BaseModel):
    """Schema for research task response."""
    id: int
    user_id: int
    query: str
    model_name: str
    depth: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    validation_status: Optional[str] = None
    tokens_used: int
    cost: float
    feed_id: Optional[UUID] = None
    legacy_feed_id: Optional[int] = None
    article_id: Optional[UUID] = None
    legacy_article_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResearchTaskList(BaseModel):
    """Schema for paginated research task list."""
    tasks: List[ResearchTaskResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# Template Schemas
class TemplateCreate(BaseModel):
    """Schema for creating a template."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    query_template: str = Field(..., min_length=10, max_length=2000)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    default_model: str = Field(default="sonar", pattern="^(sonar|sonar-pro|sonar-reasoning-pro)$")
    default_depth: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    is_public: bool = Field(default=False)
    research_function: Optional[str] = None
    function_parameters: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None


class TemplateUpdate(BaseModel):
    """Schema for updating a template."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    query_template: Optional[str] = Field(None, min_length=10, max_length=2000)
    parameters: Optional[Dict[str, Any]] = None
    default_model: Optional[str] = Field(None, pattern="^(sonar|sonar-pro|sonar-reasoning-pro)$")
    default_depth: Optional[str] = Field(None, pattern="^(quick|standard|deep)$")
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    research_function: Optional[str] = None
    function_parameters: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None


class TemplateResponse(BaseModel):
    """Schema for template response."""
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    query_template: str
    parameters: Dict[str, Any]
    default_model: str
    default_depth: str
    is_active: bool
    is_public: bool
    usage_count: int
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    research_function: Optional[str] = None
    function_parameters: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class TemplateApply(BaseModel):
    """Schema for applying a template."""
    variables: Dict[str, Any] = Field(default_factory=dict)
    model_name: Optional[str] = None
    depth: Optional[str] = None
    feed_id: Optional[UUID] = None
    legacy_feed_id: Optional[int] = None
    article_id: Optional[UUID] = None
    legacy_article_id: Optional[int] = None


class TemplatePreview(BaseModel):
    """Schema for template preview."""
    template_id: int
    variables: Dict[str, Any]
    rendered_query: str
    estimated_cost: float


# Statistics Schemas
class UsageStats(BaseModel):
    """Schema for usage statistics."""
    total_requests: int
    total_tokens: int
    total_cost: float
    requests_by_model: Dict[str, int]
    cost_by_model: Dict[str, float]
    avg_tokens_per_request: float
    period_start: datetime
    period_end: datetime


class CostBreakdown(BaseModel):
    """Schema for cost breakdown."""
    daily_cost: float
    weekly_cost: float
    monthly_cost: float
    cost_by_day: List[Dict[str, Any]]
    cost_by_model: Dict[str, float]
    remaining_daily_budget: float
    remaining_monthly_budget: float


# Research Run Schemas
class ResearchRunCreate(BaseModel):
    """Schema for creating a research run."""
    template_id: int = Field(..., gt=0)
    parameters: Dict[str, str] = Field(default_factory=dict)
    model_name: Optional[str] = Field(None, pattern="^(sonar|sonar-pro|sonar-reasoning-pro)$")
    depth: Optional[str] = Field(None, pattern="^(quick|standard|deep)$")
    scheduled_at: Optional[datetime] = None
    is_recurring: bool = Field(default=False)
    recurrence_pattern: Optional[str] = Field(None, pattern="^(daily|weekly|monthly)$")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchRunResponse(BaseModel):
    """Schema for research run response."""
    id: int
    user_id: int
    template_id: int
    template_name: str
    parameters: Dict[str, str]
    model_name: str
    depth: str
    scheduled_at: Optional[datetime] = None
    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tasks_created: int
    tasks_completed: int
    tasks_failed: int
    total_tokens_used: int
    total_cost: float
    results_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    triggered_by: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchRunList(BaseModel):
    """Schema for paginated research run list."""
    runs: List[ResearchRunResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ResearchRunStatus(BaseModel):
    """Schema for run status."""
    id: int
    status: str
    progress: float
    tasks_created: int
    tasks_completed: int
    tasks_failed: int
    total_tokens_used: int
    total_cost: float
    error_message: Optional[str] = None
