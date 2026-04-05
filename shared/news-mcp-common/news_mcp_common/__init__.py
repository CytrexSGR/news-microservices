"""News MCP Common Library

Shared functionality for News MCP microservices.
"""

__version__ = "0.1.0"

from .auth import JWTHandler, get_current_user, require_roles, verify_token
from .config import settings
from .database import BaseModel, get_db_session, init_db
from .events import EventConsumer, EventPublisher
try:
    from .observability import setup_tracing, track_request
except ImportError:
    import logging as _logging
    _logging.getLogger(__name__).warning("observability module unavailable (OpenTelemetry compat issue)")
    setup_tracing = None
    track_request = None

__all__ = [
    # Auth
    "JWTHandler",
    "get_current_user",
    "require_roles",
    "verify_token",
    # Config
    "settings",
    # Database
    "BaseModel",
    "get_db_session",
    "init_db",
    # Events
    "EventPublisher",
    "EventConsumer",
    # Observability
    "setup_tracing",
    "track_request",
]