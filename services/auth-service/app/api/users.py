"""
User management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from app.db.session import get_db
from app.schemas.auth import UserResponse, UserUpdate, UserListResponse
from app.services.auth import AuthService
from app.api.dependencies import get_current_admin_user, get_current_active_user
from app.models.auth import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).
    
    Args:
        page: Page number
        page_size: Items per page
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Paginated list of users
    """
    skip = (page - 1) * page_size
    users = AuthService.get_users(db, skip=skip, limit=page_size)
    
    # Get total count
    from app.models.auth import User as UserModel
    total = db.query(UserModel).count()
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID.
    Users can only view their own profile unless they are admin.
    
    Args:
        user_id: User ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User profile
    """
    # Check permissions
    if user_id != current_user.id and not current_user.is_superuser:
        # Check if user has admin role
        from app.models.auth import UserRole, Role
        admin_role = db.query(UserRole).join(Role).filter(
            UserRole.user_id == current_user.id,
            Role.name == "admin"
        ).first()
        
        if not admin_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    user = AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Refresh to load relationships
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile.
    Users can only update their own profile unless they are admin.
    
    Args:
        user_id: User ID
        user_data: User update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user profile
    """
    # Check permissions
    if user_id != current_user.id and not current_user.is_superuser:
        # Check if user has admin role
        from app.models.auth import UserRole, Role
        admin_role = db.query(UserRole).join(Role).filter(
            UserRole.user_id == current_user.id,
            Role.name == "admin"
        ).first()
        
        if not admin_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Non-admin users cannot modify is_active
    if not current_user.is_superuser and user_data.is_active is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can modify user active status"
        )
    
    user = AuthService.update_user(db, user_id, user_data)
    
    # Log user update
    AuthService.log_auth_event(
        db=db,
        user_id=current_user.id,
        action="update_user",
        success=True
    )
    
    # Refresh to load relationships
    db.refresh(user)
    return user
