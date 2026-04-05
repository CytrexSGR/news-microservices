"""
Secrets Manager Integration for Auth Service
Supports AWS Secrets Manager and HashiCorp Vault
"""
import os
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class SecretsProvider(ABC):
    """Abstract base class for secrets providers."""

    @abstractmethod
    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve a secret by name."""
        pass

    @abstractmethod
    async def update_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """Update or create a secret."""
        pass


class AWSSecretsManager(SecretsProvider):
    """AWS Secrets Manager implementation."""

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize AWS Secrets Manager client."""
        self.region_name = region_name
        self._client = None

    def _get_client(self):
        """Lazy-load boto3 client."""
        if self._client is None:
            try:
                import boto3
                from botocore.exceptions import ClientError
                self._client = boto3.client('secretsmanager', region_name=self.region_name)
                self._client_error = ClientError
            except ImportError:
                logger.error("boto3 not installed. Install with: pip install boto3")
                raise RuntimeError("AWS SDK (boto3) not available")
        return self._client

    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve secret from AWS Secrets Manager.

        Args:
            secret_name: Name/ARN of the secret

        Returns:
            Dictionary containing secret values

        Raises:
            RuntimeError: If secret cannot be retrieved
        """
        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.get_secret_value,
                SecretId=secret_name
            )

            import json
            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            else:
                # Binary secret (not expected for JWT keys)
                logger.warning(f"Binary secret retrieved for {secret_name}")
                return {"SecretBinary": response['SecretBinary']}

        except self._client_error as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS Secrets Manager error ({error_code}): {e}")
            raise RuntimeError(f"Failed to retrieve secret: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret: {e}")
            raise

    async def update_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """
        Update secret in AWS Secrets Manager.

        Args:
            secret_name: Name/ARN of the secret
            secret_value: New secret value (will be JSON-serialized)

        Returns:
            True if successful

        Raises:
            RuntimeError: If secret cannot be updated
        """
        try:
            import json
            client = self._get_client()

            await asyncio.to_thread(
                client.update_secret,
                SecretId=secret_name,
                SecretString=json.dumps(secret_value)
            )
            logger.info(f"Successfully updated secret: {secret_name}")
            return True

        except self._client_error as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                # Secret doesn't exist, create it
                logger.info(f"Secret not found, creating: {secret_name}")
                await asyncio.to_thread(
                    client.create_secret,
                    Name=secret_name,
                    SecretString=json.dumps(secret_value)
                )
                return True
            else:
                logger.error(f"AWS Secrets Manager error ({error_code}): {e}")
                raise RuntimeError(f"Failed to update secret: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error updating secret: {e}")
            raise


class HashiCorpVault(SecretsProvider):
    """HashiCorp Vault implementation."""

    def __init__(self, vault_addr: str, vault_token: str, mount_point: str = "secret"):
        """
        Initialize Vault client.

        Args:
            vault_addr: Vault server address (e.g., http://localhost:8200)
            vault_token: Vault authentication token
            mount_point: KV secrets engine mount point
        """
        self.vault_addr = vault_addr
        self.vault_token = vault_token
        self.mount_point = mount_point
        self._client = None

    def _get_client(self):
        """Lazy-load hvac client."""
        if self._client is None:
            try:
                import hvac
                self._client = hvac.Client(url=self.vault_addr, token=self.vault_token)
                if not self._client.is_authenticated():
                    raise RuntimeError("Vault authentication failed")
            except ImportError:
                logger.error("hvac not installed. Install with: pip install hvac")
                raise RuntimeError("Vault SDK (hvac) not available")
        return self._client

    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve secret from Vault.

        Args:
            secret_name: Path to the secret in Vault

        Returns:
            Dictionary containing secret values

        Raises:
            RuntimeError: If secret cannot be retrieved
        """
        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.secrets.kv.v2.read_secret_version,
                path=secret_name,
                mount_point=self.mount_point
            )
            return response['data']['data']
        except Exception as e:
            logger.error(f"Vault error retrieving secret {secret_name}: {e}")
            raise RuntimeError(f"Failed to retrieve secret from Vault: {e}")

    async def update_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """
        Update secret in Vault.

        Args:
            secret_name: Path to the secret in Vault
            secret_value: New secret value

        Returns:
            True if successful

        Raises:
            RuntimeError: If secret cannot be updated
        """
        try:
            client = self._get_client()
            await asyncio.to_thread(
                client.secrets.kv.v2.create_or_update_secret,
                path=secret_name,
                secret=secret_value,
                mount_point=self.mount_point
            )
            logger.info(f"Successfully updated secret: {secret_name}")
            return True
        except Exception as e:
            logger.error(f"Vault error updating secret {secret_name}: {e}")
            raise RuntimeError(f"Failed to update secret in Vault: {e}")


class LocalSecretsProvider(SecretsProvider):
    """
    Local file-based secrets provider for development.
    NOT FOR PRODUCTION USE.
    """

    def __init__(self, secrets_dir: str = "/app/secrets"):
        """Initialize local secrets provider."""
        self.secrets_dir = secrets_dir
        os.makedirs(secrets_dir, exist_ok=True)
        logger.warning("Using LocalSecretsProvider - NOT SECURE FOR PRODUCTION")

    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve secret from local file."""
        import json
        secret_path = os.path.join(self.secrets_dir, f"{secret_name}.json")

        if not os.path.exists(secret_path):
            raise RuntimeError(f"Secret not found: {secret_name}")

        with open(secret_path, 'r') as f:
            return json.load(f)

    async def update_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """Update secret in local file."""
        import json
        secret_path = os.path.join(self.secrets_dir, f"{secret_name}.json")

        with open(secret_path, 'w') as f:
            json.dump(secret_value, f, indent=2)

        logger.info(f"Updated local secret: {secret_name}")
        return True


class SecretsManager:
    """
    Unified secrets management interface.
    Handles JWT key rotation and secret retrieval.
    """

    def __init__(self, provider: SecretsProvider, jwt_secret_name: str = "auth-service/jwt-secret"):
        """
        Initialize secrets manager.

        Args:
            provider: Secrets provider implementation
            jwt_secret_name: Name/path of JWT secret in provider
        """
        self.provider = provider
        self.jwt_secret_name = jwt_secret_name
        self._current_key: Optional[str] = None
        self._previous_key: Optional[str] = None
        self._key_rotation_date: Optional[datetime] = None
        self._rotation_interval_days = 30  # Rotate keys every 30 days

    async def get_jwt_secret(self) -> str:
        """
        Get current JWT secret key.

        Returns:
            Current JWT secret key string
        """
        if self._current_key is None:
            await self._load_jwt_keys()
        return self._current_key

    async def get_jwt_keys(self) -> tuple[str, Optional[str]]:
        """
        Get current and previous JWT keys for validation.

        During rotation period, tokens signed with previous key are still valid.

        Returns:
            Tuple of (current_key, previous_key)
        """
        if self._current_key is None:
            await self._load_jwt_keys()
        return self._current_key, self._previous_key

    async def _load_jwt_keys(self):
        """Load JWT keys from secrets provider."""
        try:
            secret_data = await self.provider.get_secret(self.jwt_secret_name)
            self._current_key = secret_data.get('current_key')
            self._previous_key = secret_data.get('previous_key')

            rotation_date_str = secret_data.get('rotation_date')
            if rotation_date_str:
                self._key_rotation_date = datetime.fromisoformat(rotation_date_str)

            if not self._current_key:
                raise RuntimeError("JWT secret missing 'current_key' field")

            logger.info("JWT keys loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load JWT keys: {e}")
            raise

    async def rotate_jwt_key(self, new_key: Optional[str] = None) -> bool:
        """
        Rotate JWT signing key.

        Process:
        1. Current key becomes previous key
        2. New key becomes current key
        3. Tokens signed with previous key remain valid during grace period

        Args:
            new_key: New JWT secret key (auto-generated if not provided)

        Returns:
            True if rotation successful
        """
        try:
            # Load current keys
            if self._current_key is None:
                await self._load_jwt_keys()

            # Generate new key if not provided
            if new_key is None:
                import secrets
                new_key = secrets.token_urlsafe(64)  # 512-bit key

            # Rotate keys
            old_current = self._current_key
            self._current_key = new_key
            self._previous_key = old_current
            self._key_rotation_date = datetime.utcnow()

            # Save to secrets provider
            secret_data = {
                'current_key': self._current_key,
                'previous_key': self._previous_key,
                'rotation_date': self._key_rotation_date.isoformat(),
                'rotation_interval_days': self._rotation_interval_days
            }

            await self.provider.update_secret(self.jwt_secret_name, secret_data)

            logger.info(f"JWT key rotated successfully at {self._key_rotation_date}")
            return True

        except Exception as e:
            logger.error(f"JWT key rotation failed: {e}")
            return False

    async def should_rotate_key(self) -> bool:
        """
        Check if JWT key should be rotated based on rotation interval.

        Returns:
            True if key should be rotated
        """
        if self._key_rotation_date is None:
            await self._load_jwt_keys()

        if self._key_rotation_date is None:
            # No rotation date recorded, consider rotation
            return True

        days_since_rotation = (datetime.utcnow() - self._key_rotation_date).days
        return days_since_rotation >= self._rotation_interval_days

    async def auto_rotate_if_needed(self) -> bool:
        """
        Automatically rotate key if rotation interval has passed.

        Returns:
            True if rotation was performed
        """
        if await self.should_rotate_key():
            logger.info("JWT key rotation interval reached, rotating...")
            return await self.rotate_jwt_key()
        return False


def create_secrets_manager(
    provider_type: str = "local",
    **kwargs
) -> SecretsManager:
    """
    Factory function to create secrets manager with appropriate provider.

    Args:
        provider_type: Type of provider ("aws", "vault", "local")
        **kwargs: Provider-specific configuration

    Returns:
        Configured SecretsManager instance

    Example:
        # AWS Secrets Manager
        sm = create_secrets_manager(
            provider_type="aws",
            region_name="us-east-1"
        )

        # HashiCorp Vault
        sm = create_secrets_manager(
            provider_type="vault",
            vault_addr="http://localhost:8200",
            vault_token="your-token"
        )

        # Local (development only)
        sm = create_secrets_manager(provider_type="local")
    """
    if provider_type == "aws":
        provider = AWSSecretsManager(
            region_name=kwargs.get('region_name', 'us-east-1')
        )
    elif provider_type == "vault":
        provider = HashiCorpVault(
            vault_addr=kwargs.get('vault_addr', os.getenv('VAULT_ADDR', 'http://localhost:8200')),
            vault_token=kwargs.get('vault_token', os.getenv('VAULT_TOKEN', '')),
            mount_point=kwargs.get('mount_point', 'secret')
        )
    elif provider_type == "local":
        provider = LocalSecretsProvider(
            secrets_dir=kwargs.get('secrets_dir', '/app/secrets')
        )
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

    return SecretsManager(
        provider=provider,
        jwt_secret_name=kwargs.get('jwt_secret_name', 'auth-service/jwt-secret')
    )
