"""
JWT validation module for microservices authentication.
Week 1 Security Implementation - Shared auth without database dependencies.
"""
from typing import Optional
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel


# Security scheme
security = HTTPBearer()


class UserInfo(BaseModel):
    """User information extracted from JWT token."""
    user_id: int
    email: str
    role: str = "user"
    exp: int


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    secret_key: str = None,
    algorithm: str = "HS256"
) -> UserInfo:
    """
    Verify JWT token and extract user information.

    Args:
        credentials: HTTP Bearer token from request header
        secret_key: JWT secret key (must be provided by service)
        algorithm: JWT algorithm (default: HS256)

    Returns:
        UserInfo: Validated user information

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    if not secret_key:
        raise ValueError("JWT secret_key must be provided")

    token = credentials.credentials

    try:
        # Decode and verify token
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])

        # Extract user information
        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role", "user")
        exp: int = payload.get("exp")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check expiration
        if exp and datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return UserInfo(user_id=user_id, email=email, role=role, exp=exp)

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(secret_key: str, algorithm: str = "HS256"):
    """
    FastAPI dependency factory for JWT authentication.

    Usage in service:
        from shared.auth import get_current_user
        from app.core.config import settings

        # Create dependency
        get_user = get_current_user(
            secret_key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        # Use in endpoint
        @app.get("/protected")
        async def protected_route(user: UserInfo = Depends(get_user)):
            return {"user_id": user.user_id, "email": user.email}

    Args:
        secret_key: JWT secret key from service configuration
        algorithm: JWT algorithm (default: HS256)

    Returns:
        Dependency function that validates JWT and returns UserInfo
    """
    def dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
        return verify_token(credentials, secret_key, algorithm)

    return dependency


def require_role(*allowed_roles: str):
    """
    Role-based access control decorator factory.

    Usage:
        require_admin = require_role("admin")

        @app.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: int,
            current_user: UserInfo = Depends(require_admin(settings.JWT_SECRET_KEY))
        ):
            return {"deleted": user_id}

    Args:
        *allowed_roles: Roles that are allowed to access the endpoint

    Returns:
        Dependency function that checks user role
    """
    def role_checker_factory(secret_key: str, algorithm: str = "HS256"):
        def role_checker(user: UserInfo = Depends(get_current_user(secret_key, algorithm))) -> UserInfo:
            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                )
            return user
        return role_checker
    return role_checker_factory
