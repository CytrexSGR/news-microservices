"""
Tests for security utilities: password hashing, JWT tokens, API keys.
"""
import pytest
from datetime import datetime, timedelta
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_api_key,
    hash_api_key,
    verify_api_key
)
from app.config import settings


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_get_password_hash_returns_string(self):
        """Test that hash returns a string."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_get_password_hash_different_each_time(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2

    def test_verify_password_success(self):
        """Test password verification succeeds for correct password."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test password verification fails for incorrect password."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password("WrongPassword123!", hashed) is False

    def test_verify_password_empty_string(self):
        """Test password verification with empty string."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password("", hashed) is False

    def test_password_hashing_with_special_characters(self):
        """Test password hashing with special characters."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_password_hashing_with_unicode(self):
        """Test password hashing with unicode characters."""
        password = "Пароль123!Ñoño"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_password_hashing_with_long_password(self):
        """Test password hashing with password exceeding 72 bytes."""
        # Create password longer than 72 bytes
        password = "A" * 100 + "TestPassword123!"
        hashed = get_password_hash(password)
        # Should truncate and verify
        assert verify_password(password, hashed) is True

    def test_case_sensitive_password_verification(self):
        """Test that password verification is case-sensitive."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password("testpassword123!", hashed) is False

    def test_empty_password_hashing(self):
        """Test hashing an empty password."""
        password = ""
        hashed = get_password_hash(password)
        assert verify_password("", hashed) is True
        assert verify_password("anything", hashed) is False


class TestAccessTokenGeneration:
    """Tests for JWT access token creation and verification."""

    def test_create_access_token_returns_string(self):
        """Test that access token creation returns a string."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expires_delta(self):
        """Test access token creation with custom expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta)

        payload = verify_token(token, "access")
        assert payload is not None
        assert payload["sub"] == "testuser"

    def test_create_access_token_default_expiration(self):
        """Test access token uses default expiration from settings."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        payload = verify_token(token, "access")
        assert payload is not None
        # Verify token has expiration
        assert "exp" in payload

    def test_access_token_contains_required_claims(self):
        """Test that access token contains all required claims."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)

        payload = verify_token(token, "access")
        assert "sub" in payload
        assert "user_id" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "access"

    def test_access_token_type_claim(self):
        """Test that access token has correct type claim."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        payload = verify_token(token, "access")
        assert payload["type"] == "access"

    def test_verify_access_token_with_wrong_type(self):
        """Test verification fails when checking access token as refresh token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # Try to verify as refresh token
        payload = verify_token(token, "refresh")
        assert payload is None

    def test_access_token_expiration(self):
        """Test that expired access tokens are not verified."""
        data = {"sub": "testuser"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta)

        # Should not verify expired token
        payload = verify_token(token, "access")
        assert payload is None

    def test_verify_token_with_invalid_token(self):
        """Test verification fails for invalid token."""
        payload = verify_token("invalid.token.here", "access")
        assert payload is None

    def test_verify_token_with_malformed_token(self):
        """Test verification fails for malformed token."""
        payload = verify_token("not_a_valid_jwt", "access")
        assert payload is None

    def test_verify_token_with_empty_string(self):
        """Test verification fails for empty string."""
        payload = verify_token("", "access")
        assert payload is None

    def test_access_token_preserves_user_data(self):
        """Test that access token preserves custom user data."""
        data = {
            "sub": "testuser",
            "user_id": 123,
            "email": "test@example.com",
            "roles": ["admin", "user"]
        }
        token = create_access_token(data)

        payload = verify_token(token, "access")
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == 123
        assert payload["email"] == "test@example.com"
        assert payload["roles"] == ["admin", "user"]


class TestRefreshTokenGeneration:
    """Tests for JWT refresh token creation and verification."""

    def test_create_refresh_token_returns_string(self):
        """Test that refresh token creation returns a string."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_type_claim(self):
        """Test that refresh token has correct type claim."""
        data = {"sub": "testuser"}
        token = create_refresh_token(data)

        payload = verify_token(token, "refresh")
        assert payload["type"] == "refresh"

    def test_verify_refresh_token_with_wrong_type(self):
        """Test verification fails when checking refresh token as access token."""
        data = {"sub": "testuser"}
        token = create_refresh_token(data)

        # Try to verify as access token
        payload = verify_token(token, "access")
        assert payload is None

    def test_refresh_token_longer_expiration(self):
        """Test that refresh token has longer expiration than access token."""
        data = {"sub": "testuser"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_payload = verify_token(access_token, "access")
        refresh_payload = verify_token(refresh_token, "refresh")

        # Refresh token expiration should be later
        assert refresh_payload["exp"] > access_payload["exp"]

    def test_refresh_token_contains_required_claims(self):
        """Test that refresh token contains required claims."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_refresh_token(data)

        payload = verify_token(token, "refresh")
        assert "sub" in payload
        assert "user_id" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert payload["type"] == "refresh"

    def test_refresh_token_preserves_user_data(self):
        """Test that refresh token preserves custom user data."""
        data = {
            "sub": "testuser",
            "user_id": 123,
            "email": "test@example.com"
        }
        token = create_refresh_token(data)

        payload = verify_token(token, "refresh")
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == 123
        assert payload["email"] == "test@example.com"


class TestAPIKeyGeneration:
    """Tests for API key generation and hashing."""

    def test_generate_api_key_returns_string(self):
        """Test that API key generation returns a string."""
        key = generate_api_key()
        assert isinstance(key, str)
        assert len(key) > 0

    def test_generate_api_key_has_prefix(self):
        """Test that generated API key has correct prefix."""
        key = generate_api_key()
        assert key.startswith(settings.API_KEY_PREFIX)

    def test_generate_api_key_unique(self):
        """Test that each generated API key is unique."""
        key1 = generate_api_key()
        key2 = generate_api_key()
        assert key1 != key2

    def test_hash_api_key_returns_string(self):
        """Test that API key hashing returns a string."""
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_api_key_produces_same_hash_for_same_key(self):
        """Test that hashing same key produces same hash."""
        key = generate_api_key()
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        assert hash1 == hash2

    def test_verify_api_key_success(self):
        """Test API key verification succeeds for correct key."""
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert verify_api_key(key, hashed) is True

    def test_verify_api_key_failure(self):
        """Test API key verification fails for incorrect key."""
        key1 = generate_api_key()
        key2 = generate_api_key()
        hashed = hash_api_key(key1)
        assert verify_api_key(key2, hashed) is False

    def test_verify_api_key_case_sensitive(self):
        """Test that API key verification is case-sensitive."""
        key = generate_api_key()
        hashed = hash_api_key(key)
        # Change case of key
        modified_key = key.swapcase()
        assert verify_api_key(modified_key, hashed) is False

    def test_hash_api_key_different_from_input(self):
        """Test that hash is different from original key."""
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert key != hashed

    def test_api_key_minimum_length(self):
        """Test that generated API key has minimum required length."""
        key = generate_api_key()
        # Should be prefix + random part
        assert len(key) > len(settings.API_KEY_PREFIX) + 10

    def test_hash_api_key_with_empty_string(self):
        """Test hashing empty API key."""
        hashed = hash_api_key("")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_empty_api_key(self):
        """Test verifying empty API key."""
        hashed = hash_api_key("")
        assert verify_api_key("", hashed) is True
        assert verify_api_key("nonempty", hashed) is False


class TestTokenVerification:
    """Tests for token verification edge cases."""

    def test_verify_token_with_none(self):
        """Test verification with None token."""
        # Should not raise exception
        payload = verify_token(None, "access")
        assert payload is None

    def test_verify_token_with_modified_payload(self):
        """Test verification fails if token payload is modified."""
        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)

        # Modify token by changing one character
        modified_token = token[:-5] + "XXXXX"
        payload = verify_token(modified_token, "access")
        assert payload is None

    def test_access_token_not_interchangeable_with_refresh(self):
        """Test that access and refresh tokens are not interchangeable."""
        data = {"sub": "testuser"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        # Each token should only verify with correct type
        assert verify_token(access_token, "access") is not None
        assert verify_token(access_token, "refresh") is None
        assert verify_token(refresh_token, "refresh") is not None
        assert verify_token(refresh_token, "access") is None

    def test_token_iat_claim_present(self):
        """Test that tokens have 'iat' (issued at) claim."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token, "access")
        assert "iat" in payload
        assert isinstance(payload["iat"], int)

    def test_token_contains_timestamp_claims(self):
        """Test that tokens contain valid timestamp claims."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = verify_token(token, "access")

        iat = payload["iat"]
        exp = payload["exp"]

        # Expiration should be after issuance
        assert exp > iat
        # Both should be valid Unix timestamps
        assert isinstance(iat, int)
        assert isinstance(exp, int)
