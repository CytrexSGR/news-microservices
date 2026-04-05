"""
JWT service for token management with Redis-based blacklisting and Secrets Manager integration.
"""
import redis
from typing import Optional
from app.config import settings
from app.core.secrets_manager import create_secrets_manager, SecretsManager
import logging

logger = logging.getLogger(__name__)


class JWTService:
    """Service for managing JWT tokens and blacklisting with key rotation support."""

    def __init__(self):
        """Initialize Redis connection and Secrets Manager."""
        # Initialize Redis connection for token blacklisting
        try:
            redis_url = settings.get_redis_url()
            self.redis_client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established for JWT service")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

        # Initialize Secrets Manager for JWT key management
        self._secrets_manager: Optional[SecretsManager] = None
        self._initialize_secrets_manager()
    
    def blacklist_token(self, token: str, expiry: int = None) -> bool:
        """
        Add a token to the blacklist.
        
        Args:
            token: JWT token to blacklist
            expiry: Expiry time in seconds (defaults to token expiry from settings)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis not available, token blacklisting disabled")
            return False
        
        try:
            expiry = expiry or settings.REDIS_TOKEN_EXPIRY
            key = f"blacklist:{token}"
            self.redis_client.setex(key, expiry, "1")
            logger.debug(f"Token blacklisted with expiry {expiry}s")
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is blacklisted, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            key = f"blacklist:{token}"
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False
    
    def increment_rate_limit(self, user_id: int) -> Optional[int]:
        """
        Increment rate limit counter for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Current request count or None if Redis unavailable
        """
        if not self.redis_client:
            return None
        
        try:
            key = f"rate_limit:{user_id}"
            count = self.redis_client.incr(key)
            
            # Set expiry on first request
            if count == 1:
                self.redis_client.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)
            
            return count
        except Exception as e:
            logger.error(f"Failed to increment rate limit: {e}")
            return None
    
    def check_rate_limit(self, user_id: int) -> bool:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User ID

        Returns:
            True if rate limit exceeded, False otherwise
        """
        if not settings.RATE_LIMIT_ENABLED or not self.redis_client:
            return False

        try:
            count = self.increment_rate_limit(user_id)
            if count and count > settings.RATE_LIMIT_REQUESTS:
                logger.warning(f"User {user_id} exceeded rate limit: {count} requests")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return False

    def _initialize_secrets_manager(self):
        """Initialize Secrets Manager based on configuration."""
        try:
            self._secrets_manager = create_secrets_manager(
                provider_type=settings.SECRETS_PROVIDER,
                region_name=settings.AWS_REGION,
                vault_addr=settings.VAULT_ADDR,
                vault_token=settings.VAULT_TOKEN,
                jwt_secret_name=settings.JWT_SECRET_NAME
            )
            logger.info(f"Secrets Manager initialized with provider: {settings.SECRETS_PROVIDER}")
        except Exception as e:
            logger.error(f"Failed to initialize Secrets Manager: {e}")
            logger.warning("Falling back to environment-based JWT secret")
            self._secrets_manager = None

    async def get_jwt_secret(self) -> str:
        """
        Get current JWT secret key.

        Returns:
            JWT secret key (from Secrets Manager or fallback to settings)
        """
        if self._secrets_manager:
            try:
                return await self._secrets_manager.get_jwt_secret()
            except Exception as e:
                logger.error(f"Failed to get JWT secret from Secrets Manager: {e}")
                logger.warning("Falling back to settings JWT_SECRET_KEY")

        return settings.JWT_SECRET_KEY

    async def get_jwt_keys_for_validation(self) -> tuple[str, Optional[str]]:
        """
        Get current and previous JWT keys for token validation.

        During key rotation, tokens signed with the previous key remain valid.

        Returns:
            Tuple of (current_key, previous_key)
        """
        if self._secrets_manager:
            try:
                return await self._secrets_manager.get_jwt_keys()
            except Exception as e:
                logger.error(f"Failed to get JWT keys from Secrets Manager: {e}")
                logger.warning("Falling back to settings JWT_SECRET_KEY")

        return settings.JWT_SECRET_KEY, None

    async def rotate_jwt_key(self) -> bool:
        """
        Manually rotate JWT signing key.

        Returns:
            True if rotation successful, False otherwise
        """
        if not self._secrets_manager:
            logger.error("Secrets Manager not initialized, cannot rotate key")
            return False

        try:
            success = await self._secrets_manager.rotate_jwt_key()
            if success:
                logger.info("JWT key rotation completed successfully")
            return success
        except Exception as e:
            logger.error(f"JWT key rotation failed: {e}")
            return False

    async def auto_rotate_key_if_needed(self) -> bool:
        """
        Automatically rotate JWT key if rotation interval has passed.

        Returns:
            True if rotation was performed, False otherwise
        """
        if not settings.JWT_ROTATION_ENABLED or not self._secrets_manager:
            return False

        try:
            rotated = await self._secrets_manager.auto_rotate_if_needed()
            if rotated:
                logger.info("Automatic JWT key rotation completed")
            return rotated
        except Exception as e:
            logger.error(f"Auto rotation failed: {e}")
            return False


# Global JWT service instance
jwt_service = JWTService()
