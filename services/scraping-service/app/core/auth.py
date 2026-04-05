"""
Authentication utilities for Scraping Service.

Issue P0-1: Adds JWT authentication to Wikipedia API endpoints.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import settings

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


class CurrentUser:
    """Current authenticated user."""

    def __init__(
        self,
        user_id: int,
        email: Optional[str] = None,
        roles: list = None
    ):
        self.user_id = user_id
        self.email = email
        self.roles = roles or []
        self.is_superuser = "admin" in self.roles or "superuser" in self.roles


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify JWT token.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    payload: dict = Depends(verify_token)
) -> CurrentUser:
    """
    Get current authenticated user from token.

    Args:
        payload: Decoded JWT payload

    Returns:
        CurrentUser: Current authenticated user

    Raises:
        HTTPException: If token is missing required claims
    """
    # Accept both 'sub' (JWT standard) and 'user_id' for backwards compatibility
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user_id or sub claim"
        )

    return CurrentUser(
        user_id=user_id,
        email=payload.get("email"),
        roles=payload.get("roles", [])
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional)
) -> Optional[CurrentUser]:
    """
    Get user information if token is provided, otherwise return None.

    Useful for endpoints that support both authenticated and anonymous access.

    Args:
        credentials: HTTP Bearer credentials (optional)

    Returns:
        Optional[CurrentUser]: User information or None
    """
    if credentials is None:
        return None

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            return None

        return CurrentUser(
            user_id=user_id,
            email=payload.get("email"),
            roles=payload.get("roles", [])
        )
    except JWTError:
        return None


def require_roles(*allowed_roles: str):
    """
    Dependency to require specific roles.

    Args:
        *allowed_roles: Role names that are allowed access

    Returns:
        Dependency function that checks roles
    """
    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ):
        if current_user.is_superuser:
            return current_user

        user_roles = set(current_user.roles)
        if not user_roles.intersection(set(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}"
            )
        return current_user

    return role_checker
