# Core module for feed-service
from app.core.redis import get_redis, close_redis

__all__ = ["get_redis", "close_redis"]
