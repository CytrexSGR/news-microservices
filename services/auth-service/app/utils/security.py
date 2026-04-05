"""
Security utilities for password hashing, JWT tokens, and API keys.
"""
from passlib.context import CryptContext
from authlib.jose import jwt, JoseError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib
import bcrypt
from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt directly (bypassing passlib due to version conflict).

    Bcrypt has a 72-byte limit, so we truncate the password if needed.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    # Bcrypt has a 72-byte limit - truncate password if needed
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Use bcrypt directly to avoid passlib version conflict
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using bcrypt directly.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """
    # Bcrypt has a 72-byte limit - truncate password if needed (same as hashing)
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Use bcrypt directly to avoid passlib version conflict
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))


async def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token using dynamically fetched secret.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    from app.services.jwt import jwt_service

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    # Get current JWT secret from Secrets Manager
    secret_key = await jwt_service.get_jwt_secret()

    # authlib uses header dict as first argument
    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}
    encoded_jwt = jwt.encode(header, to_encode, secret_key)

    # authlib returns bytes, decode to string
    return encoded_jwt.decode("utf-8") if isinstance(encoded_jwt, bytes) else encoded_jwt


async def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration using dynamically fetched secret.

    Args:
        data: Data to encode in the token

    Returns:
        Encoded JWT refresh token
    """
    from app.services.jwt import jwt_service

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    # Get current JWT secret from Secrets Manager
    secret_key = await jwt_service.get_jwt_secret()

    # authlib uses header dict as first argument
    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}
    encoded_jwt = jwt.encode(header, to_encode, secret_key)

    # authlib returns bytes, decode to string
    return encoded_jwt.decode("utf-8") if isinstance(encoded_jwt, bytes) else encoded_jwt


async def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token using current and previous keys (supports rotation).

    Args:
        token: JWT token to verify
        token_type: Expected token type (access or refresh)

    Returns:
        Decoded token payload if valid, None otherwise
    """
    from app.services.jwt import jwt_service

    def _decode_with_key(token_str: str, key: str) -> Optional[Dict[str, Any]]:
        """Helper to decode token with a specific key using authlib."""
        try:
            # authlib decode - returns JWTClaims object
            claims = jwt.decode(token_str, key)

            # Validate standard claims (exp, iat, etc.)
            claims.validate()

            # Convert to dict for compatibility
            payload = dict(claims)

            # Verify token type
            if payload.get("type") != token_type:
                return None

            return payload
        except (JoseError, ValueError, Exception):
            return None

    try:
        # Get current and previous keys (for rotation support)
        current_key, previous_key = await jwt_service.get_jwt_keys_for_validation()

        # Try current key first
        result = _decode_with_key(token, current_key)
        if result is not None:
            return result

        # If current key fails and we have a previous key, try it
        if previous_key:
            result = _decode_with_key(token, previous_key)
            if result is not None:
                return result

        return None

    except Exception:
        return None


def generate_api_key() -> str:
    """
    Generate a secure random API key.
    
    Returns:
        API key with prefix
    """
    random_key = secrets.token_urlsafe(settings.API_KEY_LENGTH)
    return f"{settings.API_KEY_PREFIX}{random_key}"


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.
    
    Args:
        api_key: Plain API key
        
    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash.
    
    Args:
        plain_key: Plain API key
        hashed_key: Hashed API key
        
    Returns:
        True if key matches, False otherwise
    """
    return hash_api_key(plain_key) == hashed_key
