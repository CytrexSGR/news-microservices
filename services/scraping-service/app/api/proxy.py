"""
Proxy Manager API Endpoints

Phase 6: Scale

Provides endpoints for:
- Proxy pool management
- Proxy health monitoring
- Domain affinity management
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.services.proxy_manager import get_proxy_manager
from app.models.proxy import ProxyConfig, ProxyStatusEnum

router = APIRouter(prefix="/api/v1/proxy", tags=["proxy"])


class ProxyAddRequest(BaseModel):
    """Request to add a proxy"""
    id: str
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "http"  # http, https, socks5


class ProxyAddBatchRequest(BaseModel):
    """Request to add multiple proxies"""
    proxies: List[Dict[str, Any]]


class ProxyStatsResponse(BaseModel):
    """Proxy pool statistics"""
    total_proxies: int
    healthy_proxies: int
    unhealthy_proxies: int
    unknown_proxies: int
    avg_response_time_ms: float
    total_requests: int
    total_failures: int
    success_rate: float


class ProxyHealthResponse(BaseModel):
    """Proxy health information"""
    proxy_id: str
    status: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    consecutive_failures: int
    avg_response_time_ms: float
    last_used: Optional[str] = None
    last_failure: Optional[str] = None


@router.get("/stats", response_model=ProxyStatsResponse)
async def get_proxy_stats() -> ProxyStatsResponse:
    """Get proxy pool statistics"""
    manager = get_proxy_manager()
    stats = manager.get_stats()

    return ProxyStatsResponse(
        total_proxies=stats.total_proxies,
        healthy_proxies=stats.healthy_proxies,
        unhealthy_proxies=stats.unhealthy_proxies,
        unknown_proxies=stats.unknown_proxies,
        avg_response_time_ms=stats.avg_response_time_ms,
        total_requests=stats.total_requests,
        total_failures=stats.total_failures,
        success_rate=stats.success_rate
    )


@router.get("/list")
async def list_proxies() -> Dict[str, Any]:
    """List all proxies in the pool"""
    manager = get_proxy_manager()

    proxies = []
    for proxy_id, proxy in manager._proxies.items():
        health = manager.get_health(proxy_id)
        proxies.append({
            "id": proxy.id,
            "host": proxy.host,
            "port": proxy.port,
            "type": proxy.proxy_type.value if hasattr(proxy.proxy_type, 'value') else str(proxy.proxy_type),
            "url_masked": proxy.url_masked,
            "status": health.status.value if health else "unknown"
        })

    return {
        "count": len(proxies),
        "proxies": proxies
    }


@router.post("/add")
async def add_proxy(request: ProxyAddRequest) -> Dict[str, Any]:
    """Add a proxy to the pool"""
    manager = get_proxy_manager()

    proxy = ProxyConfig(
        id=request.id,
        host=request.host,
        port=request.port,
        username=request.username,
        password=request.password
    )

    manager.add_proxy(proxy)

    return {
        "success": True,
        "message": f"Added proxy: {request.id}",
        "proxy": {
            "id": proxy.id,
            "host": proxy.host,
            "port": proxy.port,
            "url_masked": proxy.url_masked
        }
    }


@router.post("/add-batch")
async def add_proxies_batch(request: ProxyAddBatchRequest) -> Dict[str, Any]:
    """Add multiple proxies to the pool"""
    manager = get_proxy_manager()
    count = manager.add_proxies_from_list(request.proxies)

    return {
        "success": True,
        "proxies_added": count,
        "message": f"Added {count} proxies to the pool"
    }


@router.delete("/{proxy_id}")
async def remove_proxy(proxy_id: str) -> Dict[str, Any]:
    """Remove a proxy from the pool"""
    manager = get_proxy_manager()
    success = manager.remove_proxy(proxy_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Proxy not found: {proxy_id}"
        )

    return {
        "success": True,
        "message": f"Removed proxy: {proxy_id}"
    }


@router.get("/health/{proxy_id}", response_model=ProxyHealthResponse)
async def get_proxy_health(proxy_id: str) -> ProxyHealthResponse:
    """Get health information for a specific proxy"""
    manager = get_proxy_manager()
    health = manager.get_health(proxy_id)

    if not health:
        raise HTTPException(
            status_code=404,
            detail=f"Proxy not found: {proxy_id}"
        )

    return ProxyHealthResponse(
        proxy_id=proxy_id,
        status=health.status.value,
        total_requests=health.total_requests,
        successful_requests=health.successful_requests,
        failed_requests=health.failed_requests,
        consecutive_failures=health.consecutive_failures,
        avg_response_time_ms=health.avg_response_time_ms,
        last_used=health.last_success_at.isoformat() if health.last_success_at else None,
        last_failure=health.last_failure_at.isoformat() if health.last_failure_at else None
    )


@router.post("/reset-unhealthy")
async def reset_unhealthy_proxies() -> Dict[str, Any]:
    """Reset unhealthy proxies for retry"""
    manager = get_proxy_manager()
    count = manager.reset_unhealthy_proxies()

    return {
        "success": True,
        "proxies_reset": count,
        "message": f"Reset {count} unhealthy proxies"
    }


@router.post("/clear-affinity")
async def clear_domain_affinity(domain: Optional[str] = None) -> Dict[str, Any]:
    """Clear domain affinity mappings"""
    manager = get_proxy_manager()
    count = manager.clear_domain_affinity(domain)

    message = f"Cleared affinity for domain: {domain}" if domain else "Cleared all domain affinities"

    return {
        "success": True,
        "affinities_cleared": count,
        "message": message
    }


@router.get("/for-domain/{domain}")
async def get_proxy_for_domain(domain: str) -> Dict[str, Any]:
    """Get the proxy that would be used for a domain"""
    manager = get_proxy_manager()
    proxy = manager.get_proxy_for_domain(domain)

    if not proxy:
        return {
            "domain": domain,
            "proxy": None,
            "message": "No proxy available or rotation disabled"
        }

    return {
        "domain": domain,
        "proxy": {
            "id": proxy.id,
            "host": proxy.host,
            "port": proxy.port,
            "url_masked": proxy.url_masked
        }
    }
