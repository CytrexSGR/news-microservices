"""
Unit tests for authentication module.

Tests JWT token validation (P0-1).
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from jose import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import verify_token, get_current_user, require_roles, CurrentUser
from app.core.config import settings


class TestVerifyToken:
    """Tests for verify_token function."""

    @pytest.mark.asyncio
    async def test_verify_token_valid(self, valid_jwt_token):
        """Test that valid token is accepted."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_jwt_token
        )

        payload = await verify_token(credentials)

        assert payload["sub"] == "test-user-123"
        assert "user" in payload["roles"]

    @pytest.mark.asyncio
    async def test_verify_token_expired(self, expired_jwt_token):
        """Test that expired token is rejected."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=expired_jwt_token
        )

        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_verify_token_invalid_signature(self):
        """Test that token with wrong signature is rejected."""
        payload = {
            "sub": "test-user",
            "roles": ["user"],
            "exp": datetime.now(timezone.utc).timestamp() + 3600
        }
        token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )

        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_token_malformed(self):
        """Test that malformed token is rejected."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="not-a-valid-jwt-token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)

        assert exc_info.value.status_code == 401


class TestGetCurrentUser:
    """Tests for get_current_user function."""

    @pytest.mark.asyncio
    async def test_get_current_user_returns_user_object(self):
        """Test that get_current_user returns CurrentUser object."""
        payload = {
            "sub": 123,
            "email": "test@example.com",
            "roles": ["user", "admin"]
        }

        user = await get_current_user(payload)

        assert isinstance(user, CurrentUser)
        assert user.user_id == 123
        assert user.email == "test@example.com"
        assert user.roles == ["user", "admin"]

    @pytest.mark.asyncio
    async def test_get_current_user_missing_sub(self):
        """Test that missing 'sub' raises error."""
        payload = {
            "email": "test@example.com",
            "roles": ["user"]
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(payload)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_accepts_user_id(self):
        """Test that 'user_id' is accepted as fallback for 'sub'."""
        payload = {
            "user_id": 456,
            "email": "test@example.com",
            "roles": ["user"]
        }

        user = await get_current_user(payload)

        assert user.user_id == 456


class TestRequireRoles:
    """Tests for require_roles dependency."""

    @pytest.mark.asyncio
    async def test_require_roles_accepts_matching_role(self):
        """Test that user with required role is accepted."""
        user = CurrentUser(user_id=123, email="test@example.com", roles=["admin"])

        dependency = require_roles("admin")
        result = await dependency(user)

        assert result == user

    @pytest.mark.asyncio
    async def test_require_roles_accepts_any_matching_role(self):
        """Test that user with any of required roles is accepted."""
        user = CurrentUser(user_id=123, email="test@example.com", roles=["user"])

        dependency = require_roles("admin", "user")
        result = await dependency(user)

        assert result == user

    @pytest.mark.asyncio
    async def test_require_roles_rejects_missing_role(self):
        """Test that user without required role is rejected."""
        user = CurrentUser(user_id=123, email="test@example.com", roles=["user"])

        dependency = require_roles("admin")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(user)

        assert exc_info.value.status_code == 403
        assert "insufficient permissions" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_require_roles_empty_user_roles(self):
        """Test that user with no roles is rejected."""
        user = CurrentUser(user_id=123, email="test@example.com", roles=[])

        dependency = require_roles("user")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_roles_superuser_bypasses(self):
        """Test that superuser bypasses role check."""
        user = CurrentUser(user_id=123, email="admin@example.com", roles=["admin"])

        dependency = require_roles("nonexistent_role")
        result = await dependency(user)

        assert result == user  # Superuser (admin role) bypasses
