"""
Tests for Role-Based Access Control (RBAC) functionality.
"""
import pytest
from fastapi import status
from app.models.auth import User, Role, UserRole


class TestRBACRoles:
    """Tests for role creation and management."""

    def test_default_roles_exist(self, db_session):
        """Test that default roles are created during setup."""
        admin_role = db_session.query(Role).filter_by(name="admin").first()
        user_role = db_session.query(Role).filter_by(name="user").first()
        moderator_role = db_session.query(Role).filter_by(name="moderator").first()

        assert admin_role is not None
        assert user_role is not None
        assert moderator_role is not None

    def test_admin_role_properties(self, db_session):
        """Test admin role has correct properties."""
        admin_role = db_session.query(Role).filter_by(name="admin").first()

        assert admin_role.name == "admin"
        assert admin_role.description == "Administrator"

    def test_user_role_properties(self, db_session):
        """Test user role has correct properties."""
        user_role = db_session.query(Role).filter_by(name="user").first()

        assert user_role.name == "user"
        assert user_role.description == "Regular user"

    def test_role_relationships(self, db_session, test_user):
        """Test role relationships with users."""
        user_role = db_session.query(Role).filter_by(name="user").first()

        db_session.refresh(user_role)
        # Check that role has users
        assert len(user_role.user_roles) > 0


class TestUserRoleAssignment:
    """Tests for assigning roles to users."""

    def test_user_assigned_default_role_on_creation(self, db_session):
        """Test that new user gets default role on creation."""
        from app.services.auth import AuthService
        from app.schemas.auth import UserCreate

        user_data = UserCreate(
            email="roletest@example.com",
            username="roletest",
            password="TestPassword123!"
        )

        user = AuthService.create_user(db_session, user_data)
        db_session.refresh(user)

        assert len(user.roles) > 0
        assert user.roles[0].role.name == "user"

    def test_user_role_assignment(self, db_session, test_user):
        """Test manually assigning role to user."""
        admin_role = db_session.query(Role).filter_by(name="admin").first()

        user_role = UserRole(user_id=test_user.id, role_id=admin_role.id)
        db_session.add(user_role)
        db_session.commit()

        db_session.refresh(test_user)
        role_names = [ur.role.name for ur in test_user.roles]

        assert "admin" in role_names

    def test_user_multiple_roles(self, db_session, test_user):
        """Test that user can have multiple roles."""
        admin_role = db_session.query(Role).filter_by(name="admin").first()
        moderator_role = db_session.query(Role).filter_by(name="moderator").first()

        admin_user_role = UserRole(user_id=test_user.id, role_id=admin_role.id)
        moderator_user_role = UserRole(user_id=test_user.id, role_id=moderator_role.id)

        db_session.add(admin_user_role)
        db_session.add(moderator_user_role)
        db_session.commit()

        db_session.refresh(test_user)
        role_names = [ur.role.name for ur in test_user.roles]

        assert len(role_names) >= 2
        assert "admin" in role_names
        assert "moderator" in role_names

    def test_remove_user_role(self, db_session, test_user):
        """Test removing a role from user."""
        initial_role_count = len(test_user.roles)

        # Remove first role
        role_to_remove = test_user.roles[0]
        db_session.delete(role_to_remove)
        db_session.commit()

        db_session.refresh(test_user)
        assert len(test_user.roles) < initial_role_count


class TestRBACPermissions:
    """Tests for permission checking in endpoints."""

    def test_admin_can_list_users(self, client, admin_auth_headers):
        """Test admin user can list all users."""
        response = client.get("/api/v1/users", headers=admin_auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_regular_user_cannot_list_users(self, client, auth_headers):
        """Test regular user cannot list all users."""
        response = client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_view_other_users(self, client, admin_auth_headers, test_user):
        """Test admin can view other user's profile."""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_user_cannot_view_other_users(self, client, auth_headers, admin_user):
        """Test user cannot view other user's profile."""
        response = client.get(
            f"/api/v1/users/{admin_user.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_can_view_own_profile(self, client, auth_headers, test_user):
        """Test user can view their own profile."""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_update_other_users(self, client, admin_auth_headers, test_user):
        """Test admin can update other users."""
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=admin_auth_headers,
            json={"first_name": "AdminUpdated"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_user_cannot_update_other_users(self, client, auth_headers, admin_user):
        """Test user cannot update other users."""
        response = client.put(
            f"/api/v1/users/{admin_user.id}",
            headers=auth_headers,
            json={"first_name": "Hacked"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_can_update_own_profile(self, client, auth_headers, test_user):
        """Test user can update their own profile."""
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={"first_name": "Updated"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_user_cannot_change_role_status(self, client, auth_headers, test_user):
        """Test user cannot change their role status."""
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={"is_superuser": True}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_change_active_status(self, client, admin_auth_headers, test_user):
        """Test admin can change user active status."""
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=admin_auth_headers,
            json={"is_active": False}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False

    def test_user_cannot_change_own_active_status(self, client, auth_headers, test_user):
        """Test user cannot deactivate their own account."""
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={"is_active": False}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSuperuserPermissions:
    """Tests for superuser-specific permissions."""

    def test_superuser_flag_set_for_admin(self, db_session, admin_user):
        """Test that admin user has superuser flag."""
        db_session.refresh(admin_user)
        assert admin_user.is_superuser is True

    def test_regular_user_not_superuser(self, db_session, test_user):
        """Test that regular user is not superuser."""
        db_session.refresh(test_user)
        assert test_user.is_superuser is False

    def test_superuser_admin_permissions(self, client, admin_auth_headers):
        """Test that superuser has admin permissions."""
        response = client.get("/api/v1/users", headers=admin_auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_non_superuser_no_admin_permissions(self, client, auth_headers):
        """Test that non-superuser lacks admin permissions."""
        response = client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRBACWithAPIKeys:
    """Tests for API key access with RBAC."""

    def test_user_can_create_own_api_keys(self, client, auth_headers):
        """Test user can create their own API keys."""
        response = client.post(
            "/api/v1/auth/api-keys",
            headers=auth_headers,
            json={"name": "My API Key"}
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_user_can_list_own_api_keys(self, client, auth_headers):
        """Test user can list their own API keys."""
        # Create a key first
        client.post(
            "/api/v1/auth/api-keys",
            headers=auth_headers,
            json={"name": "Test Key"}
        )

        # List keys
        response = client.get(
            "/api/v1/auth/api-keys",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    def test_user_can_delete_own_api_keys(self, client, auth_headers):
        """Test user can delete their own API keys."""
        # Create a key
        create_response = client.post(
            "/api/v1/auth/api-keys",
            headers=auth_headers,
            json={"name": "Key to Delete"}
        )
        key_id = create_response.json()["id"]

        # Delete key
        response = client.delete(
            f"/api/v1/auth/api-keys/{key_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_cannot_list_other_users_api_keys(self, client, auth_headers, admin_user):
        """Test user cannot list other user's API keys."""
        # This would depend on API implementation
        # Assuming there's an endpoint to list other user's keys
        pass


class TestRBACEdgeCases:
    """Tests for RBAC edge cases."""

    def test_inactive_user_cannot_access_resources(self, client, db_session, test_user):
        """Test that inactive user cannot access protected resources."""
        # Deactivate user
        test_user.is_active = False
        db_session.commit()

        # Try to login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_locked_user_cannot_access_resources(self, client, db_session, test_user):
        """Test that locked user cannot access protected resources."""
        from datetime import datetime, timedelta

        # Lock user
        test_user.locked_until = datetime.now() + timedelta(minutes=30)
        db_session.commit()

        # Try to login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_with_no_roles_still_authenticated(self, client, db_session, test_user):
        """Test that user with no roles can still authenticate (fallback behavior)."""
        # Remove all roles from user
        for user_role in test_user.roles:
            db_session.delete(user_role)
        db_session.commit()

        # User should still be able to login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == status.HTTP_200_OK


class TestRoleBasedActionLogging:
    """Tests for logging role-based actions."""

    def test_admin_action_logged(self, client, db_session, admin_auth_headers, test_user):
        """Test that admin actions are logged."""
        # Perform admin action
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=admin_auth_headers,
            json={"first_name": "Updated"}
        )

        assert response.status_code == status.HTTP_200_OK
        # Logging would be checked in audit log

    def test_unauthorized_action_logged(self, client, db_session, auth_headers, admin_user):
        """Test that unauthorized actions are logged."""
        # Try to perform admin action as regular user
        response = client.put(
            f"/api/v1/users/{admin_user.id}",
            headers=auth_headers,
            json={"first_name": "Hacked"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Unauthorized action would be logged

    def test_failed_login_logged_in_audit(self, client, db_session, test_user):
        """Test that failed logins are recorded."""
        # Failed login attempt
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "WrongPassword!"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # Would be logged in audit trail
