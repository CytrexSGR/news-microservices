"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from app.db.session import get_db
from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse,
    TokenResponse, RefreshTokenRequest,
    APIKeyCreate, APIKeyResponse
)
from app.services.auth import AuthService
from app.services.jwt import jwt_service
from app.utils.security import create_access_token, create_refresh_token, verify_token
from app.config import settings
from app.api.dependencies import get_current_user, get_current_active_user
from app.models.auth import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        request: FastAPI request
        db: Database session
        
    Returns:
        Created user
    """
    try:
        user = AuthService.create_user(db, user_data)
        
        # Log registration
        AuthService.log_auth_event(
            db=db,
            user_id=user.id,
            action="register",
            success=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        
        # Log failed registration
        AuthService.log_auth_event(
            db=db,
            user_id=None,
            action="register",
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access and refresh tokens.
    
    Args:
        user_credentials: User login credentials
        request: FastAPI request
        db: Database session
        
    Returns:
        Access and refresh tokens
    """
    # Authenticate user
    user = AuthService.authenticate_user(
        db,
        user_credentials.username,
        user_credentials.password
    )
    
    if not user:
        # Log failed login
        AuthService.log_auth_event(
            db=db,
            user_id=None,
            action="login",
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_message="Invalid credentials"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user roles
    user_roles = [ur.role.name for ur in user.roles]

    # Create tokens with roles
    token_data = {"sub": str(user.id), "username": user.username, "roles": user_roles}
    access_token = await create_access_token(token_data)
    refresh_token = await create_refresh_token(token_data)
    
    # Log successful login
    AuthService.log_auth_event(
        db=db,
        user_id=user.id,
        action="login",
        success=True,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    logger.info(f"User logged in: {user.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Args:
        token_request: Refresh token request
        db: Database session
        
    Returns:
        New access and refresh tokens
    """
    # Verify refresh token (async function)
    payload = await verify_token(token_request.refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Convert user_id from string to int
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    user = AuthService.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user roles
    user_roles = [ur.role.name for ur in user.roles]

    # Create new tokens with roles
    token_data = {"sub": str(user.id), "username": user.username, "roles": user_roles}
    access_token = await create_access_token(token_data)
    new_refresh_token = await create_refresh_token(token_data)
    
    logger.info(f"Token refreshed for user: {user.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user by blacklisting the token.
    
    Args:
        request: FastAPI request
        current_user: Current authenticated user
        db: Database session
    """
    # Get token from authorization header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        
        # Blacklist token
        jwt_service.blacklist_token(
            token,
            expiry=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    # Log logout
    AuthService.log_auth_event(
        db=db,
        user_id=current_user.id,
        action="logout",
        success=True,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    logger.info(f"User logged out: {current_user.username}")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User profile
    """
    # Refresh user data with relationships
    db.refresh(current_user)
    return current_user


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key for the current user.
    
    Args:
        key_data: API key creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created API key (includes plain key only once)
    """
    api_key, plain_key = AuthService.create_api_key(db, current_user.id, key_data)
    
    # Log API key creation
    AuthService.log_auth_event(
        db=db,
        user_id=current_user.id,
        action="create_api_key",
        success=True
    )
    
    # Return response with plain key
    response = APIKeyResponse.model_validate(api_key)
    response.key = plain_key  # Only returned once
    
    return response


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all API keys for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of API keys (without plain keys)
    """
    api_keys = AuthService.get_user_api_keys(db, current_user.id)
    return api_keys


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an API key.
    
    Args:
        key_id: API key ID
        current_user: Current authenticated user
        db: Database session
    """
    deleted = AuthService.delete_api_key(db, current_user.id, key_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Log API key deletion
    AuthService.log_auth_event(
        db=db,
        user_id=current_user.id,
        action="delete_api_key",
        success=True
    )


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get authentication service statistics.

    Returns:
        Statistics about users
    """
    from sqlalchemy import func

    total_users = db.query(func.count(User.id)).scalar() or 0

    return {
        "total_users": total_users
    }
