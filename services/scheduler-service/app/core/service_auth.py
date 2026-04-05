"""
Service-to-Service Authentication

Provides API key-based authentication for inter-service communication.
Identical pattern to Content Analysis Service.
"""

import secrets
from typing import Optional, Dict
from fastapi import Header, HTTPException, status, Depends
from app.core.config import settings

# Service API Keys (loaded from environment)
VALID_SERVICE_KEYS: Dict[str, str] = {
    "feed-service": settings.FEED_SERVICE_API_KEY if settings.FEED_SERVICE_API_KEY else None,
    "auth-service": settings.AUTH_SERVICE_API_KEY if settings.AUTH_SERVICE_API_KEY else None,
    "content-analysis-service": settings.ANALYSIS_SERVICE_API_KEY if settings.ANALYSIS_SERVICE_API_KEY else None,
}

# Remove None values
VALID_SERVICE_KEYS = {k: v for k, v in VALID_SERVICE_KEYS.items() if v is not None}


async def verify_service_key(
    x_service_key: Optional[str] = Header(None),
    x_service_name: Optional[str] = Header(None)
) -> Dict[str, str]:
    """
    Verify service API key from request headers.

    Headers:
        X-Service-Key: The service's API key
        X-Service-Name: The service's name (optional)

    Returns:
        Service information dict

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_service_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Service API key required (X-Service-Key header)",
            headers={"WWW-Authenticate": "ServiceKey"},
        )

    # Check if key is valid (constant-time comparison)
    service_name = None
    for name, valid_key in VALID_SERVICE_KEYS.items():
        if secrets.compare_digest(x_service_key, valid_key):
            service_name = name
            break

    if not service_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service API key",
            headers={"WWW-Authenticate": "ServiceKey"},
        )

    return {
        "service_name": service_name,
        "authenticated": True,
        "auth_type": "service_api_key"
    }


async def get_service_identity(
    service_info: Dict[str, str] = Depends(verify_service_key)
) -> Dict[str, str]:
    """Get authenticated service identity."""
    return service_info


def require_service(allowed_services: list[str]):
    """
    Dependency to require specific service(s).

    Args:
        allowed_services: List of allowed service names

    Returns:
        Dependency function
    """
    async def service_checker(
        service_info: Dict[str, str] = Depends(get_service_identity)
    ):
        service_name = service_info.get("service_name")

        if service_name not in allowed_services:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Service '{service_name}' not authorized for this endpoint"
            )

        return service_info

    return service_checker


# Convenience dependencies
require_any_internal_service = get_service_identity


def get_service_key_for_outbound(target_service: str) -> Optional[str]:
    """
    Get API key for making outbound requests to another service.

    Args:
        target_service: Target service name

    Returns:
        API key if configured
    """
    key_mapping = {
        "feed-service": settings.FEED_SERVICE_API_KEY,
        "content-analysis-service": settings.ANALYSIS_SERVICE_API_KEY,
        "auth-service": settings.AUTH_SERVICE_API_KEY,
    }
    return key_mapping.get(target_service)


def create_service_headers(target_service: str) -> Dict[str, str]:
    """
    Create headers for service-to-service HTTP requests.

    Args:
        target_service: Name of the service being called

    Returns:
        Headers dict with authentication
    """
    api_key = get_service_key_for_outbound(target_service)

    if not api_key:
        raise ValueError(f"No API key configured for {target_service}")

    return {
        "X-Service-Key": api_key,
        "X-Service-Name": settings.SERVICE_NAME,
        "Content-Type": "application/json"
    }


def list_registered_services() -> list[str]:
    """List all registered services with valid API keys."""
    return list(VALID_SERVICE_KEYS.keys())
