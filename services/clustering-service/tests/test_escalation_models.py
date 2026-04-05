"""Unit tests for escalation SQLAlchemy models.

Tests model instantiation, column types, defaults, and enum values
for the Intelligence Interpretation Layer models:
- EscalationAnchor
- FMPNewsCorrelation
- ArticleCluster escalation columns
"""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.models import (
    ArticleCluster,
    EscalationAnchor,
    EscalationDomain,
    FMPNewsCorrelation,
    CorrelationType,
    FMPRegime,
)


class TestEscalationDomainEnum:
    """Tests for EscalationDomain enum."""

    def test_enum_values(self):
        """Verify EscalationDomain enum has correct values."""
        assert EscalationDomain.GEOPOLITICAL.value == "geopolitical"
        assert EscalationDomain.MILITARY.value == "military"
        assert EscalationDomain.ECONOMIC.value == "economic"

    def test_enum_count(self):
        """Verify there are exactly 3 domains."""
        assert len(EscalationDomain) == 3

    def test_enum_is_string_enum(self):
        """Verify enum values are strings."""
        for domain in EscalationDomain:
            assert isinstance(domain.value, str)


class TestCorrelationTypeEnum:
    """Tests for CorrelationType enum."""

    def test_enum_values(self):
        """Verify CorrelationType enum has correct values."""
        assert CorrelationType.CONFIRMATION.value == "CONFIRMATION"
        assert CorrelationType.DIVERGENCE.value == "DIVERGENCE"
        assert CorrelationType.EARLY_WARNING.value == "EARLY_WARNING"

    def test_enum_count(self):
        """Verify there are exactly 3 correlation types."""
        assert len(CorrelationType) == 3


class TestFMPRegimeEnum:
    """Tests for FMPRegime enum."""

    def test_enum_values(self):
        """Verify FMPRegime enum has correct values."""
        assert FMPRegime.RISK_ON.value == "RISK_ON"
        assert FMPRegime.RISK_OFF.value == "RISK_OFF"
        assert FMPRegime.TRANSITIONAL.value == "TRANSITIONAL"

    def test_enum_count(self):
        """Verify there are exactly 3 regime types."""
        assert len(FMPRegime) == 3


class TestEscalationAnchorModel:
    """Tests for EscalationAnchor SQLAlchemy model."""

    def test_model_exists(self):
        """Verify EscalationAnchor model is importable."""
        assert EscalationAnchor is not None

    def test_tablename(self):
        """Verify correct table name."""
        assert EscalationAnchor.__tablename__ == "escalation_anchors"

    def test_required_columns_exist(self):
        """Verify all required columns are defined."""
        required_columns = [
            "id",
            "domain",
            "level",
            "label",
            "reference_text",
            "embedding",
            "keywords",
            "weight",
            "is_active",
            "created_at",
            "updated_at",
        ]
        for col in required_columns:
            assert hasattr(EscalationAnchor, col), f"Missing column: {col}"

    def test_column_types(self):
        """Verify column types are correct."""
        columns = EscalationAnchor.__table__.columns

        assert str(columns["id"].type) == "UUID"
        assert "VARCHAR" in str(columns["domain"].type).upper()
        assert "INTEGER" in str(columns["level"].type).upper()
        assert "VARCHAR" in str(columns["label"].type).upper()
        assert "TEXT" in str(columns["reference_text"].type).upper()
        assert "VECTOR" in str(columns["embedding"].type).upper()
        assert "ARRAY" in str(columns["keywords"].type).upper()
        assert "NUMERIC" in str(columns["weight"].type).upper()
        assert "BOOLEAN" in str(columns["is_active"].type).upper()

    def test_constraints_defined(self):
        """Verify CHECK constraints are defined."""
        constraint_names = [c.name for c in EscalationAnchor.__table__.constraints]

        # Check constraints should be defined
        assert "chk_anchor_domain" in constraint_names
        assert "chk_anchor_level" in constraint_names
        assert "uq_anchor_domain_level_label" in constraint_names

    def test_repr(self):
        """Verify __repr__ returns expected format."""
        anchor = EscalationAnchor()
        anchor.domain = "geopolitical"
        anchor.level = 3
        anchor.label = "test_label"

        repr_str = repr(anchor)
        assert "geopolitical" in repr_str
        assert "3" in repr_str
        assert "test_label" in repr_str


class TestFMPNewsCorrelationModel:
    """Tests for FMPNewsCorrelation SQLAlchemy model."""

    def test_model_exists(self):
        """Verify FMPNewsCorrelation model is importable."""
        assert FMPNewsCorrelation is not None

    def test_tablename(self):
        """Verify correct table name."""
        assert FMPNewsCorrelation.__tablename__ == "fmp_news_correlations"

    def test_required_columns_exist(self):
        """Verify all required columns are defined."""
        required_columns = [
            "id",
            "detected_at",
            "correlation_type",
            "fmp_regime",
            "escalation_level",
            "confidence",
            "related_clusters",
            "extra_metadata",  # SQLAlchemy attribute (maps to 'metadata' column)
            "expires_at",
            "is_active",
            "created_at",
            "updated_at",
        ]
        for col in required_columns:
            assert hasattr(FMPNewsCorrelation, col), f"Missing column: {col}"

    def test_column_types(self):
        """Verify column types are correct."""
        columns = FMPNewsCorrelation.__table__.columns

        assert str(columns["id"].type) == "UUID"
        # DateTime with timezone maps to TIMESTAMP WITH TIME ZONE in PostgreSQL
        col_type = str(columns["detected_at"].type).upper()
        assert "DATETIME" in col_type or "TIMESTAMP" in col_type
        assert "VARCHAR" in str(columns["correlation_type"].type).upper()
        assert "VARCHAR" in str(columns["fmp_regime"].type).upper()
        assert "INTEGER" in str(columns["escalation_level"].type).upper()
        assert "NUMERIC" in str(columns["confidence"].type).upper()
        assert "ARRAY" in str(columns["related_clusters"].type).upper()
        # The attribute is 'extra_metadata' but the column name is 'metadata'
        assert "JSONB" in str(columns["metadata"].type).upper()
        assert "BOOLEAN" in str(columns["is_active"].type).upper()

    def test_constraints_defined(self):
        """Verify CHECK constraints are defined."""
        constraint_names = [c.name for c in FMPNewsCorrelation.__table__.constraints]

        assert "chk_fmp_correlation_type" in constraint_names
        assert "chk_fmp_regime" in constraint_names
        assert "chk_fmp_escalation_level" in constraint_names
        assert "chk_fmp_confidence" in constraint_names

    def test_repr(self):
        """Verify __repr__ returns expected format."""
        correlation = FMPNewsCorrelation()
        correlation.correlation_type = "DIVERGENCE"
        correlation.fmp_regime = "RISK_OFF"

        repr_str = repr(correlation)
        assert "DIVERGENCE" in repr_str
        assert "RISK_OFF" in repr_str


class TestArticleClusterEscalationColumns:
    """Tests for escalation columns on ArticleCluster model."""

    def test_escalation_columns_exist(self):
        """Verify escalation columns are defined on ArticleCluster."""
        escalation_columns = [
            "escalation_geopolitical",
            "escalation_military",
            "escalation_economic",
            "escalation_combined",
            "escalation_level",
            "escalation_signals",
            "escalation_calculated_at",
        ]
        for col in escalation_columns:
            assert hasattr(ArticleCluster, col), f"Missing column: {col}"

    def test_escalation_column_types(self):
        """Verify escalation column types are correct."""
        columns = ArticleCluster.__table__.columns

        # Numeric columns for domain scores
        assert "NUMERIC" in str(columns["escalation_geopolitical"].type).upper()
        assert "NUMERIC" in str(columns["escalation_military"].type).upper()
        assert "NUMERIC" in str(columns["escalation_economic"].type).upper()
        assert "NUMERIC" in str(columns["escalation_combined"].type).upper()

        # Integer for level
        assert "INTEGER" in str(columns["escalation_level"].type).upper()

        # JSONB for signals
        assert "JSONB" in str(columns["escalation_signals"].type).upper()

        # DateTime with timezone maps to TIMESTAMP WITH TIME ZONE in PostgreSQL
        col_type = str(columns["escalation_calculated_at"].type).upper()
        assert "DATETIME" in col_type or "TIMESTAMP" in col_type

    def test_escalation_columns_nullable(self):
        """Verify escalation columns are nullable."""
        columns = ArticleCluster.__table__.columns

        assert columns["escalation_geopolitical"].nullable is True
        assert columns["escalation_military"].nullable is True
        assert columns["escalation_economic"].nullable is True
        assert columns["escalation_combined"].nullable is True
        assert columns["escalation_level"].nullable is True
        assert columns["escalation_signals"].nullable is True
        assert columns["escalation_calculated_at"].nullable is True


class TestModelImports:
    """Tests for model imports from __init__.py."""

    def test_all_models_importable_from_init(self):
        """Verify all models can be imported from app.models."""
        from app.models import (
            ArticleCluster,
            EscalationAnchor,
            EscalationDomain,
            FMPNewsCorrelation,
            CorrelationType,
            FMPRegime,
        )

        assert ArticleCluster is not None
        assert EscalationAnchor is not None
        assert EscalationDomain is not None
        assert FMPNewsCorrelation is not None
        assert CorrelationType is not None
        assert FMPRegime is not None

    def test_all_exports_in_dunder_all(self):
        """Verify new models are in __all__."""
        from app import models

        assert "EscalationAnchor" in models.__all__
        assert "EscalationDomain" in models.__all__
        assert "FMPNewsCorrelation" in models.__all__
        assert "CorrelationType" in models.__all__
        assert "FMPRegime" in models.__all__
