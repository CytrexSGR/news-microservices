"""
MCP Tools Package.

Aggregates all MCP tools from individual modules and exports the tool_registry.
"""

# Import registry first to ensure it's initialized
from .registry import tool_registry, register_tool

# Import all tool modules to register their tools
# The @register_tool decorator adds tools to tool_registry on import
from . import content_analysis
from . import entity_canonicalization
# NOTE: osint module removed 2026-01-03 - osint-service was archived (placeholder only)
from . import intelligence
from . import narrative

# Re-export for backwards compatibility
__all__ = [
    "tool_registry",
    "register_tool",
]
