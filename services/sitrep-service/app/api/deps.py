# services/sitrep-service/app/api/deps.py
"""API dependencies including authentication and database sessions.

Provides FastAPI dependency injection for:
- JWT authentication (get_current_user_id)
- Database sessions (get_db)
- Story aggregator access (get_story_aggregator)

Example usage:
    @router.get("/sitreps")
    async def list_sitreps(
        user_id: str = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db),
    ):
        ...
"""

import logging
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import async_session_maker
from app.services.story_aggregator import StoryAggregator
from app.workers.cluster_consumer import get_aggregator

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for dependency injection.

    Yields:
        AsyncSession: Database session that auto-closes after request

    Example:
        @router.get("/sitreps")
        async def list_sitreps(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        yield session


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Extract and validate user ID from JWT token.

    Validates the JWT token from the Authorization header and extracts
    the user ID from the 'sub' claim.

    Args:
        credentials: HTTP Bearer credentials containing the JWT token

    Returns:
        str: The user ID from the token's 'sub' claim

    Raises:
        HTTPException: 401 if token is invalid or missing user ID

    Example:
        @router.get("/sitreps")
        async def list_sitreps(user_id: str = Depends(get_current_user_id)):
            ...
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


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[str]:
    """
    Optional authentication - returns user_id if valid token provided.

    Useful for endpoints that support both authenticated and
    unauthenticated access.

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        str: User ID if valid token provided, None otherwise

    Example:
        @router.get("/sitreps/latest")
        async def get_latest(user_id: Optional[str] = Depends(get_optional_user_id)):
            ...
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None


def get_story_aggregator() -> StoryAggregator:
    """
    Get the global StoryAggregator instance.

    Returns the aggregator that collects cluster events from RabbitMQ.
    Used for manual SITREP generation.

    Returns:
        StoryAggregator: Global aggregator instance

    Raises:
        HTTPException: 503 if aggregator is not available

    Example:
        @router.post("/sitreps/generate")
        async def generate(aggregator: StoryAggregator = Depends(get_story_aggregator)):
            ...
    """
    aggregator = get_aggregator()
    if aggregator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Story aggregator not available - cluster consumer may not be running",
        )
    return aggregator
