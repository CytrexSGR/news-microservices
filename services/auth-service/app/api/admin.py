"""
Admin API endpoints for Auth Service management.
Includes JWT key rotation and secrets management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.services.jwt import jwt_service
from app.api.dependencies import get_current_active_user
from app.models.auth import User
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


class KeyRotationResponse(BaseModel):
    """Response model for key rotation."""
    success: bool
    message: str
    rotated_at: str = None


@router.post("/rotate-jwt-key", response_model=KeyRotationResponse)
async def rotate_jwt_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger JWT key rotation.

    Requires admin role.

    Process:
    1. Current key becomes previous key
    2. New key is generated
    3. Both keys remain valid during grace period
    4. Old tokens (signed with previous key) remain valid

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Rotation status and metadata
    """
    # Check admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for key rotation"
        )

    try:
        # Perform rotation
        success = await jwt_service.rotate_jwt_key()

        if success:
            from datetime import datetime
            return KeyRotationResponse(
                success=True,
                message="JWT key rotated successfully",
                rotated_at=datetime.utcnow().isoformat()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Key rotation failed"
            )

    except Exception as e:
        logger.error(f"Key rotation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Key rotation failed: {str(e)}"
        )


class RotationStatusResponse(BaseModel):
    """Response model for rotation status."""
    should_rotate: bool
    last_rotation: str = None
    rotation_interval_days: int
    secrets_provider: str


@router.get("/rotation-status", response_model=RotationStatusResponse)
async def get_rotation_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get JWT key rotation status.

    Requires admin role.

    Args:
        current_user: Authenticated user

    Returns:
        Current rotation status
    """
    from app.config import settings

    # Check admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )

    try:
        should_rotate = await jwt_service.auto_rotate_key_if_needed()

        # Get rotation metadata
        if jwt_service._secrets_manager and jwt_service._secrets_manager._key_rotation_date:
            last_rotation = jwt_service._secrets_manager._key_rotation_date.isoformat()
        else:
            last_rotation = None

        return RotationStatusResponse(
            should_rotate=should_rotate,
            last_rotation=last_rotation,
            rotation_interval_days=settings.JWT_ROTATION_INTERVAL_DAYS,
            secrets_provider=settings.SECRETS_PROVIDER
        )

    except Exception as e:
        logger.error(f"Failed to get rotation status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rotation status: {str(e)}"
        )
