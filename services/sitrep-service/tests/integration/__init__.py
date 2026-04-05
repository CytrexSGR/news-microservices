# services/sitrep-service/tests/integration/__init__.py
"""Integration tests for SITREP service.

These tests verify end-to-end flows and component integration:
- Event-to-SITREP flow: cluster events -> story aggregation -> report generation
- API with database: Full REST API testing with real database operations
- Scheduled generation: Timer-based SITREP generation flow
"""
