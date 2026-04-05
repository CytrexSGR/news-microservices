"""Authentication utilities for Research Service."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional

from app.core.config import settings


security = HTTPBearer()


class CurrentUser:
    """Current authenticated user."""
    
    def __init__(self, user_id: int, email: Optional[str] = None, roles: list = None):
        self.user_id = user_id
        self.email = email
        self.roles = roles or []
        self.is_superuser = "admin" in self.roles or "superuser" in self.roles


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token."""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
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


async def get_current_user(payload: dict = Depends(verify_token)) -> CurrentUser:
    """Get current authenticated user from token."""
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


def require_roles(*allowed_roles: str):
    """Dependency to require specific roles."""
    async def role_checker(current_user: CurrentUser = Depends(get_current_user)):
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
