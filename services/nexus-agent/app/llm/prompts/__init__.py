"""Prompt templates for NEXUS Agent."""

from pathlib import Path
from typing import List, Dict

PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_file = PROMPTS_DIR / f"{name}.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt template not found: {name}")
    return prompt_file.read_text()


def format_tool_selection_prompt(tool_descriptions: List[Dict[str, str]]) -> str:
    """Format the tool selection prompt with available tools."""
    prompt_template = load_prompt("tool_selection")

    # Format tool descriptions
    tool_desc_lines = []
    for tool in tool_descriptions:
        tool_desc_lines.append(f"- **{tool['name']}**: {tool['description']}")

    tool_desc_text = "\n".join(tool_desc_lines)
    return prompt_template.replace("{tool_descriptions}", tool_desc_text)


# Pre-load common prompts
GATEKEEPER_PROMPT = load_prompt("gatekeeper")
BRAIN_RESPONSE_PROMPT = load_prompt("brain_response")
TOOL_SELECTION_PROMPT_TEMPLATE = load_prompt("tool_selection")

# Phase 3 prompts
PLANNER_PROMPT = load_prompt("planner")
SYNTHESIZER_PROMPT = load_prompt("synthesizer")
