"""
Unit Tests for Configuration.

Tests settings loading and validation.
"""
import pytest
from unittest.mock import patch
import os

from app.config import Settings


class TestSettings:
    """Tests for Settings configuration class."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()

        assert settings.APP_NAME == "OSS Service"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.DEBUG is True
        assert settings.ENVIRONMENT == "development"
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8110

    def test_neo4j_default_settings(self):
        """Test default Neo4j settings."""
        settings = Settings()

        assert settings.NEO4J_URI == "bolt://neo4j:7687"
        assert settings.NEO4J_USER == "neo4j"
        assert settings.NEO4J_DATABASE == "neo4j"

    def test_analysis_default_settings(self):
        """Test default analysis settings."""
        settings = Settings()

        assert settings.ANALYSIS_INTERVAL_SECONDS == 3600
        assert settings.MIN_PATTERN_OCCURRENCES == 10
        assert settings.CONFIDENCE_THRESHOLD == 0.7

    def test_logging_default_settings(self):
        """Test default logging settings."""
        settings = Settings()

        assert settings.LOG_LEVEL == "INFO"
        assert settings.LOG_FORMAT == "text"

    def test_settings_from_environment(self):
        """Test settings can be overridden from environment."""
        with patch.dict(os.environ, {
            "APP_NAME": "Custom OSS",
            "PORT": "9999",
            "MIN_PATTERN_OCCURRENCES": "20",
            "CONFIDENCE_THRESHOLD": "0.9",
            "LOG_LEVEL": "DEBUG"
        }):
            settings = Settings()

            assert settings.APP_NAME == "Custom OSS"
            assert settings.PORT == 9999
            assert settings.MIN_PATTERN_OCCURRENCES == 20
            assert settings.CONFIDENCE_THRESHOLD == 0.9
            assert settings.LOG_LEVEL == "DEBUG"

    def test_proposals_api_url_default(self):
        """Test default Proposals API URL."""
        settings = Settings()

        assert "ontology-proposals-service" in settings.PROPOSALS_API_URL
        assert ":8109" in settings.PROPOSALS_API_URL

    def test_settings_from_custom_environment(self):
        """Test custom environment settings."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "PROPOSALS_API_URL": "http://custom-api:8000"
        }):
            settings = Settings()

            assert settings.ENVIRONMENT == "production"
            assert settings.DEBUG is False
            assert settings.PROPOSALS_API_URL == "http://custom-api:8000"


class TestSettingsValidation:
    """Tests for settings validation."""

    def test_confidence_threshold_range(self):
        """Test confidence threshold accepts valid range."""
        with patch.dict(os.environ, {"CONFIDENCE_THRESHOLD": "0.5"}):
            settings = Settings()
            assert settings.CONFIDENCE_THRESHOLD == 0.5

        with patch.dict(os.environ, {"CONFIDENCE_THRESHOLD": "1.0"}):
            settings = Settings()
            assert settings.CONFIDENCE_THRESHOLD == 1.0

    def test_port_is_integer(self):
        """Test port is converted to integer."""
        with patch.dict(os.environ, {"PORT": "8080"}):
            settings = Settings()
            assert isinstance(settings.PORT, int)
            assert settings.PORT == 8080

    def test_analysis_interval_is_integer(self):
        """Test analysis interval is converted to integer."""
        with patch.dict(os.environ, {"ANALYSIS_INTERVAL_SECONDS": "7200"}):
            settings = Settings()
            assert isinstance(settings.ANALYSIS_INTERVAL_SECONDS, int)
            assert settings.ANALYSIS_INTERVAL_SECONDS == 7200
