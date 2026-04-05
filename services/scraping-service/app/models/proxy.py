"""
Proxy Models

Phase 6: Scale

Defines proxy configurations and health tracking models.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ProxyTypeEnum(str, Enum):
    """Proxy protocol type"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"


class ProxyStatusEnum(str, Enum):
    """Proxy health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ProxyConfig(BaseModel):
    """Proxy server configuration"""
    id: str = Field(..., description="Unique proxy identifier")
    host: str = Field(..., description="Proxy hostname or IP")
    port: int = Field(..., ge=1, le=65535, description="Proxy port")
    proxy_type: ProxyTypeEnum = Field(default=ProxyTypeEnum.HTTP)
    username: Optional[str] = Field(None, description="Auth username")
    password: Optional[str] = Field(None, description="Auth password")

    # Metadata
    provider: Optional[str] = Field(None, description="Proxy provider name")
    region: Optional[str] = Field(None, description="Geographic region")
    is_residential: bool = Field(default=False, description="Residential proxy flag")

    @property
    def url(self) -> str:
        """Get full proxy URL"""
        if self.username and self.password:
            return f"{self.proxy_type.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type.value}://{self.host}:{self.port}"

    @property
    def url_masked(self) -> str:
        """Get proxy URL with masked password"""
        if self.username and self.password:
            return f"{self.proxy_type.value}://{self.username}:***@{self.host}:{self.port}"
        return f"{self.proxy_type.value}://{self.host}:{self.port}"


class ProxyHealth(BaseModel):
    """Proxy health metrics"""
    proxy_id: str
    status: ProxyStatusEnum = Field(default=ProxyStatusEnum.UNKNOWN)

    # Success metrics
    total_requests: int = Field(default=0)
    successful_requests: int = Field(default=0)
    failed_requests: int = Field(default=0)

    # Performance metrics
    avg_response_time_ms: float = Field(default=0.0)
    last_response_time_ms: float = Field(default=0.0)

    # Health check info
    last_check_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    last_error: Optional[str] = None

    # Consecutive failures for circuit breaking
    consecutive_failures: int = Field(default=0)

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


class ProxyPoolStats(BaseModel):
    """Proxy pool statistics"""
    total_proxies: int = Field(default=0)
    healthy_proxies: int = Field(default=0)
    degraded_proxies: int = Field(default=0)
    unhealthy_proxies: int = Field(default=0)
    unknown_proxies: int = Field(default=0)

    # Aggregate metrics
    total_requests: int = Field(default=0)
    total_success: int = Field(default=0)
    total_failures: int = Field(default=0)
    success_rate: float = Field(default=0.0, description="Overall success rate")
    avg_response_time_ms: float = Field(default=0.0, description="Average response time in ms")

    # Pool by provider
    by_provider: Dict[str, int] = Field(default_factory=dict)
    by_region: Dict[str, int] = Field(default_factory=dict)


class ProxyRotationConfig(BaseModel):
    """Proxy rotation configuration"""
    enabled: bool = Field(default=False)
    strategy: str = Field(default="round_robin", description="Rotation strategy: round_robin, random, weighted")

    # Health checking
    health_check_interval_seconds: int = Field(default=60)
    health_check_timeout_seconds: int = Field(default=10)
    health_check_url: str = Field(default="https://httpbin.org/ip")

    # Circuit breaking
    max_consecutive_failures: int = Field(default=3)
    recovery_timeout_seconds: int = Field(default=300)

    # Domain affinity (use same proxy for same domain)
    domain_affinity: bool = Field(default=True)
    domain_affinity_ttl_seconds: int = Field(default=3600)

    # Exclusions
    excluded_domains: List[str] = Field(default_factory=list, description="Domains that don't need proxy")
