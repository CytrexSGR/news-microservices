"""
Tests for AuthService business logic.
"""
import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.auth import AuthService
from app.models.auth import User, Role, UserRole, APIKey, AuthAuditLog
from app.schemas.auth import UserCreate, UserUpdate, APIKeyCreate
from app.utils.security import get_password_hash, create_access_token


class TestCreateUser:
    """Tests for user creation."""

    def test_create_user_success(self, db_session):
        """Test successful user creation."""
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            password="TestPassword123!",
            first_name="New",
            last_name="User"
        )

        user = AuthService.create_user(db_session, user_data)

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.first_name == "New"
        assert user.last_name == "User"
        assert user.is_active is True
        assert user.is_superuser is False

    def test_create_user_assigns_default_role(self, db_session):
        """Test that new user gets default 'user' role."""
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            password="TestPassword123!"
        )

        user = AuthService.create_user(db_session, user_data)

        # Refresh and check roles
        db_session.refresh(user)
        assert len(user.roles) > 0
        assert user.roles[0].role.name == "user"

    def test_create_user_duplicate_email(self, db_session, test_user):
        """Test creating user with duplicate email fails."""
        user_data = UserCreate(
            email="test@example.com",  # Same as test_user
            username="differentuser",
            password="TestPassword123!"
        )

        with pytest.raises(HTTPException) as exc:
            AuthService.create_user(db_session, user_data)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_user_duplicate_username(self, db_session, test_user):
        """Test creating user with duplicate username fails."""
        user_data = UserCreate(
            email="different@example.com",
            username="testuser",  # Same as test_user
            password="TestPassword123!"
        )

        with pytest.raises(HTTPException) as exc:
            AuthService.create_user(db_session, user_data)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_user_password_hashed(self, db_session):
        """Test that user password is hashed, not stored in plain text."""
        plain_password = "TestPassword123!"
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            password=plain_password
        )

        user = AuthService.create_user(db_session, user_data)

        # Password should be hashed
        assert user.password_hash != plain_password
        assert len(user.password_hash) > 0

    def test_create_user_sets_timestamps(self, db_session):
        """Test that user creation sets timestamps."""
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            password="TestPassword123!"
        )

        user = AuthService.create_user(db_session, user_data)

        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)


class TestAuthenticateUser:
    """Tests for user authentication."""

    def test_authenticate_user_success(self, db_session, test_user):
        """Test successful user authentication."""
        user = AuthService.authenticate_user(
            db_session,
            "testuser",
            "TestPassword123!"
        )

        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_authenticate_user_with_email(self, db_session, test_user):
        """Test authentication using email instead of username."""
        user = AuthService.authenticate_user(
            db_session,
            "test@example.com",
            "TestPassword123!"
        )

        assert user is not None
        assert user.email == "test@example.com"

    def test_authenticate_user_nonexistent(self, db_session):
        """Test authentication with nonexistent user."""
        user = AuthService.authenticate_user(
            db_session,
            "nonexistent",
            "TestPassword123!"
        )

        assert user is None

    def test_authenticate_user_wrong_password(self, db_session, test_user):
        """Test authentication with wrong password fails."""
        user = AuthService.authenticate_user(
            db_session,
            "testuser",
            "WrongPassword123!"
        )

        assert user is None

    def test_authenticate_user_increments_failed_attempts(self, db_session, test_user):
        """Test that failed login increments failed_login_attempts."""
        initial_attempts = test_user.failed_login_attempts

        AuthService.authenticate_user(
            db_session,
            "testuser",
            "WrongPassword123!"
        )

        db_session.refresh(test_user)
        assert test_user.failed_login_attempts == initial_attempts + 1

    def test_authenticate_user_locks_account_after_5_failed_attempts(self, db_session):
        """Test that account locks after 5 failed attempts."""
        user_data = UserCreate(
            email="locktest@example.com",
            username="lockuser",
            password="TestPassword123!"
        )
        user = AuthService.create_user(db_session, user_data)

        # Try 5 failed authentications
        for _ in range(5):
            AuthService.authenticate_user(db_session, "lockuser", "WrongPassword!")

        db_session.refresh(user)
        assert user.failed_login_attempts >= 5
        assert user.locked_until is not None

    def test_authenticate_user_locked_account(self, db_session):
        """Test that locked account cannot authenticate."""
        user_data = UserCreate(
            email="locked@example.com",
            username="lockeduser",
            password="TestPassword123!"
        )
        user = AuthService.create_user(db_session, user_data)

        # Lock the account
        user.locked_until = datetime.now() + timedelta(minutes=30)
        db_session.commit()

        authenticated_user = AuthService.authenticate_user(
            db_session,
            "lockeduser",
            "TestPassword123!"
        )

        assert authenticated_user is None

    def test_authenticate_user_resets_failed_attempts_on_success(self, db_session):
        """Test that successful login resets failed_login_attempts."""
        user_data = UserCreate(
            email="resettest@example.com",
            username="resetuser",
            password="TestPassword123!"
        )
        user = AuthService.create_user(db_session, user_data)

        # Simulate failed attempts
        user.failed_login_attempts = 2
        db_session.commit()

        # Successful login
        AuthService.authenticate_user(db_session, "resetuser", "TestPassword123!")

        db_session.refresh(user)
        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    def test_authenticate_user_updates_last_login(self, db_session, test_user):
        """Test that successful login updates last_login timestamp."""
        original_last_login = test_user.last_login

        user = AuthService.authenticate_user(
            db_session,
            "testuser",
            "TestPassword123!"
        )

        assert user.last_login is not None
        assert user.last_login != original_last_login

    def test_authenticate_inactive_user(self, db_session):
        """Test that inactive user cannot authenticate."""
        user_data = UserCreate(
            email="inactive@example.com",
            username="inactiveuser",
            password="TestPassword123!"
        )
        user = AuthService.create_user(db_session, user_data)
        user.is_active = False
        db_session.commit()

        authenticated_user = AuthService.authenticate_user(
            db_session,
            "inactiveuser",
            "TestPassword123!"
        )

        assert authenticated_user is None

    def test_authenticate_user_empty_credentials(self, db_session):
        """Test authentication with empty credentials."""
        user = AuthService.authenticate_user(db_session, "", "")
        assert user is None


class TestGetUserOperations:
    """Tests for user retrieval operations."""

    def test_get_user_by_id_success(self, db_session, test_user):
        """Test successful user retrieval by ID."""
        user = AuthService.get_user_by_id(db_session, test_user.id)

        assert user is not None
        assert user.id == test_user.id
        assert user.username == "testuser"

    def test_get_user_by_id_nonexistent(self, db_session):
        """Test retrieving nonexistent user returns None."""
        user = AuthService.get_user_by_id(db_session, 99999)
        assert user is None

    def test_get_user_by_username_success(self, db_session, test_user):
        """Test successful user retrieval by username."""
        user = AuthService.get_user_by_username(db_session, "testuser")

        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_get_user_by_username_nonexistent(self, db_session):
        """Test retrieving user by nonexistent username."""
        user = AuthService.get_user_by_username(db_session, "nonexistent")
        assert user is None

    def test_get_users_pagination(self, db_session, test_user):
        """Test user list pagination."""
        users = AuthService.get_users(db_session, skip=0, limit=10)

        assert len(users) > 0
        assert any(u.username == "testuser" for u in users)

    def test_get_users_empty_result(self, db_session):
        """Test get_users with high offset returns empty list."""
        users = AuthService.get_users(db_session, skip=10000, limit=10)
        assert len(users) == 0


class TestUpdateUser:
    """Tests for user update operations."""

    def test_update_user_success(self, db_session, test_user):
        """Test successful user update."""
        update_data = UserUpdate(first_name="Updated", last_name="Name")

        updated_user = AuthService.update_user(db_session, test_user.id, update_data)

        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.username == "testuser"

    def test_update_user_nonexistent(self, db_session):
        """Test updating nonexistent user fails."""
        update_data = UserUpdate(first_name="New")

        with pytest.raises(HTTPException) as exc:
            AuthService.update_user(db_session, 99999, update_data)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    def test_update_user_sets_updated_at(self, db_session, test_user):
        """Test that user update sets updated_at timestamp."""
        original_updated_at = test_user.updated_at
        update_data = UserUpdate(first_name="New")

        updated_user = AuthService.update_user(db_session, test_user.id, update_data)

        assert updated_user.updated_at is not None
        assert updated_user.updated_at != original_updated_at

    def test_update_user_partial_update(self, db_session, test_user):
        """Test partial user update only changes specified fields."""
        original_email = test_user.email
        update_data = UserUpdate(first_name="New")

        updated_user = AuthService.update_user(db_session, test_user.id, update_data)

        assert updated_user.first_name == "New"
        assert updated_user.email == original_email


class TestAPIKeyOperations:
    """Tests for API key management."""

    def test_create_api_key_success(self, db_session, test_user):
        """Test successful API key creation."""
        key_data = APIKeyCreate(name="Test Key", description="For testing")

        api_key, plain_key = AuthService.create_api_key(db_session, test_user.id, key_data)

        assert api_key.id is not None
        assert api_key.name == "Test Key"
        assert api_key.description == "For testing"
        assert api_key.user_id == test_user.id
        assert api_key.is_active is True
        assert plain_key.startswith("nmc_")

    def test_create_api_key_with_expiry(self, db_session, test_user):
        """Test API key creation with expiration."""
        expires_at = datetime.now() + timedelta(days=30)
        key_data = APIKeyCreate(name="Expiring Key", expires_at=expires_at)

        api_key, plain_key = AuthService.create_api_key(db_session, test_user.id, key_data)

        assert api_key.expires_at is not None

    def test_get_user_api_keys(self, db_session, test_user):
        """Test retrieving user's API keys."""
        # Create a key
        key_data = APIKeyCreate(name="Test Key")
        AuthService.create_api_key(db_session, test_user.id, key_data)

        # Retrieve keys
        keys = AuthService.get_user_api_keys(db_session, test_user.id)

        assert len(keys) > 0
        assert keys[0].name == "Test Key"

    def test_delete_api_key_success(self, db_session, test_user):
        """Test successful API key deletion."""
        # Create a key
        key_data = APIKeyCreate(name="Key to Delete")
        api_key, _ = AuthService.create_api_key(db_session, test_user.id, key_data)

        # Delete key
        deleted = AuthService.delete_api_key(db_session, test_user.id, api_key.id)

        assert deleted is True

    def test_delete_api_key_nonexistent(self, db_session, test_user):
        """Test deleting nonexistent API key."""
        deleted = AuthService.delete_api_key(db_session, test_user.id, 99999)
        assert deleted is False

    def test_delete_api_key_wrong_user(self, db_session, test_user, admin_user):
        """Test user cannot delete another user's API key."""
        # Create key for test_user
        key_data = APIKeyCreate(name="Test Key")
        api_key, _ = AuthService.create_api_key(db_session, test_user.id, key_data)

        # Try to delete as different user
        deleted = AuthService.delete_api_key(db_session, admin_user.id, api_key.id)

        assert deleted is False

    def test_verify_api_key_success(self, db_session, test_user):
        """Test successful API key verification."""
        key_data = APIKeyCreate(name="Test Key")
        api_key, plain_key = AuthService.create_api_key(db_session, test_user.id, key_data)

        # Verify the key
        user = AuthService.verify_api_key(db_session, plain_key)

        assert user is not None
        assert user.id == test_user.id

    def test_verify_api_key_invalid(self, db_session):
        """Test verification of invalid API key."""
        user = AuthService.verify_api_key(db_session, "invalid_key_12345")
        assert user is None

    def test_verify_api_key_updates_usage(self, db_session, test_user):
        """Test that API key verification updates usage count."""
        key_data = APIKeyCreate(name="Test Key")
        api_key, plain_key = AuthService.create_api_key(db_session, test_user.id, key_data)

        initial_count = api_key.usage_count

        AuthService.verify_api_key(db_session, plain_key)

        db_session.refresh(api_key)
        assert api_key.usage_count == initial_count + 1

    def test_verify_expired_api_key(self, db_session, test_user):
        """Test that expired API key cannot be verified."""
        expires_at = datetime.now() - timedelta(days=1)
        key_data = APIKeyCreate(name="Expired Key", expires_at=expires_at)
        api_key, plain_key = AuthService.create_api_key(db_session, test_user.id, key_data)

        user = AuthService.verify_api_key(db_session, plain_key)

        assert user is None

    def test_verify_inactive_api_key(self, db_session, test_user):
        """Test that inactive API key cannot be verified."""
        key_data = APIKeyCreate(name="Inactive Key")
        api_key, plain_key = AuthService.create_api_key(db_session, test_user.id, key_data)

        # Deactivate key
        api_key.is_active = False
        db_session.commit()

        user = AuthService.verify_api_key(db_session, plain_key)

        assert user is None


class TestAuthAuditLogging:
    """Tests for authentication audit logging."""

    def test_log_auth_event_success(self, db_session, test_user):
        """Test logging successful auth event."""
        AuthService.log_auth_event(
            db_session,
            test_user.id,
            "login",
            success=True,
            ip_address="127.0.0.1"
        )

        logs = db_session.query(AuthAuditLog).filter_by(user_id=test_user.id).all()
        assert len(logs) > 0
        assert logs[0].action == "login"
        assert logs[0].success is True
        assert logs[0].ip_address == "127.0.0.1"

    def test_log_auth_event_failure(self, db_session):
        """Test logging failed auth event."""
        AuthService.log_auth_event(
            db_session,
            None,
            "login",
            success=False,
            ip_address="192.168.1.1",
            error_message="Invalid credentials"
        )

        logs = db_session.query(AuthAuditLog).filter_by(action="login").all()
        assert len(logs) > 0
        assert logs[0].success is False
        assert logs[0].error_message == "Invalid credentials"

    def test_log_auth_event_with_user_agent(self, db_session, test_user):
        """Test logging auth event with user agent."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        AuthService.log_auth_event(
            db_session,
            test_user.id,
            "login",
            success=True,
            user_agent=user_agent
        )

        log = db_session.query(AuthAuditLog).filter_by(user_id=test_user.id).first()
        assert log.user_agent == user_agent

    def test_log_auth_event_sets_timestamp(self, db_session, test_user):
        """Test that audit log has timestamp."""
        AuthService.log_auth_event(db_session, test_user.id, "login", success=True)

        log = db_session.query(AuthAuditLog).filter_by(user_id=test_user.id).first()
        assert log.timestamp is not None
        assert isinstance(log.timestamp, datetime)
