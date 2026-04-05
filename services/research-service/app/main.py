"""Main FastAPI application for Research Service."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db
from app.api import api_router
from app.services.perplexity import perplexity_client

# Import shared rate limiting
import sys
sys.path.insert(0, '/home/cytrex/news-microservices/services')
from common.rate_limiting import setup_rate_limiting

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if settings.LOG_FORMAT == "text"
    else '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
)

logger = logging.getLogger(__name__)

# OPTIMIZATION (Task 404): Health check cache
_celery_health_cache = None
_celery_health_cache_time = 0.0
_celery_health_cache_ttl = 60  # Cache Celery status for 60 seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting Research Service...")
    
    # Initialize database tables
    init_db()
    logger.info("Database initialized")
    
    # Check Perplexity API
    api_available = await perplexity_client.check_health()
    if api_available:
        logger.info("Perplexity API is available")
    else:
        logger.warning("Perplexity API is not available - check API key")
    
    logger.info(f"Research Service started on port {settings.SERVICE_PORT}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Research Service...")
    logger.info("Research Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="AI-powered research service using Perplexity API for deep research on news articles",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Configure rate limiting (Redis-backed)
setup_rate_limiting(app, settings.REDIS_URL)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.

    OPTIMIZATION (Task 404): Fast health checks with timeouts to prevent
    slow external dependencies from blocking the endpoint.
    Target: <100ms for cached checks.

    Provides:
    - Overall service status (healthy/degraded/unhealthy)
    - Detailed checks for all dependencies
    - Rate limiting status
    - API quota information
    """
    import time
    from app.core.database import SessionLocal
    from app.workers.celery_app import celery_app
    import redis
    from sqlalchemy import text

    start_time = time.time()

    health_status = {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
        "config": {
            "rate_limiting": {
                "enabled": settings.RATE_LIMIT_ENABLED,
                "per_minute": settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
                "per_hour": settings.RATE_LIMIT_REQUESTS_PER_HOUR,
                "per_day": settings.RATE_LIMIT_REQUESTS_PER_DAY,
            },
            "cost_tracking": {
                "enabled": settings.ENABLE_COST_TRACKING,
                "max_per_request": settings.MAX_COST_PER_REQUEST,
                "max_daily": settings.MAX_DAILY_COST,
                "max_monthly": settings.MAX_MONTHLY_COST,
            },
            "perplexity_model": settings.PERPLEXITY_DEFAULT_MODEL,
        }
    }

    # 1. Database Check (fast - local connection)
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["checks"]["database"] = {
            "status": "ok",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "error",
            "message": str(e)
        }
        health_status["status"] = "unhealthy"

    # 2. Redis Check (fast - local connection)
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        redis_client.close()
        health_status["checks"]["redis"] = {
            "status": "ok",
            "message": "Redis cache and rate limiting operational"
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "error",
            "message": str(e)
        }
        health_status["status"] = "unhealthy"

    # 3. Celery Check (OPTIMIZATION: cached for 60s to avoid 500ms inspect call)
    global _celery_health_cache, _celery_health_cache_time
    current_time = time.time()
    cache_age = current_time - _celery_health_cache_time

    if _celery_health_cache is not None and cache_age < _celery_health_cache_ttl:
        health_status["checks"]["celery"] = _celery_health_cache
    else:
        try:
            inspect = celery_app.control.inspect(timeout=0.5)
            active_workers = inspect.active()
            if active_workers:
                worker_count = len(active_workers)
                _celery_health_cache = {
                    "status": "ok",
                    "message": f"{worker_count} worker(s) active",
                    "workers": worker_count
                }
            else:
                _celery_health_cache = {
                    "status": "degraded",
                    "message": "No active Celery workers",
                    "workers": 0
                }
                health_status["status"] = "degraded"
            health_status["checks"]["celery"] = _celery_health_cache
            _celery_health_cache_time = current_time
        except Exception as e:
            error_msg = str(e)[:100]
            _celery_health_cache = {
                "status": "degraded",
                "message": f"Celery check timeout/error: {error_msg}",
                "workers": 0
            }
            _celery_health_cache_time = current_time
            health_status["checks"]["celery"] = _celery_health_cache
            health_status["status"] = "degraded"

    # 4. Perplexity API Check (cached for 60s)
    perplexity_available = await perplexity_client.check_health()
    health_status["checks"]["perplexity_api"] = {
        "status": "ok" if perplexity_available else "unavailable",
        "message": "Perplexity API is accessible" if perplexity_available else "Perplexity API unreachable (check API key)"
    }

    # 5. Rate Limiting Status
    try:
        limiter = app.state.rate_limiter
        rate_limit_ok = limiter.redis is not None
        health_status["checks"]["rate_limiting"] = {
            "status": "ok" if rate_limit_ok else "degraded",
            "message": "Rate limiting operational" if rate_limit_ok else "Rate limiter not initialized"
        }
    except Exception as e:
        health_status["checks"]["rate_limiting"] = {
            "status": "error",
            "message": str(e)
        }

    # Calculate response time
    response_time = (time.time() - start_time) * 1000  # Convert to ms
    health_status["response_time_ms"] = round(response_time, 2)

    # Return appropriate HTTP status code
    http_status = 200 if health_status["status"] == "healthy" else (503 if health_status["status"] == "unhealthy" else 200)

    return health_status


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format for monitoring and alerting.
    """
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        from fastapi import Response
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        return {
            "status": "metrics_not_configured",
            "message": "Prometheus metrics not configured",
            "note": "Install prometheus-client to enable metrics"
        }


@app.get("/status/rate-limits")
async def rate_limit_status():
    """
    Get current rate limiting configuration and status.

    Returns:
    - Rate limiting rules per authenticated user
    - Global limits for unauthenticated requests
    - Redis connection status
    """
    from common.rate_limiting import RateLimitConfig

    return {
        "service": settings.SERVICE_NAME,
        "rate_limiting": {
            "enabled": settings.RATE_LIMIT_ENABLED,
            "authenticated_user": {
                "per_minute": RateLimitConfig.USER_RATE_PER_MINUTE,
                "per_hour": RateLimitConfig.USER_RATE_PER_HOUR,
                "description": "Limits applied to authenticated users (JWT token)"
            },
            "unauthenticated": {
                "per_minute": RateLimitConfig.GLOBAL_RATE_PER_MINUTE,
                "per_hour": RateLimitConfig.GLOBAL_RATE_PER_HOUR,
                "description": "Limits applied to unauthenticated requests"
            },
            "note": "Unauthenticated limits are 50% of authenticated limits for fairness"
        },
        "cost_control": {
            "enabled": settings.ENABLE_COST_TRACKING,
            "per_request_limit": f"${settings.MAX_COST_PER_REQUEST:.2f}",
            "daily_limit": f"${settings.MAX_DAILY_COST:.2f}",
            "monthly_limit": f"${settings.MAX_MONTHLY_COST:.2f}",
            "alert_threshold": f"{int(settings.COST_ALERT_THRESHOLD * 100)}%",
            "description": "Cost limits to prevent runaway API expenses"
        },
        "perplexity_api": {
            "model": settings.PERPLEXITY_DEFAULT_MODEL,
            "timeout_seconds": settings.PERPLEXITY_TIMEOUT,
            "max_retries": settings.PERPLEXITY_MAX_RETRIES,
            "description": "Perplexity AI API configuration"
        }
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "description": "AI-powered research service using Perplexity API",
        "documentation": "/docs",
        "health": "/health",
        "status": {
            "rate_limits": "/status/rate-limits",
            "metrics": "/metrics"
        },
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource was not found: {request.url.path}",
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
