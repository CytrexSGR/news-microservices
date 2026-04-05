"""SQLAlchemy models for Research Service."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ResearchTask(Base):
    """Research task model."""
    __tablename__ = "research_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Query information
    query = Column(Text, nullable=False)
    model_name = Column(String(50), nullable=False, default="sonar")
    depth = Column(String(20), default="standard")  # quick, standard, deep

    # Status
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed

    # Results
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)
    validation_status = Column(String(50), nullable=True)
    output_schema = Column(JSON, nullable=True)  # Pydantic schema for structured output

    # Cost tracking
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)

    # Metadata
    feed_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    article_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)

    # Legacy fields for migration from old Integer-based system
    legacy_feed_id = Column(Integer, nullable=True, index=True)
    legacy_article_id = Column(Integer, nullable=True, index=True)

    run_id = Column(Integer, ForeignKey("research_runs.id"), nullable=True)  # Link to research run (indexed in __table_args__)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    run = relationship("ResearchRun", backref="tasks")

    # Indexes
    __table_args__ = (
        Index('ix_research_tasks_user_status', 'user_id', 'status'),
        Index('ix_research_tasks_created', 'created_at'),
        Index('ix_research_tasks_run_id', 'run_id'),
    )


class ResearchTemplate(Base):
    """Research template model."""
    __tablename__ = "research_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Template information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    query_template = Column(Text, nullable=False)
    
    # Parameters
    parameters = Column(JSON, default=dict)  # Available template variables
    default_model = Column(String(50), default="sonar")
    default_depth = Column(String(20), default="standard")
    research_function = Column(String(50), nullable=True)
    output_schema = Column(JSON, nullable=True)
    function_parameters = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('ix_research_templates_user_active', 'user_id', 'is_active'),
    )


class ResearchCache(Base):
    """Research results cache model."""
    __tablename__ = "research_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Cache key (hash of query + model + depth)
    cache_key = Column(String(64), unique=True, nullable=False, index=True)
    
    # Query information
    query = Column(Text, nullable=False)
    model_name = Column(String(50), nullable=False)
    depth = Column(String(20), nullable=False)
    
    # Cached result
    result = Column(JSON, nullable=False)
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    
    # Cache metadata
    hit_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ResearchRun(Base):
    """Research run model for automated/scheduled research."""
    __tablename__ = "research_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Template information
    template_id = Column(Integer, ForeignKey("research_templates.id"), nullable=False, index=True)
    template_name = Column(String(100), nullable=False)  # Denormalized for reporting

    # Execution configuration
    parameters = Column(JSON, default=dict)  # Parameters applied to template
    model_name = Column(String(50), nullable=False, default="sonar")
    depth = Column(String(20), default="standard")

    # Scheduling information
    scheduled_at = Column(DateTime, nullable=True, index=True)  # When to run (null = manual)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(50), nullable=True)  # cron-like: "daily", "weekly", "monthly"

    # Execution status
    status = Column(String(20), default="pending", index=True)  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Results tracking
    tasks_created = Column(Integer, default=0)  # Number of research tasks spawned
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)

    # Results summary (aggregated from tasks)
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)

    # Output summary
    results_summary = Column(JSON, nullable=True)  # Aggregated insights, key findings
    error_message = Column(Text, nullable=True)

    # Metadata
    triggered_by = Column(String(50), default="manual")  # manual, schedule, api, webhook
    run_metadata = Column(JSON, default=dict)  # Additional context (feed_id, article_ids, etc.)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("ResearchTemplate", backref="runs")

    # Indexes for query performance
    __table_args__ = (
        Index('ix_research_runs_user_status', 'user_id', 'status'),
        Index('ix_research_runs_template_status', 'template_id', 'status'),
        Index('ix_research_runs_scheduled', 'scheduled_at', 'status'),
        Index('ix_research_runs_created', 'created_at'),
        Index('ix_research_runs_completed', 'completed_at'),
    )


class CostTracking(Base):
    """Cost tracking model."""
    __tablename__ = "cost_tracking"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Cost information
    date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    model_name = Column(String(50), nullable=False)
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)

    # Request information
    task_id = Column(Integer, ForeignKey("research_tasks.id"), nullable=True)
    run_id = Column(Integer, ForeignKey("research_runs.id"), nullable=True)  # Link to research run
    request_count = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
