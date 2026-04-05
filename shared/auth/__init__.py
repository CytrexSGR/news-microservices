"""
Shared authentication module for News Microservices.
Provides JWT validation without database dependencies.
"""
from .jwt_validator import get_current_user, verify_token, UserInfo

__all__ = ["get_current_user", "verify_token", "UserInfo"]
