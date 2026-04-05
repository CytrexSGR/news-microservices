"""
Centralized Type Validators for Content-Analysis-V3

Normalizes LLM output variations to canonical types.
Used across all Pydantic models for consistent type handling.

This module solves the problem of LLM inconsistency where different
models return variations like "PEOPLE" vs "PERSON", "ORG" vs "ORGANIZATION".
By centralizing normalization here, all Pydantic models maintain
consistent typing for downstream graph and database storage.
"""


class CanonicalTypeValidator:
    """
    Normalize LLM variations to canonical types.

    This class provides static methods to normalize common LLM output
    variations to a consistent canonical form. It handles:

    - Entity types (PERSON, ORGANIZATION, LOCATION, etc.)
    - Relation types (WORKS_FOR, LOCATED_IN, OWNS, etc.)
    - Category types (FINANCE, POLITICS, CONFLICT, etc.)

    Usage:
        from app.models.validators import CanonicalTypeValidator

        # In Pydantic field_validator:
        @field_validator('type', mode='before')
        @classmethod
        def normalize_type(cls, v):
            return CanonicalTypeValidator.normalize_entity_type(v)

    Notes:
        - All methods are case-insensitive (convert to uppercase)
        - Unknown types are returned as-is (uppercased)
        - Mappings can be extended by adding to the class dictionaries
    """

    # Entity type mappings - handles plural forms and common variations
    ENTITY_TYPE_MAPPINGS = {
        # Person variations
        "PEOPLE": "PERSON",
        "PERSONS": "PERSON",
        "INDIVIDUAL": "PERSON",
        "INDIVIDUALS": "PERSON",
        # Organization variations
        "ORGANIZATIONS": "ORGANIZATION",
        "ORG": "ORGANIZATION",
        "ORGS": "ORGANIZATION",
        "COMPANY": "ORGANIZATION",
        "COMPANIES": "ORGANIZATION",
        "CORPORATION": "ORGANIZATION",
        "CORPORATIONS": "ORGANIZATION",
        "INSTITUTION": "ORGANIZATION",
        "INSTITUTIONS": "ORGANIZATION",
        "PLATFORM": "ORGANIZATION",
        "PLATFORMS": "ORGANIZATION",
        "PUBLICATION": "ORGANIZATION",  # News outlets, newspapers
        "PUBLICATIONS": "ORGANIZATION",
        "MEDIA": "ORGANIZATION",
        "NEWSPAPER": "ORGANIZATION",
        "NEWSPAPERS": "ORGANIZATION",
        # Location variations
        "LOCATIONS": "LOCATION",
        "PLACE": "LOCATION",
        "PLACES": "LOCATION",
        "COUNTRY": "LOCATION",
        "COUNTRIES": "LOCATION",
        "CITY": "LOCATION",
        "CITIES": "LOCATION",
        "REGION": "LOCATION",
        "REGIONS": "LOCATION",
        # Event variations
        "EVENTS": "EVENT",
        "INCIDENT": "EVENT",
        "INCIDENTS": "EVENT",
        # Concept variations
        "CONCEPTS": "CONCEPT",
        "IDEA": "CONCEPT",
        "IDEAS": "CONCEPT",
        # Technology variations
        "TECHNOLOGIES": "TECHNOLOGY",
        "TECH": "TECHNOLOGY",
        "TECHS": "TECHNOLOGY",
        # Product variations
        "PRODUCTS": "PRODUCT",
        "SERVICE": "PRODUCT",
        "SERVICES": "PRODUCT",
        "PROGRAM": "PRODUCT",
        "PROGRAMS": "PRODUCT",
        # Currency variations
        "CURRENCIES": "CURRENCY",
        "MONEY": "CURRENCY",
        # Financial instrument variations
        "FINANCIAL_INSTRUMENTS": "FINANCIAL_INSTRUMENT",
        "STOCK": "FINANCIAL_INSTRUMENT",
        "STOCKS": "FINANCIAL_INSTRUMENT",
        "BOND": "FINANCIAL_INSTRUMENT",
        "BONDS": "FINANCIAL_INSTRUMENT",
        # Law/Policy variations
        "LAWS": "LAW",
        "LEGISLATION": "LAW",
        "POLICIES": "POLICY",
        "REGULATION": "POLICY",
        "REGULATIONS": "POLICY",
        # Time variations
        "TIMES": "TIME",
        "DATE": "TIME",
        "DATES": "TIME",
        "PERIOD": "TIME",
        "PERIODS": "TIME",
        # Other/Miscellaneous variations
        "POPULATION": "OTHER",  # Demographic concepts
        "DEMOGRAPHIC": "OTHER",
        "DEMOGRAPHICS": "OTHER",
        "METRIC": "OTHER",
        "METRICS": "OTHER",
        "STATISTIC": "OTHER",
        "STATISTICS": "OTHER",
    }

    # Relation type mappings - handles common variations
    RELATION_TYPE_MAPPINGS = {
        # Employment relations
        "WORKS_AT": "WORKS_FOR",
        "EMPLOYED_BY": "WORKS_FOR",
        "EMPLOYEE_OF": "WORKS_FOR",
        # Location relations
        "LOCATED_AT": "LOCATED_IN",
        "BASED_IN": "LOCATED_IN",
        "HEADQUARTERS_IN": "LOCATED_IN",
        # Ownership relations
        "OWNS": "OWNS",
        "CONTROLS": "OWNS",
        "SUBSIDIARY_OF": "OWNED_BY",
        # Partnership relations
        "PARTNERS_WITH": "PARTNER_OF",
        "ALLIED_WITH": "PARTNER_OF",
        # Competition relations
        "COMPETES_WITH": "COMPETITOR_OF",
        "RIVALS": "COMPETITOR_OF",
    }

    # Category mappings for topics
    CATEGORY_MAPPINGS = {
        "FINANCIAL": "FINANCE",
        "MONETARY": "FINANCE",
        "ECONOMIC": "FINANCE",
        "POLITICAL": "POLITICS",
        "GOVERNMENTAL": "POLITICS",
        "MILITARY": "SECURITY",
        "DEFENSE": "SECURITY",
        "TECHNOLOGICAL": "TECHNOLOGY",
        "DIGITAL": "TECHNOLOGY",
        "MEDICAL": "HEALTH",
        "HEALTHCARE": "HEALTH",
        "HUMANITARIAN_CRISIS": "HUMANITARIAN",
        "REFUGEE": "HUMANITARIAN",
        "WAR": "CONFLICT",
        "WARFARE": "CONFLICT",
        "BATTLE": "CONFLICT",
    }

    @staticmethod
    def normalize_entity_type(v: str) -> str:
        """
        Normalize entity type string to canonical form.

        Args:
            v: Entity type string from LLM (e.g., "PEOPLE", "ORG", "Company")

        Returns:
            Canonical entity type (e.g., "PERSON", "ORGANIZATION")
            Returns input as-is if not a string

        Examples:
            >>> normalize_entity_type("PEOPLE")
            "PERSON"
            >>> normalize_entity_type("company")
            "ORGANIZATION"
        """
        if not isinstance(v, str):
            return v
        v_upper = v.upper().strip()
        return CanonicalTypeValidator.ENTITY_TYPE_MAPPINGS.get(v_upper, v_upper)

    @staticmethod
    def normalize_relation_type(v: str) -> str:
        """
        Normalize relation type string to canonical form.

        Args:
            v: Relation type string from LLM (e.g., "works at", "EMPLOYED_BY")

        Returns:
            Canonical relation type (e.g., "WORKS_FOR")
            Spaces are replaced with underscores

        Examples:
            >>> normalize_relation_type("works at")
            "WORKS_FOR"
            >>> normalize_relation_type("SUBSIDIARY_OF")
            "OWNED_BY"
        """
        if not isinstance(v, str):
            return v
        v_upper = v.upper().strip().replace(" ", "_")
        return CanonicalTypeValidator.RELATION_TYPE_MAPPINGS.get(v_upper, v_upper)

    @staticmethod
    def normalize_category(v: str) -> str:
        """
        Normalize category string to canonical form.

        Args:
            v: Category string from LLM (e.g., "FINANCIAL", "political")

        Returns:
            Canonical category (e.g., "FINANCE", "POLITICS")

        Examples:
            >>> normalize_category("FINANCIAL")
            "FINANCE"
            >>> normalize_category("military")
            "SECURITY"
        """
        if not isinstance(v, str):
            return v
        v_upper = v.upper().strip()
        return CanonicalTypeValidator.CATEGORY_MAPPINGS.get(v_upper, v_upper)
