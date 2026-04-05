# File: services/feed-service/app/repositories/__init__.py
"""
Repository layer for feed-service.

Provides data access abstractions for:
- Review queue operations (HITL workflow)
"""

from app.repositories.review_repository import ReviewRepository

__all__ = ["ReviewRepository"]
