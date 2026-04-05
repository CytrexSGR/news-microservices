# services/clustering-service/app/api/dependencies.py
"""API dependencies including authentication."""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Extract and validate user ID from JWT token.

    Args:
        credentials: HTTP Bearer credentials containing the JWT token

    Returns:
        str: The user ID from the token's 'sub' claim

    Raises:
        HTTPException: If token is invalid or missing user ID
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")

        if user_id is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception

        return user_id

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise credentials_exception
