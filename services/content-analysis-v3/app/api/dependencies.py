"""
FastAPI dependencies for Content-Analysis-V3.
Includes JWT authentication using shared auth module.
"""
import sys
import os

# Add shared module to path
shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

from fastapi import Depends, HTTPException, status
from typing import Optional

# Import shared auth module
try:
    from auth.jwt_validator import get_current_user, UserInfo, require_role

    # Import settings after auth module
    import sys
    import os
    sys.path.insert(0, '/app')
    from app.core.config import settings

    # Create dependency with service's JWT secret
    get_authenticated_user = get_current_user(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    # Create admin role checker
    require_admin_role = require_role("admin")(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

except ImportError as e:
    # Fallback if shared auth not available
    import logging
    logging.error(f"Failed to import shared auth module: {e}")

    # Define fallback UserInfo
    from pydantic import BaseModel

    class UserInfo(BaseModel):
        user_id: int
        email: str
        role: str = "user"

    # Fallback dependency that raises error
    def get_authenticated_user():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not available - shared auth module not found"
        )


def get_optional_authenticated_user(
    user: Optional[UserInfo] = Depends(get_authenticated_user)
) -> Optional[UserInfo]:
    """
    Optional authentication dependency.
    Returns None if no auth provided, otherwise validates token.
    """
    return user


def require_admin(
    user: UserInfo = Depends(get_authenticated_user)
) -> UserInfo:
    """
    Require admin role for endpoint access.

    Args:
        user: Authenticated user

    Returns:
        User if admin, raises HTTPException otherwise

    Raises:
        HTTPException: 403 if user is not admin
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return user
