"""
User and authentication models.

Centralized user management for all services.
"""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Core user model for authentication and authorization.

    Used by auth-service and referenced by all other services.
    """

    __tablename__ = "users"

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))

    # Security
    last_login = Column(String(255))  # Timezone-aware datetime
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(String(255))  # Timezone-aware datetime

    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuthAuditLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Role-based access control roles."""

    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    permissions = Column(Text)  # JSON string of permissions

    # Relationships
    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"


class UserRole(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Association table for User-Role many-to-many relationship."""

    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="roles")
    role = relationship("Role", back_populates="users")

    # Unique constraint
    __table_args__ = (
        Index('idx_user_role_unique', 'user_id', 'role_id', unique=True),
    )

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class APIKey(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """API keys for programmatic access."""

    __tablename__ = "api_keys"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(String(255))  # Timezone-aware datetime
    last_used = Column(String(255))  # Timezone-aware datetime
    usage_count = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class AuthAuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Audit log for authentication and authorization events."""

    __tablename__ = "auth_audit_log"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(255))
    success = Column(Boolean, nullable=False, index=True)
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    error_message = Column(Text)
    extra_data = Column(Text)  # JSON string for additional data

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<AuthAuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}')>"
