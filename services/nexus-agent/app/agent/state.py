"""LangGraph State Definition for NEXUS Agent."""

from typing import TypedDict, Annotated, Sequence, Literal, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from operator import add


class ToolCall(TypedDict):
    """Represents a tool call request from the brain."""

    tool_name: str
    arguments: Dict[str, Any]
    reason: str  # Why this tool was selected


class ToolResultState(TypedDict):
    """Represents the result of a tool execution."""

    tool_name: str
    success: bool
    data: Any
    error: Optional[str]
    execution_time_ms: int


# === Phase 3: Planning Types ===

class PlanStep(TypedDict):
    """Represents a single step in an execution plan."""

    step_number: int
    description: str
    tool_name: str
    tool_args: Dict[str, Any]
    depends_on: List[int]
    purpose: str


class ExecutionPlan(TypedDict):
    """Represents a complete execution plan."""

    goal: str
    steps: List[PlanStep]
    estimated_tools: int
    complexity: Literal["simple", "medium", "complex"]


class StepResult(TypedDict):
    """Represents the result of executing a plan step."""

    step_number: int
    tool_name: str
    success: bool
    data: Any
    error: Optional[str]
    execution_time_ms: int


class AgentState(TypedDict):
    """State that flows through the NEXUS agent graph."""

    # === Conversation ===
    messages: Annotated[Sequence[BaseMessage], add]
    user_id: str
    session_id: str

    # === Classification (Gatekeeper) ===
    intent: Literal[
        "simple_query",      # Can answer directly
        "complex_task",      # Needs Brain + tools (single execution)
        "complex_analysis",  # Needs Planner + multi-step (Phase 3)
        "chitchat",          # Casual conversation
        "plan_confirmation", # Confirming a pending plan
    ]
    complexity_score: float  # 0.0 - 1.0
    requires_tools: bool
    requires_planning: bool  # Phase 3: needs multi-step planning

    # === Tool Execution (Phase 2) ===
    available_tools: List[str]  # Names of registered tools
    tool_calls: List[ToolCall]  # Tools the brain wants to execute
    tool_results: List[ToolResultState]  # Results from executed tools
    tools_executed: bool  # Whether tools have been run this iteration

    # === Execution State ===
    current_node: str
    iteration: int
    max_iterations: int

    # === Output ===
    final_response: str | None
    confidence: float

    # === Metadata ===
    tokens_used: int
    latency_ms: int
    error: str | None

    # === Phase 3: Planning ===
    pending_plan: Optional[ExecutionPlan]
    plan_confirmed: bool
    plan_cancelled: bool
    plan_modifications: List[str]
    awaiting_confirmation: bool  # Signal to API

    # === Phase 3: Execution ===
    current_step: int
    step_results: List[StepResult]
    execution_status: Literal["idle", "running", "paused", "completed", "failed"]

    # === Phase 3: Synthesis ===
    synthesized_result: Optional[Dict[str, Any]]

    # === Phase 4: Memory ===
    memory_context: Optional[Dict[str, Any]]  # Recalled memories
