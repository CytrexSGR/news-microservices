"""
Tests for user management endpoints.
"""
import pytest
from fastapi import status


class TestListUsers:
    """Tests for listing users."""
    
    def test_list_users_as_admin(self, client, admin_auth_headers, test_user):
        """Test listing users as admin."""
        response = client.get(
            "/api/v1/users",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 1
    
    def test_list_users_as_regular_user(self, client, auth_headers):
        """Test listing users as regular user fails."""
        response = client.get(
            "/api/v1/users",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_users_pagination(self, client, admin_auth_headers):
        """Test user list pagination."""
        response = client.get(
            "/api/v1/users?page=1&page_size=10",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10


class TestGetUser:
    """Tests for getting user by ID."""
    
    def test_get_own_profile(self, client, auth_headers, test_user):
        """Test user can get their own profile."""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
    
    def test_get_other_user_as_regular_user(self, client, auth_headers, admin_user):
        """Test regular user cannot get other user's profile."""
        response = client.get(
            f"/api/v1/users/{admin_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_other_user_as_admin(self, client, admin_auth_headers, test_user):
        """Test admin can get other user's profile."""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
    
    def test_get_nonexistent_user(self, client, admin_auth_headers):
        """Test getting nonexistent user returns 404."""
        response = client.get(
            "/api/v1/users/99999",
            headers=admin_auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateUser:
    """Tests for updating user profile."""
    
    def test_update_own_profile(self, client, auth_headers, test_user):
        """Test user can update their own profile."""
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={
                "first_name": "Updated",
                "last_name": "Name"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
    
    def test_update_other_user_as_regular_user(self, client, auth_headers, admin_user):
        """Test regular user cannot update other user."""
        response = client.put(
            f"/api/v1/users/{admin_user.id}",
            headers=auth_headers,
            json={"first_name": "Hacked"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_other_user_as_admin(self, client, admin_auth_headers, test_user):
        """Test admin can update other user."""
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=admin_auth_headers,
            json={
                "first_name": "Admin",
                "last_name": "Updated"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Admin"
    
    def test_regular_user_cannot_change_active_status(self, client, auth_headers, test_user):
        """Test regular user cannot change their active status."""
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={"is_active": False}
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
