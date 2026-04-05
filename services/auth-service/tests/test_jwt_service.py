"""
Tests for JWT service with Redis integration.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app.services.jwt import JWTService
from app.config import settings


class TestJWTServiceInit:
    """Tests for JWT service initialization."""

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_jwt_service_init_success(self, mock_redis):
        """Test JWT service initializes successfully."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        service = JWTService()

        assert service.redis_client is not None
        mock_redis.assert_called_once()

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_jwt_service_init_redis_connection_failure(self, mock_redis):
        """Test JWT service handles Redis connection failure gracefully."""
        mock_redis.side_effect = Exception("Connection refused")

        service = JWTService()

        # Service should still be usable, but with redis_client = None
        assert service.redis_client is None

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_jwt_service_init_ping_failure(self, mock_redis):
        """Test JWT service handles Redis ping failure."""
        mock_client = Mock()
        mock_client.ping.side_effect = Exception("Redis unavailable")
        mock_redis.return_value = mock_client

        service = JWTService()

        assert service.redis_client is None


class TestBlacklistToken:
    """Tests for token blacklisting."""

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_blacklist_token_success(self, mock_redis):
        """Test successful token blacklisting."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.setex.return_value = True
        mock_redis.return_value = mock_client

        service = JWTService()
        result = service.blacklist_token("test_token_123")

        assert result is True
        mock_client.setex.assert_called_once()

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_blacklist_token_no_redis(self, mock_redis):
        """Test blacklist token returns False when Redis unavailable."""
        mock_redis.side_effect = Exception("Connection failed")

        service = JWTService()
        result = service.blacklist_token("test_token_123")

        assert result is False

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_blacklist_token_with_custom_expiry(self, mock_redis):
        """Test token blacklisting with custom expiry."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.setex.return_value = True
        mock_redis.return_value = mock_client

        service = JWTService()
        custom_expiry = 7200  # 2 hours
        result = service.blacklist_token("test_token_123", expiry=custom_expiry)

        assert result is True
        call_args = mock_client.setex.call_args
        assert call_args[0][1] == custom_expiry  # Check expiry parameter

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_blacklist_token_redis_error(self, mock_redis):
        """Test token blacklisting handles Redis errors gracefully."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.setex.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_client

        service = JWTService()
        result = service.blacklist_token("test_token_123")

        assert result is False

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_blacklist_token_default_expiry(self, mock_redis):
        """Test token blacklisting uses default expiry from settings."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.setex.return_value = True
        mock_redis.return_value = mock_client

        service = JWTService()
        service.blacklist_token("test_token_123")

        call_args = mock_client.setex.call_args
        expiry = call_args[0][1]
        assert expiry == settings.REDIS_TOKEN_EXPIRY

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_blacklist_token_with_special_characters(self, mock_redis):
        """Test blacklisting tokens with special characters."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.setex.return_value = True
        mock_redis.return_value = mock_client

        service = JWTService()
        special_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = service.blacklist_token(special_token)

        assert result is True


class TestIsTokenBlacklisted:
    """Tests for checking token blacklist status."""

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_is_token_blacklisted_true(self, mock_redis):
        """Test checking if token is blacklisted (positive case)."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.exists.return_value = 1
        mock_redis.return_value = mock_client

        service = JWTService()
        result = service.is_token_blacklisted("blacklisted_token")

        assert result is True
        mock_client.exists.assert_called_once()

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_is_token_blacklisted_false(self, mock_redis):
        """Test checking if token is blacklisted (negative case)."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.exists.return_value = 0
        mock_redis.return_value = mock_client

        service = JWTService()
        result = service.is_token_blacklisted("valid_token")

        assert result is False

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_is_token_blacklisted_no_redis(self, mock_redis):
        """Test blacklist check returns False when Redis unavailable."""
        mock_redis.side_effect = Exception("Connection failed")

        service = JWTService()
        result = service.is_token_blacklisted("test_token")

        assert result is False

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_is_token_blacklisted_redis_error(self, mock_redis):
        """Test blacklist check handles Redis errors gracefully."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.exists.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_client

        service = JWTService()
        result = service.is_token_blacklisted("test_token")

        assert result is False

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_is_token_blacklisted_with_empty_string(self, mock_redis):
        """Test blacklist check with empty token string."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.exists.return_value = 0
        mock_redis.return_value = mock_client

        service = JWTService()
        result = service.is_token_blacklisted("")

        assert result is False


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_increment_rate_limit_success(self, mock_redis):
        """Test successful rate limit increment."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.incr.return_value = 1
        mock_redis.return_value = mock_client

        service = JWTService()
        count = service.increment_rate_limit(123)

        assert count == 1
        mock_client.incr.assert_called_once()

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_increment_rate_limit_multiple_times(self, mock_redis):
        """Test multiple rate limit increments."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.incr.side_effect = [1, 2, 3, 4, 5]
        mock_redis.return_value = mock_client

        service = JWTService()

        for i, expected in enumerate([1, 2, 3, 4, 5], 1):
            count = service.increment_rate_limit(123)
            assert count == expected

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_increment_rate_limit_no_redis(self, mock_redis):
        """Test rate limit returns None when Redis unavailable."""
        mock_redis.side_effect = Exception("Connection failed")

        service = JWTService()
        count = service.increment_rate_limit(123)

        assert count is None

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_increment_rate_limit_redis_error(self, mock_redis):
        """Test rate limit handles Redis errors gracefully."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.incr.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_client

        service = JWTService()
        count = service.increment_rate_limit(123)

        assert count is None

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_increment_rate_limit_sets_expiry_on_first_request(self, mock_redis):
        """Test that rate limit expiry is set on first request."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.incr.return_value = 1
        mock_redis.return_value = mock_client

        service = JWTService()
        service.increment_rate_limit(123)

        # Should call expire on first request
        mock_client.expire.assert_called_once()

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_increment_rate_limit_no_expiry_on_subsequent_requests(self, mock_redis):
        """Test that rate limit expiry is not reset on subsequent requests."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.incr.side_effect = [1, 2, 3]
        mock_redis.return_value = mock_client

        service = JWTService()
        service.increment_rate_limit(123)
        service.increment_rate_limit(123)
        service.increment_rate_limit(123)

        # Should only call expire once (first request)
        assert mock_client.expire.call_count == 1

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_check_rate_limit_not_exceeded(self, mock_redis):
        """Test rate limit check when limit not exceeded."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.incr.return_value = 5  # Below limit
        mock_redis.return_value = mock_client

        service = JWTService()
        exceeded = service.check_rate_limit(123)

        # Should return False since count (5) < limit
        assert exceeded is False

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_check_rate_limit_exceeded(self, mock_redis):
        """Test rate limit check when limit is exceeded."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        # Return value higher than settings.RATE_LIMIT_REQUESTS
        mock_client.incr.return_value = settings.RATE_LIMIT_REQUESTS + 1
        mock_redis.return_value = mock_client

        service = JWTService()
        exceeded = service.check_rate_limit(123)

        assert exceeded is True

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_check_rate_limit_disabled(self, mock_redis):
        """Test rate limit check when rate limiting is disabled."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        service = JWTService()

        # Temporarily disable rate limiting
        original_setting = settings.RATE_LIMIT_ENABLED
        settings.RATE_LIMIT_ENABLED = False

        try:
            exceeded = service.check_rate_limit(123)
            assert exceeded is False
            # Should not call increment_rate_limit when disabled
            mock_client.incr.assert_not_called()
        finally:
            settings.RATE_LIMIT_ENABLED = original_setting

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_check_rate_limit_no_redis(self, mock_redis):
        """Test rate limit check returns False when Redis unavailable."""
        mock_redis.side_effect = Exception("Connection failed")

        service = JWTService()
        exceeded = service.check_rate_limit(123)

        assert exceeded is False

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_check_rate_limit_redis_error(self, mock_redis):
        """Test rate limit check handles Redis errors gracefully."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.incr.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_client

        service = JWTService()
        exceeded = service.check_rate_limit(123)

        assert exceeded is False

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_check_rate_limit_with_different_users(self, mock_redis):
        """Test rate limiting tracks different users separately."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        service = JWTService()

        # User 1: 5 requests
        mock_client.incr.return_value = 5
        result1 = service.check_rate_limit(1)

        # User 2: 20 requests
        mock_client.incr.return_value = 20
        result2 = service.check_rate_limit(2)

        # Both calls should be tracked separately
        assert mock_client.incr.call_count == 2

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_increment_rate_limit_with_zero_user_id(self, mock_redis):
        """Test rate limiting with user_id = 0."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.incr.return_value = 1
        mock_redis.return_value = mock_client

        service = JWTService()
        count = service.increment_rate_limit(0)

        assert count == 1
        mock_client.incr.assert_called_once()


class TestJWTServiceIntegration:
    """Integration tests for JWT service operations."""

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_blacklist_and_check_token_flow(self, mock_redis):
        """Test complete token blacklist flow."""
        mock_client = Mock()
        mock_client.ping.return_value = True

        # Setup return values for blacklist and check operations
        mock_client.setex.return_value = True
        mock_client.exists.side_effect = [1]  # Token is blacklisted
        mock_redis.return_value = mock_client

        service = JWTService()

        # Blacklist token
        blacklist_result = service.blacklist_token("test_token_xyz")
        assert blacklist_result is True

        # Check if blacklisted
        is_blacklisted = service.is_token_blacklisted("test_token_xyz")
        assert is_blacklisted is True

    @patch('app.services.jwt.redis.Redis.from_url')
    def test_rate_limit_and_token_blacklist(self, mock_redis):
        """Test concurrent rate limiting and token blacklisting."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.incr.return_value = 5
        mock_client.setex.return_value = True
        mock_client.exists.return_value = 0
        mock_redis.return_value = mock_client

        service = JWTService()

        # Check rate limit
        exceeded = service.check_rate_limit(123)
        assert exceeded is False

        # Blacklist token
        blacklist_result = service.blacklist_token("token_456")
        assert blacklist_result is True

        # Both operations should be tracked
        assert mock_client.incr.called
        assert mock_client.setex.called
