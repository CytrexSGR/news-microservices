"""Tests for enhanced API endpoints - fragmentation and usage stats."""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch


class TestFragmentationEndpoints:
    """Tests for fragmentation analysis endpoints."""

    @pytest.mark.asyncio
    async def test_get_fragmentation_report(self, client: AsyncClient):
        """GET /fragmentation/report returns metrics."""
        # Setup mock
        mock_report = {
            "entity_type": "ORGANIZATION",
            "fragmentation_score": 0.4,
            "total_entities": 100,
            "total_aliases": 250,
            "avg_aliases_per_entity": 2.5,
            "singleton_count": 30,
            "singleton_percentage": 30.0,
            "potential_duplicates": [],
            "potential_duplicate_count": 0,
            "improvement_target": "30% reduction in singletons"
        }

        with patch("app.api.routes.canonicalization.FragmentationMetrics") as mock_frag:
            mock_instance = MagicMock()
            mock_instance.generate_report = AsyncMock(return_value=mock_report)
            mock_frag.return_value = mock_instance

            response = await client.get(
                "/api/v1/canonicalization/fragmentation/report?entity_type=ORGANIZATION"
            )

            assert response.status_code == 200
            data = response.json()
            assert "fragmentation_score" in data
            assert "total_entities" in data
            assert data["entity_type"] == "ORGANIZATION"
            assert data["fragmentation_score"] == 0.4

    @pytest.mark.asyncio
    async def test_get_potential_duplicates(self, client: AsyncClient):
        """GET /fragmentation/duplicates returns potential duplicates."""
        mock_duplicates = [
            {
                "entity_id_1": 1,
                "name1": "Apple Inc.",
                "entity_id_2": 2,
                "name2": "Apple Inc",
                "similarity": 0.98
            },
            {
                "entity_id_1": 3,
                "name1": "Microsoft Corp",
                "entity_id_2": 4,
                "name2": "Microsoft Corporation",
                "similarity": 0.95
            }
        ]

        with patch("app.api.routes.canonicalization.FragmentationMetrics") as mock_frag:
            mock_instance = MagicMock()
            mock_instance.find_potential_duplicates = AsyncMock(return_value=mock_duplicates)
            mock_frag.return_value = mock_instance

            response = await client.get(
                "/api/v1/canonicalization/fragmentation/duplicates?entity_type=PERSON"
            )

            assert response.status_code == 200
            data = response.json()
            assert "duplicates" in data
            assert isinstance(data["duplicates"], list)
            assert data["count"] == 2

    @pytest.mark.asyncio
    async def test_get_singleton_entities(self, client: AsyncClient):
        """GET /fragmentation/singletons returns high-risk entities."""
        # Create mock singleton entities
        mock_singleton1 = MagicMock()
        mock_singleton1.id = 1
        mock_singleton1.name = "Lonely Entity 1"
        mock_singleton1.type = "LOCATION"
        mock_singleton1.wikidata_id = "Q123"

        mock_singleton2 = MagicMock()
        mock_singleton2.id = 2
        mock_singleton2.name = "Lonely Entity 2"
        mock_singleton2.type = "LOCATION"
        mock_singleton2.wikidata_id = "Q456"

        with patch("app.api.routes.canonicalization.FragmentationMetrics") as mock_frag:
            mock_instance = MagicMock()
            mock_instance.get_singleton_entities = AsyncMock(
                return_value=[mock_singleton1, mock_singleton2]
            )
            mock_frag.return_value = mock_instance

            response = await client.get(
                "/api/v1/canonicalization/fragmentation/singletons?entity_type=LOCATION"
            )

            assert response.status_code == 200
            data = response.json()
            assert "singletons" in data
            assert "count" in data
            assert data["count"] == 2
            assert len(data["singletons"]) == 2


class TestEnhancedStatsEndpoints:
    """Tests for enhanced statistics endpoints."""

    @pytest.mark.asyncio
    async def test_get_usage_stats(self, client: AsyncClient):
        """GET /stats/usage returns usage statistics."""
        # Create mock entities with usage counts
        mock_entity1 = MagicMock()
        mock_entity1.name = "United States"
        mock_entity1.type = "LOCATION"

        mock_entity2 = MagicMock()
        mock_entity2.name = "Germany"
        mock_entity2.type = "LOCATION"

        mock_results = [
            (mock_entity1, 500),
            (mock_entity2, 300)
        ]

        with patch("app.api.routes.canonicalization.AliasStore") as mock_store:
            mock_instance = MagicMock()
            mock_instance.get_most_used_entities = AsyncMock(return_value=mock_results)
            mock_store.return_value = mock_instance

            response = await client.get(
                "/api/v1/canonicalization/stats/usage?entity_type=LOCATION"
            )

            assert response.status_code == 200
            data = response.json()
            assert "most_used_entities" in data
            assert isinstance(data["most_used_entities"], list)

    @pytest.mark.asyncio
    async def test_get_usage_stats_no_entity_type(self, client: AsyncClient):
        """GET /stats/usage without entity_type returns empty list."""
        with patch("app.api.routes.canonicalization.AliasStore") as mock_store:
            mock_instance = MagicMock()
            mock_instance.get_most_used_entities = AsyncMock(return_value=[])
            mock_store.return_value = mock_instance

            response = await client.get("/api/v1/canonicalization/stats/usage")

            assert response.status_code == 200
            data = response.json()
            assert "most_used_entities" in data
            assert data["most_used_entities"] == []
