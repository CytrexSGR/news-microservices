"""
Source Profile Model

Tracks scraping capabilities and performance per domain.
Enables intelligent strategy selection based on historical data.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ScrapeMethodEnum(str, Enum):
    """Available scraping methods"""
    NEWSPAPER4K = "newspaper4k"
    TRAFILATURA = "trafilatura"
    PLAYWRIGHT = "playwright"
    PLAYWRIGHT_STEALTH = "playwright_stealth"
    HTTPX_BASIC = "httpx_basic"
    JSONLD = "jsonld"


class PaywallTypeEnum(str, Enum):
    """Paywall classification"""
    NONE = "none"                   # No paywall
    SOFT = "soft"                   # Can be bypassed (cookie, JS disable)
    HARD = "hard"                   # Requires subscription
    METERED = "metered"             # Limited free articles
    REGISTRATION = "registration"   # Free but requires login
    UNKNOWN = "unknown"             # Not yet classified


class ScrapeStatusEnum(str, Enum):
    """Scraping capability status"""
    WORKING = "working"             # Currently scraping successfully
    DEGRADED = "degraded"           # Partial success (low success rate)
    BLOCKED = "blocked"             # Domain is blocking us
    UNSUPPORTED = "unsupported"     # Cannot scrape (technical limitation)
    UNKNOWN = "unknown"             # Not yet tested


# SQLAlchemy ORM Model
class SourceProfileDB(Base):
    """Database model for source profiles"""
    __tablename__ = "source_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)

    # Scraping configuration
    scrape_method = Column(String(50), default=ScrapeMethodEnum.NEWSPAPER4K.value)
    fallback_methods = Column(JSON, default=list)  # Ordered list of fallback methods
    scrape_status = Column(String(50), default=ScrapeStatusEnum.UNKNOWN.value)

    # Paywall information
    paywall_type = Column(String(50), default=PaywallTypeEnum.UNKNOWN.value)
    paywall_bypass_method = Column(String(100), nullable=True)  # e.g., "disable_js", "clear_cookies"

    # Performance metrics
    success_rate = Column(Float, default=0.0)
    avg_response_time_ms = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    total_successes = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=10)
    last_rate_limited_at = Column(DateTime, nullable=True)

    # Content quality
    avg_word_count = Column(Integer, default=0)
    avg_extraction_quality = Column(Float, default=0.0)  # 0-1 score

    # Anti-detection settings
    requires_ua_rotation = Column(Boolean, default=True)
    requires_stealth = Column(Boolean, default=False)
    requires_proxy = Column(Boolean, default=False)
    custom_headers = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_successful_scrape = Column(DateTime, nullable=True)
    last_failed_scrape = Column(DateTime, nullable=True)

    # Notes
    notes = Column(String(1000), nullable=True)


# Pydantic Schemas
class SourceProfileBase(BaseModel):
    """Base schema for source profile"""
    domain: str
    scrape_method: ScrapeMethodEnum = ScrapeMethodEnum.NEWSPAPER4K
    fallback_methods: List[ScrapeMethodEnum] = []
    paywall_type: PaywallTypeEnum = PaywallTypeEnum.UNKNOWN
    rate_limit_per_minute: int = 10
    requires_ua_rotation: bool = True
    requires_stealth: bool = False
    requires_proxy: bool = False
    custom_headers: Dict[str, str] = {}
    notes: Optional[str] = None


class SourceProfileCreate(SourceProfileBase):
    """Schema for creating source profile"""
    pass


class SourceProfileUpdate(BaseModel):
    """Schema for updating source profile"""
    scrape_method: Optional[ScrapeMethodEnum] = None
    fallback_methods: Optional[List[ScrapeMethodEnum]] = None
    paywall_type: Optional[PaywallTypeEnum] = None
    paywall_bypass_method: Optional[str] = None
    scrape_status: Optional[ScrapeStatusEnum] = None
    rate_limit_per_minute: Optional[int] = None
    requires_ua_rotation: Optional[bool] = None
    requires_stealth: Optional[bool] = None
    requires_proxy: Optional[bool] = None
    custom_headers: Optional[Dict[str, str]] = None
    notes: Optional[str] = None


class SourceProfile(SourceProfileBase):
    """Full source profile with metrics"""
    id: int = 0
    scrape_status: ScrapeStatusEnum = ScrapeStatusEnum.UNKNOWN
    success_rate: float = 0.0
    avg_response_time_ms: int = 0
    total_attempts: int = 0
    total_successes: int = 0
    total_failures: int = 0
    avg_word_count: int = 0
    avg_extraction_quality: float = 0.0
    last_successful_scrape: Optional[datetime] = None
    last_failed_scrape: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SourceProfileMetricsUpdate(BaseModel):
    """Schema for updating metrics after scrape attempt"""
    success: bool
    response_time_ms: int
    word_count: int = 0
    extraction_quality: float = 0.0
    method_used: ScrapeMethodEnum
    error_message: Optional[str] = None
