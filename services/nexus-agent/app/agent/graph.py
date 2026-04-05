"""LangGraph Definition for NEXUS Agent."""

from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import (
    gatekeeper_node,
    brain_node,
    response_node,
    tools_executor_node,
    planner_node,
    confirm_node,
    executor_node,
    synthesizer_node,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def after_gatekeeper(state: AgentState) -> str:
    """Determine next node after gatekeeper."""
    intent = state.get("intent")
    requires_planning = state.get("requires_planning", False)
    pending_plan = state.get("pending_plan")

    # Phase 3: If there's a pending plan, route based on confirmation intent
    if pending_plan:
        if intent == "plan_confirmation":
            logger.debug("routing_to_confirm", intent=intent)
            return "confirm"
        # If not a confirmation, treat as new request (clear plan by routing to brain)
        logger.debug("routing_to_brain_new_request", intent=intent)
        return "brain"

    # Phase 3: Route complex analysis to planner
    if requires_planning or intent == "complex_analysis":
        logger.debug("routing_to_planner", intent=intent)
        return "planner"

    # Phase 2: All other intents go to brain
    return "brain"


def after_brain(state: AgentState) -> str:
    """
    Determine next node after brain.

    Phase 2 routing:
    - If brain selected tools and they haven't been executed → tools
    - Otherwise → response
    """
    tool_calls = state.get("tool_calls", [])
    tools_executed = state.get("tools_executed", False)

    if tool_calls and not tools_executed:
        logger.debug("routing_to_tools", tool_count=len(tool_calls))
        return "tools"

    return "response"


def after_tools(state: AgentState) -> str:
    """After tools execute, return to brain for response generation."""
    return "brain"


def after_planner(state: AgentState) -> str:
    """After planner, go to confirm node."""
    pending_plan = state.get("pending_plan")
    if pending_plan:
        return "confirm"
    # No plan generated, go to response with error
    return "response"


def after_confirm(state: AgentState) -> str:
    """After confirm, check if plan was confirmed."""
    if state.get("plan_confirmed"):
        return "executor"
    if state.get("plan_cancelled"):
        return "response"
    # Still showing the plan, go to response (awaiting user input)
    return "response"


def after_executor(state: AgentState) -> str:
    """After executor, check if all steps complete."""
    execution_status = state.get("execution_status")

    if execution_status == "completed":
        return "synthesizer"
    if execution_status == "failed":
        return "response"
    # Still running, continue execution
    return "executor"


def after_synthesizer(state: AgentState) -> str:
    """After synthesizer, go to response."""
    return "response"


def create_nexus_graph() -> StateGraph:
    """
    Create the NEXUS agent graph.

    Phase 3 Graph:
    gatekeeper → [brain | planner]

    Brain path (Phase 2):
    brain → [tools → brain] → response → END

    Planner path (Phase 3):
    planner → confirm → response (awaiting) → [executor loop] → synthesizer → response → END
    """

    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("gatekeeper", gatekeeper_node)
    graph.add_node("brain", brain_node)
    graph.add_node("tools", tools_executor_node)
    graph.add_node("planner", planner_node)
    graph.add_node("confirm", confirm_node)
    graph.add_node("executor", executor_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("response", response_node)

    # Set entry point
    graph.set_entry_point("gatekeeper")

    # Gatekeeper → Brain OR Planner OR Confirm (for pending plan confirmation)
    graph.add_conditional_edges(
        "gatekeeper",
        after_gatekeeper,
        {
            "brain": "brain",
            "planner": "planner",
            "confirm": "confirm",
        }
    )

    # Brain → Tools OR Response
    graph.add_conditional_edges(
        "brain",
        after_brain,
        {
            "tools": "tools",
            "response": "response",
        }
    )

    # Tools → Brain
    graph.add_conditional_edges(
        "tools",
        after_tools,
        {
            "brain": "brain",
        }
    )

    # Planner → Confirm OR Response
    graph.add_conditional_edges(
        "planner",
        after_planner,
        {
            "confirm": "confirm",
            "response": "response",
        }
    )

    # Confirm → Executor OR Response
    graph.add_conditional_edges(
        "confirm",
        after_confirm,
        {
            "executor": "executor",
            "response": "response",
        }
    )

    # Executor → Executor (loop) OR Synthesizer OR Response
    graph.add_conditional_edges(
        "executor",
        after_executor,
        {
            "executor": "executor",
            "synthesizer": "synthesizer",
            "response": "response",
        }
    )

    # Synthesizer → Response
    graph.add_conditional_edges(
        "synthesizer",
        after_synthesizer,
        {
            "response": "response",
        }
    )

    # Response → END
    graph.add_edge("response", END)

    logger.info("nexus_graph_created", phase=3, nodes=8)

    return graph


# Compile the graph
nexus_graph = create_nexus_graph().compile()
