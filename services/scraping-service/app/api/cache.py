"""
HTTP Cache API Endpoints

Phase 6: Scale

Provides endpoints for:
- Cache statistics
- Cache invalidation
- Cache management
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.services.http_cache import get_http_cache

router = APIRouter(prefix="/api/v1/cache", tags=["cache"])


class CacheStatsResponse(BaseModel):
    """Cache statistics response"""
    total_entries: int
    total_size_bytes: int
    total_size_mb: float
    total_hits: int
    total_misses: int
    hit_rate: float
    oldest_entry_age_seconds: float
    avg_entry_age_seconds: float


class CacheInvalidateRequest(BaseModel):
    """Cache invalidation request"""
    url: Optional[str] = None
    domain: Optional[str] = None


class CacheInvalidateResponse(BaseModel):
    """Cache invalidation response"""
    success: bool
    entries_removed: int
    message: str


class DomainTTLRequest(BaseModel):
    """Domain TTL configuration request"""
    domain: str
    ttl_seconds: int


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats() -> CacheStatsResponse:
    """Get HTTP cache statistics"""
    cache = get_http_cache()
    stats = cache.get_stats()

    return CacheStatsResponse(
        total_entries=stats.total_entries,
        total_size_bytes=stats.total_size_bytes,
        total_size_mb=stats.total_size_bytes / (1024 * 1024),
        total_hits=stats.total_hits,
        total_misses=stats.total_misses,
        hit_rate=stats.hit_rate,
        oldest_entry_age_seconds=stats.oldest_entry_age_seconds,
        avg_entry_age_seconds=stats.avg_entry_age_seconds
    )


@router.post("/invalidate", response_model=CacheInvalidateResponse)
async def invalidate_cache(request: CacheInvalidateRequest) -> CacheInvalidateResponse:
    """
    Invalidate cache entries.

    Provide either:
    - url: Invalidate a specific URL
    - domain: Invalidate all URLs for a domain
    """
    cache = get_http_cache()

    if request.url:
        success = cache.invalidate(request.url)
        return CacheInvalidateResponse(
            success=success,
            entries_removed=1 if success else 0,
            message=f"Invalidated cache for URL: {request.url}" if success else f"URL not in cache: {request.url}"
        )

    if request.domain:
        count = cache.invalidate_domain(request.domain)
        return CacheInvalidateResponse(
            success=count > 0,
            entries_removed=count,
            message=f"Invalidated {count} entries for domain: {request.domain}"
        )

    raise HTTPException(
        status_code=400,
        detail="Provide either 'url' or 'domain' for invalidation"
    )


@router.post("/cleanup")
async def cleanup_expired() -> Dict[str, Any]:
    """Remove all expired cache entries"""
    cache = get_http_cache()
    count = cache.cleanup_expired()

    return {
        "success": True,
        "entries_removed": count,
        "message": f"Removed {count} expired entries"
    }


@router.post("/clear")
async def clear_cache() -> Dict[str, Any]:
    """Clear entire cache (use with caution)"""
    cache = get_http_cache()
    count = cache.clear()

    return {
        "success": True,
        "entries_cleared": count,
        "message": f"Cleared {count} cache entries"
    }


@router.post("/domain-ttl")
async def set_domain_ttl(request: DomainTTLRequest) -> Dict[str, Any]:
    """Set custom TTL for a domain"""
    if request.ttl_seconds < 0:
        raise HTTPException(
            status_code=400,
            detail="TTL must be non-negative"
        )

    cache = get_http_cache()
    cache.set_domain_ttl(request.domain, request.ttl_seconds)

    return {
        "success": True,
        "domain": request.domain,
        "ttl_seconds": request.ttl_seconds,
        "message": f"Set TTL for {request.domain} to {request.ttl_seconds} seconds"
    }


@router.get("/entry/{url:path}")
async def get_cache_entry(url: str) -> Dict[str, Any]:
    """Get information about a specific cached entry"""
    cache = get_http_cache()
    entry = cache.get(url)

    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"URL not in cache: {url}"
        )

    return {
        "url": entry.url,
        "word_count": entry.word_count,
        "method": entry.method,
        "status": entry.status,
        "size_bytes": entry.size_bytes,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
        "hit_count": entry.hit_count,
        "last_hit_at": entry.last_hit_at.isoformat() if entry.last_hit_at else None,
        "metadata": entry.metadata
    }
