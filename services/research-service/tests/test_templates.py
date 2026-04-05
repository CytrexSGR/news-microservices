"""
Tests for template API endpoints.
"""
import pytest
from fastapi import status
from uuid import uuid4


class TestCreateTemplate:
    """Tests for creating templates."""

    @pytest.mark.asyncio
    async def test_create_template_success(self, client, mock_auth):
        """Test successful template creation."""
        response = client.post(
            "/api/v1/templates/",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "name": "AI Research Template",
                "description": "Template for AI research",
                "query_template": "What are the latest developments in {{topic}}?",
                "parameters": {"topic": "string"},
                "default_model": "sonar",
                "default_depth": "standard"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "AI Research Template"
        assert data["query_template"] == "What are the latest developments in {{topic}}?"
        assert data["parameters"] == {"topic": "string"}
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_public_template(self, client, mock_auth):
        """Test creating public template."""
        response = client.post(
            "/api/v1/templates/",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "name": "Public Template",
                "query_template": "Research {{query}}",
                "parameters": {"query": "string"},
                "is_public": True
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_public"] is True

    @pytest.mark.asyncio
    async def test_create_template_name_too_short(self, client, mock_auth):
        """Test creating template with too short name."""
        response = client.post(
            "/api/v1/templates/",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "name": "AB",
                "query_template": "Test template {{var}}"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_template_without_auth(self, client):
        """Test creating template without authentication."""
        response = client.post(
            "/api/v1/templates/",
            json={
                "name": "Test Template",
                "query_template": "Test {{var}}"
            }
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestListTemplates:
    """Tests for listing templates."""

    @pytest.mark.asyncio
    async def test_list_templates_default(self, client, mock_auth, sample_template):
        """Test listing templates with default parameters."""
        response = client.get(
            "/api/v1/templates/",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(t["id"] == sample_template.id for t in data)

    @pytest.mark.asyncio
    async def test_list_templates_include_public(
        self, client, mock_auth, db_session, test_user_id
    ):
        """Test listing templates including public ones."""
        from app.models.research import ResearchTemplate

        # Create a public template from another user
        public_template = ResearchTemplate(
            user_id=999,  # Different user
            name="Public Template",
            query_template="Public {{query}}",
            parameters={"query": "string"},
            default_model="sonar",
            default_depth="standard",
            is_public=True,
            is_active=True
        )
        db_session.add(public_template)
        db_session.commit()

        response = client.get(
            "/api/v1/templates/?include_public=true",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(t["is_public"] is True for t in data)

    @pytest.mark.asyncio
    async def test_list_templates_exclude_public(
        self, client, mock_auth, sample_template
    ):
        """Test listing only user's templates."""
        response = client.get(
            "/api/v1/templates/?include_public=false",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(t["user_id"] == 1 for t in data)


class TestGetTemplate:
    """Tests for getting specific template."""

    @pytest.mark.asyncio
    async def test_get_template_success(self, client, mock_auth, sample_template):
        """Test getting a specific template."""
        response = client.get(
            f"/api/v1/templates/{sample_template.id}",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_template.id
        assert data["name"] == sample_template.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_template(self, client, mock_auth):
        """Test getting nonexistent template."""
        response = client.get(
            "/api/v1/templates/99999",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_public_template_from_other_user(
        self, client, mock_auth, db_session
    ):
        """Test accessing public template from another user."""
        from app.models.research import ResearchTemplate

        public_template = ResearchTemplate(
            user_id=999,
            name="Other User's Public Template",
            query_template="Public {{query}}",
            parameters={"query": "string"},
            default_model="sonar",
            default_depth="standard",
            is_public=True,
            is_active=True
        )
        db_session.add(public_template)
        db_session.commit()
        db_session.refresh(public_template)

        response = client.get(
            f"/api/v1/templates/{public_template.id}",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_200_OK


class TestUpdateTemplate:
    """Tests for updating templates."""

    @pytest.mark.asyncio
    async def test_update_template_success(self, client, mock_auth, sample_template):
        """Test successful template update."""
        response = client.put(
            f"/api/v1/templates/{sample_template.id}",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "name": "Updated Template Name",
                "description": "Updated description"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Template Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_nonexistent_template(self, client, mock_auth):
        """Test updating nonexistent template."""
        response = client.put(
            "/api/v1/templates/99999",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={"name": "New Name"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_other_users_template(
        self, client, mock_auth, db_session
    ):
        """Test updating another user's template should fail."""
        from app.models.research import ResearchTemplate

        other_template = ResearchTemplate(
            user_id=999,
            name="Other User's Template",
            query_template="Test {{var}}",
            parameters={},
            default_model="sonar",
            default_depth="standard",
            is_active=True
        )
        db_session.add(other_template)
        db_session.commit()
        db_session.refresh(other_template)

        response = client.put(
            f"/api/v1/templates/{other_template.id}",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={"name": "Hacked Name"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteTemplate:
    """Tests for deleting templates."""

    @pytest.mark.asyncio
    async def test_delete_template_success(self, client, mock_auth, sample_template):
        """Test successful template deletion."""
        response = client.delete(
            f"/api/v1/templates/{sample_template.id}",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_delete_nonexistent_template(self, client, mock_auth):
        """Test deleting nonexistent template."""
        response = client.delete(
            "/api/v1/templates/99999",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPreviewTemplate:
    """Tests for template preview."""

    @pytest.mark.asyncio
    async def test_preview_template_success(self, client, mock_auth, sample_template):
        """Test template preview."""
        response = client.post(
            f"/api/v1/templates/{sample_template.id}/preview",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "variables": {
                    "topic": "artificial intelligence",
                    "aspect": "recent breakthroughs"
                }
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "rendered_query" in data
        assert "artificial intelligence" in data["rendered_query"]
        assert "recent breakthroughs" in data["rendered_query"]
        assert "estimated_cost" in data

    @pytest.mark.asyncio
    async def test_preview_with_custom_model(self, client, mock_auth, sample_template):
        """Test preview with custom model."""
        response = client.post(
            f"/api/v1/templates/{sample_template.id}/preview",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "variables": {"topic": "AI", "aspect": "ethics"},
                "model_name": "sonar-pro"
            }
        )

        assert response.status_code == status.HTTP_200_OK


class TestApplyTemplate:
    """Tests for applying templates."""

    @pytest.mark.asyncio
    async def test_apply_template_success(
        self, client, mock_auth, sample_template, mock_perplexity_client, disable_cost_tracking
    ):
        """Test applying template and creating research task."""
        response = client.post(
            f"/api/v1/templates/{sample_template.id}/apply",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "variables": {
                    "topic": "quantum computing",
                    "aspect": "practical applications"
                }
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "query" in data
        assert "quantum computing" in data["query"]
        assert data["status"] == "completed"
        assert "result" in data

    @pytest.mark.asyncio
    async def test_apply_template_with_feed_id(
        self, client, mock_auth, sample_template, mock_perplexity_client, disable_cost_tracking
    ):
        """Test applying template with feed_id."""
        feed_uuid = str(uuid4())
        response = client.post(
            f"/api/v1/templates/{sample_template.id}/apply",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "variables": {"topic": "AI", "aspect": "ethics"},
                "feed_id": feed_uuid
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["feed_id"] == feed_uuid

    @pytest.mark.asyncio
    async def test_apply_nonexistent_template(self, client, mock_auth):
        """Test applying nonexistent template."""
        response = client.post(
            f"/api/v1/templates/{uuid4()}/apply",
            headers={"Authorization": "Bearer mock.jwt.token"},
            json={
                "variables": {"topic": "test"}
            }
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
