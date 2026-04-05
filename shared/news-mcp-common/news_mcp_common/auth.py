"""Authentication and authorization utilities for News MCP microservices."""

from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings


class TokenData(BaseModel):
    """JWT token payload data."""
    user_id: int
    email: Optional[str] = None
    roles: list[str] = []
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    jti: Optional[str] = None  # JWT ID for token revocation


class CurrentUser(BaseModel):
    """Current authenticated user data."""
    user_id: int
    email: Optional[str] = None
    roles: list[str] = []
    is_active: bool = True
    is_superuser: bool = False


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class JWTHandler:
    """Handle JWT token operations."""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        expiration_hours: Optional[int] = None,
    ):
        self.secret_key = secret_key or settings.jwt_secret_key
        self.algorithm = algorithm or settings.jwt_algorithm
        self.expiration_hours = expiration_hours or settings.jwt_expiration_hours

    def create_access_token(
        self,
        user_id: int,
        email: Optional[str] = None,
        roles: Optional[list[str]] = None,
        additional_claims: Optional[dict[str, Any]] = None,
    ) -> str:
        """Create a JWT access token."""
        now = datetime.utcnow()
        expire = now + timedelta(hours=self.expiration_hours)

        payload = {
            "sub": str(user_id),  # Subject
            "user_id": user_id,
            "email": email,
            "roles": roles or [],
            "iat": now,
            "exp": expire,
            "type": "access",
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: int,
        jti: Optional[str] = None,
    ) -> str:
        """Create a JWT refresh token."""
        now = datetime.utcnow()
        expire = now + timedelta(days=settings.jwt_refresh_expiration_days)

        payload = {
            "sub": str(user_id),
            "user_id": user_id,
            "iat": now,
            "exp": expire,
            "type": "refresh",
            "jti": jti,  # JWT ID for token revocation
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> TokenData:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return TokenData(**payload)
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def verify_token_type(self, token_data: TokenData, expected_type: str) -> None:
        """Verify token type (access or refresh)."""
        token_type = getattr(token_data, "type", "access")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}, got {token_type}",
            )


# Global JWT handler instance
jwt_handler = JWTHandler()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """Verify JWT token from Authorization header."""
    token = credentials.credentials
    return jwt_handler.decode_token(token)


async def get_current_user(
    token_data: TokenData = Depends(verify_token),
) -> CurrentUser:
    """Get current authenticated user from token."""
    return CurrentUser(
        user_id=token_data.user_id,
        email=token_data.email,
        roles=token_data.roles,
        is_superuser="admin" in token_data.roles or "superuser" in token_data.roles,
    )


def require_roles(*allowed_roles: str):
    """Dependency to require specific roles for access."""
    async def role_checker(current_user: CurrentUser = Depends(get_current_user)):
        # Superusers have access to everything
        if current_user.is_superuser:
            return current_user

        # Check if user has at least one of the allowed roles
        user_roles = set(current_user.roles)
        if not user_roles.intersection(set(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}",
            )
        return current_user

    return role_checker


def require_superuser(current_user: CurrentUser = Depends(get_current_user)):
    """Dependency to require superuser access."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return current_user


class ServiceAuthClient:
    """Client for service-to-service authentication."""

    def __init__(self, service_name: str, service_secret: Optional[str] = None):
        self.service_name = service_name
        self.service_secret = service_secret or settings.jwt_secret_key
        self.jwt_handler = JWTHandler(secret_key=self.service_secret)

    def get_service_token(self, target_service: str) -> str:
        """Get token for service-to-service communication."""
        return self.jwt_handler.create_access_token(
            user_id=0,  # Service user ID
            roles=["service"],
            additional_claims={
                "service_name": self.service_name,
                "target_service": target_service,
                "type": "service",
            }
        )

    def get_auth_header(self, target_service: str) -> dict[str, str]:
        """Get authorization header for service requests."""
        token = self.get_service_token(target_service)
        return {"Authorization": f"Bearer {token}"}


# Export convenience functions
__all__ = [
    "JWTHandler",
    "TokenData",
    "CurrentUser",
    "jwt_handler",
    "hash_password",
    "verify_password",
    "verify_token",
    "get_current_user",
    "require_roles",
    "require_superuser",
    "ServiceAuthClient",
]