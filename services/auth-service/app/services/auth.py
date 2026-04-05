"""
Authentication service with business logic.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from app.models.auth import User, Role, UserRole, APIKey, AuthAuditLog
from app.schemas.auth import UserCreate, UserUpdate, APIKeyCreate
from app.utils.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token,
    generate_api_key, hash_api_key
)
from app.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and user management operations."""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User creation data
            
        Returns:
            Created user
            
        Raises:
            HTTPException: If user already exists
        """
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        
        db.add(user)
        db.flush()
        
        # Assign default "user" role
        default_role = db.query(Role).filter_by(name="user").first()
        if default_role:
            user_role = UserRole(user_id=user.id, role_id=default_role.id)
            db.add(user_role)
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created: {user.username} (ID: {user.id})")
        return user
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/email and password.
        
        Args:
            db: Database session
            username: Username or email
            password: Password
            
        Returns:
            User if authenticated, None otherwise
        """
        # Find user by username or email
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return None
        
        # Check if account is locked
        now = datetime.now()
        if user.locked_until and user.locked_until.replace(tzinfo=None) > now:
            logger.warning(f"Login attempt for locked account: {user.username}")
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now() + timedelta(minutes=30)
                logger.warning(f"Account locked due to failed attempts: {user.username}")
            
            db.commit()
            return None
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive account: {user.username}")
            return None
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now()
        db.commit()
        
        logger.info(f"User authenticated: {user.username}")
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get list of users with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of users
        """
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> User:
        """
        Update user information.
        
        Args:
            db: Database session
            user_id: User ID
            user_data: User update data
            
        Returns:
            Updated user
            
        Raises:
            HTTPException: If user not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.now()
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated: {user.username} (ID: {user.id})")
        return user
    
    @staticmethod
    def create_api_key(db: Session, user_id: int, key_data: APIKeyCreate) -> tuple[APIKey, str]:
        """
        Create a new API key for a user.
        
        Args:
            db: Database session
            user_id: User ID
            key_data: API key creation data
            
        Returns:
            Tuple of (APIKey object, plain API key string)
        """
        # Generate API key
        plain_key = generate_api_key()
        key_hash = hash_api_key(plain_key)
        
        # Create API key record
        api_key = APIKey(
            user_id=user_id,
            key_hash=key_hash,
            name=key_data.name,
            description=key_data.description,
            expires_at=key_data.expires_at,
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        logger.info(f"API key created: {key_data.name} for user {user_id}")
        return api_key, plain_key
    
    @staticmethod
    def get_user_api_keys(db: Session, user_id: int) -> List[APIKey]:
        """Get all API keys for a user."""
        return db.query(APIKey).filter(APIKey.user_id == user_id).all()
    
    @staticmethod
    def delete_api_key(db: Session, user_id: int, key_id: int) -> bool:
        """
        Delete an API key.
        
        Args:
            db: Database session
            user_id: User ID
            key_id: API key ID
            
        Returns:
            True if deleted, False if not found
        """
        api_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()
        
        if not api_key:
            return False
        
        db.delete(api_key)
        db.commit()
        
        logger.info(f"API key deleted: {key_id} for user {user_id}")
        return True
    
    @staticmethod
    def verify_api_key(db: Session, plain_key: str) -> Optional[User]:
        """
        Verify an API key and return associated user.
        
        Args:
            db: Database session
            plain_key: Plain API key
            
        Returns:
            User if key is valid, None otherwise
        """
        key_hash = hash_api_key(plain_key)
        api_key = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()
        
        if not api_key:
            return None
        
        # Check expiry
        now = datetime.now()
        if api_key.expires_at and api_key.expires_at.replace(tzinfo=None) < now:
            logger.warning(f"Expired API key used: {api_key.id}")
            return None

        # Update usage
        api_key.last_used = now
        api_key.usage_count += 1
        db.commit()
        
        return api_key.user
    
    @staticmethod
    def log_auth_event(
        db: Session,
        user_id: Optional[int],
        action: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Log an authentication event.
        
        Args:
            db: Database session
            user_id: User ID (optional)
            action: Action performed
            success: Whether action was successful
            ip_address: Client IP address
            user_agent: Client user agent
            error_message: Error message if failed
        """
        log = AuthAuditLog(
            user_id=user_id,
            action=action,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message,
        )
        
        db.add(log)
        db.commit()
