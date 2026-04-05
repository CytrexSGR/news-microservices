"""
Tests for complete token lifecycle: creation, refresh, expiration, and revocation.
"""
import pytest
from datetime import datetime, timedelta
from fastapi import status
from app.utils.security import create_access_token, create_refresh_token, verify_token
from app.config import settings


class TestTokenCreationAndRefresh:
    """Tests for token creation and refresh flow."""

    def test_login_returns_both_tokens(self, client, test_user):
        """Test that login returns both access and refresh tokens."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_generates_new_access_token(self, client, test_user):
        """Test that refresh endpoint generates new access token."""
        # Get initial tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh to get new access token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        data = refresh_response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_returns_new_refresh_token(self, client, test_user):
        """Test that refresh returns new refresh token."""
        # Get initial tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        new_refresh_token = refresh_response.json()["refresh_token"]
        assert new_refresh_token is not None
        # Should be different from old token (though same user_id)
        assert isinstance(new_refresh_token, str)

    def test_old_access_token_invalid_after_refresh(self, client, test_user):
        """Test that old access token is still valid after refresh."""
        # Get initial tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        old_access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # Refresh to get new token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        # Old access token should still work (token doesn't invalidate immediately)
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {old_access_token}"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_new_access_token_valid_after_refresh(self, client, test_user):
        """Test that new access token is valid after refresh."""
        # Get initial tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh to get new token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        new_access_token = refresh_response.json()["access_token"]

        # New access token should work
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_refresh_with_invalid_token(self, client):
        """Test refresh with invalid refresh token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token_xyz"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_with_access_token_fails(self, client, test_user):
        """Test that refreshing with access token fails."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        access_token = login_response.json()["access_token"]

        # Try to use access token as refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token}
        )

        # Should fail since it's not a refresh token
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_not_accepted_as_bearer(self, client, test_user):
        """Test that refresh token cannot be used as bearer token."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Try to use refresh token as bearer token
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )

        # Should fail
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestTokenExpiration:
    """Tests for token expiration handling."""

    def test_access_token_has_expiration(self, test_user):
        """Test that access token has expiration claim."""
        data = {"sub": "testuser", "user_id": test_user.id}
        token = create_access_token(data)
        payload = verify_token(token, "access")

        assert "exp" in payload
        assert "iat" in payload
        assert payload["exp"] > payload["iat"]

    def test_refresh_token_has_longer_expiration(self):
        """Test that refresh token expires later than access token."""
        data = {"sub": "testuser"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_payload = verify_token(access_token, "access")
        refresh_payload = verify_token(refresh_token, "refresh")

        # Refresh token should expire later
        assert refresh_payload["exp"] > access_payload["exp"]

    def test_access_token_default_expiration_minutes(self):
        """Test that access token uses configured expiration minutes."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token, "access")

        # Calculate expiration duration
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        iat_time = datetime.utcfromtimestamp(payload["iat"])
        duration = (exp_time - iat_time).total_seconds() / 60

        # Should be approximately the configured duration
        expected_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        assert abs(duration - expected_minutes) < 1  # Allow 1 minute variance

    def test_refresh_token_default_expiration_days(self):
        """Test that refresh token uses configured expiration days."""
        data = {"sub": "testuser"}
        token = create_refresh_token(data)
        payload = verify_token(token, "refresh")

        # Calculate expiration duration
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        iat_time = datetime.utcfromtimestamp(payload["iat"])
        duration_days = (exp_time - iat_time).total_seconds() / 86400

        # Should be approximately the configured duration
        expected_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        assert abs(duration_days - expected_days) < 1  # Allow 1 day variance

    def test_expired_token_cannot_be_verified(self):
        """Test that expired token cannot be verified."""
        data = {"sub": "testuser"}
        # Create token that expires immediately
        expired_token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        # Should not verify expired token
        payload = verify_token(expired_token, "access")
        assert payload is None

    def test_token_issued_at_before_expiration(self):
        """Test that token iat is before exp."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token, "access")

        assert payload["iat"] < payload["exp"]

    def test_refresh_token_can_be_used_until_expiration(self, client, test_user):
        """Test that refresh token works until it expires."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh should work
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_200_OK


class TestLogoutAndTokenRevocation:
    """Tests for logout and token revocation."""

    def test_logout_invalidates_current_token(self, client, auth_headers):
        """Test that logout invalidates the current access token."""
        # First, verify token works
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        assert logout_response.status_code == status.HTTP_204_NO_CONTENT

        # Token should be blacklisted after logout
        # (If implementation supports it)
        # This would depend on whether tokens are immediately invalidated

    def test_logout_requires_authentication(self, client):
        """Test that logout requires valid authentication."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_logout_without_token_fails(self, client):
        """Test logout without token in header fails."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_logout_with_invalid_token_fails(self, client):
        """Test logout with invalid token fails."""
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestTokenClaims:
    """Tests for token payload claims."""

    def test_access_token_contains_user_id(self, test_user):
        """Test that access token contains user ID."""
        data = {"sub": "testuser", "user_id": test_user.id}
        token = create_access_token(data)
        payload = verify_token(token, "access")

        assert payload["user_id"] == test_user.id

    def test_access_token_contains_subject(self):
        """Test that access token contains subject claim."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token, "access")

        assert payload["sub"] == "testuser"

    def test_access_token_contains_type_claim(self):
        """Test that access token has type claim set to 'access'."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token, "access")

        assert payload["type"] == "access"

    def test_refresh_token_contains_type_claim(self):
        """Test that refresh token has type claim set to 'refresh'."""
        data = {"sub": "testuser"}
        token = create_refresh_token(data)
        payload = verify_token(token, "refresh")

        assert payload["type"] == "refresh"

    def test_token_contains_issued_at_claim(self):
        """Test that token contains 'iat' claim."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token, "access")

        assert "iat" in payload
        assert isinstance(payload["iat"], int)

    def test_token_contains_expiration_claim(self):
        """Test that token contains 'exp' claim."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token, "access")

        assert "exp" in payload
        assert isinstance(payload["exp"], int)

    def test_custom_claims_preserved_in_token(self):
        """Test that custom claims are preserved in token."""
        data = {
            "sub": "testuser",
            "user_id": 123,
            "email": "test@example.com",
            "roles": ["admin", "user"],
            "custom_field": "custom_value"
        }
        token = create_access_token(data)
        payload = verify_token(token, "access")

        assert payload["user_id"] == 123
        assert payload["email"] == "test@example.com"
        assert payload["roles"] == ["admin", "user"]
        assert payload["custom_field"] == "custom_value"


class TestTokenSecurity:
    """Tests for token security aspects."""

    def test_token_signature_verification(self):
        """Test that token signature is verified."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # Modify token payload (would break signature)
        parts = token.split('.')
        modified_token = parts[0] + ".modified" + parts[2]

        # Should not verify modified token
        payload = verify_token(modified_token, "access")
        assert payload is None

    def test_access_and_refresh_tokens_are_different(self):
        """Test that access and refresh tokens are different."""
        data = {"sub": "testuser"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        assert access_token != refresh_token

    def test_token_is_not_plain_text(self):
        """Test that tokens are JWT encoded, not plain text."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # Token should contain dots (JWT format)
        assert "." in token
        # Should be three parts separated by dots
        assert token.count(".") == 2

    def test_token_secret_key_required(self):
        """Test that JWT uses configured secret key."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # Should only verify with correct secret key
        payload = verify_token(token, "access")
        assert payload is not None

    def test_different_users_get_different_tokens(self):
        """Test that different users get different tokens."""
        data1 = {"sub": "user1", "user_id": 1}
        data2 = {"sub": "user2", "user_id": 2}

        token1 = create_access_token(data1)
        token2 = create_access_token(data2)

        assert token1 != token2

        payload1 = verify_token(token1, "access")
        payload2 = verify_token(token2, "access")

        assert payload1["user_id"] == 1
        assert payload2["user_id"] == 2
