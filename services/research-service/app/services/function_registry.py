"""
Registry for specialised research functions.
"""

from typing import Dict, List

from app.services.research import ResearchFunction
from app.services.specialized_functions import SPECIALIZED_FUNCTIONS


def _initialise_registry() -> Dict[str, ResearchFunction]:
    """Instantiate all specialised functions lazily."""
    registry: Dict[str, ResearchFunction] = {}
    for name, func_cls in SPECIALIZED_FUNCTIONS.items():
        registry[name] = func_cls()
    return registry


RESEARCH_FUNCTIONS: Dict[str, ResearchFunction] = _initialise_registry()


def get_function(name: str) -> ResearchFunction:
    """Return registered research function or raise ValueError."""
    try:
        return RESEARCH_FUNCTIONS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown research function: {name}") from exc


def list_functions() -> List[dict]:
    """List available research functions for API exposure."""
    return [
        {
            "name": function.name,
            "description": function.description,
            "default_model": function.model,
            "default_depth": function.depth,
        }
        for function in RESEARCH_FUNCTIONS.values()
    ]

