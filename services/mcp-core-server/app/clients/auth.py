"""Auth service client for MCP Core Server."""

import logging
from typing import Any, Dict, Optional

from ..config import settings
from .base import BaseClient

logger = logging.getLogger(__name__)


class AuthClient(BaseClient):
    """Client for auth-service (Port 8100)."""

    def __init__(self):
        super().__init__(
            service_name="auth-service",
            base_url=settings.auth_service_url,
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout=settings.circuit_breaker_recovery_timeout,
        )

    async def login(
        self,
        username: str,
        password: str,
    ) -> Dict[str, Any]:
        """
        Authenticate user and get JWT tokens.

        Returns:
            Dict with access_token, refresh_token, and user info
        """
        return await self.request(
            "POST",
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )

    async def refresh_token(
        self,
        refresh_token: str,
    ) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Returns:
            Dict with new access_token
        """
        return await self.request(
            "POST",
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    async def logout(
        self,
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Logout user and invalidate tokens.
        """
        return await self.request(
            "POST",
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    async def get_current_user(
        self,
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Get current user profile.
        """
        return await self.request(
            "GET",
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    async def get_auth_stats(
        self,
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Get authentication statistics (admin only).
        """
        return await self.request(
            "GET",
            "/api/v1/auth/stats",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    async def list_api_keys(
        self,
        access_token: str,
    ) -> Dict[str, Any]:
        """
        List user's API keys.
        """
        return await self.request(
            "GET",
            "/api/v1/auth/api-keys",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    async def create_api_key(
        self,
        access_token: str,
        name: str,
        expires_in_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new API key.
        """
        payload = {"name": name}
        if expires_in_days:
            payload["expires_in_days"] = expires_in_days

        return await self.request(
            "POST",
            "/api/v1/auth/api-keys",
            headers={"Authorization": f"Bearer {access_token}"},
            json=payload,
        )

    async def delete_api_key(
        self,
        access_token: str,
        key_id: str,
    ) -> Dict[str, Any]:
        """
        Delete an API key.
        """
        return await self.request(
            "DELETE",
            f"/api/v1/auth/api-keys/{key_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    async def list_users(
        self,
        access_token: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        List all users (admin only).
        """
        return await self.request(
            "GET",
            "/api/v1/users",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"skip": skip, "limit": limit},
        )

    async def get_user(
        self,
        access_token: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Get user by ID (admin only).
        """
        return await self.request(
            "GET",
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    async def register(
        self,
        username: str,
        password: str,
        email: str,
        roles: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            username: Username for the new account
            password: Password (will be hashed)
            email: User's email address
            roles: Optional list of roles (defaults to ["user"])
        """
        payload = {
            "username": username,
            "password": password,
            "email": email,
        }
        if roles:
            payload["roles"] = roles

        return await self.request(
            "POST",
            "/api/v1/auth/register",
            json=payload,
        )

    async def update_user(
        self,
        access_token: str,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        roles: Optional[list] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update user profile (admin only).

        Args:
            access_token: Admin access token
            user_id: User ID to update
            username: New username (optional)
            email: New email (optional)
            roles: New roles (optional)
            is_active: Active status (optional)
        """
        payload = {}
        if username is not None:
            payload["username"] = username
        if email is not None:
            payload["email"] = email
        if roles is not None:
            payload["roles"] = roles
        if is_active is not None:
            payload["is_active"] = is_active

        return await self.request(
            "PUT",
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=payload,
        )

    async def delete_user(
        self,
        access_token: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Delete user account (admin only).

        Args:
            access_token: Admin access token
            user_id: User ID to delete
        """
        return await self.request(
            "DELETE",
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
