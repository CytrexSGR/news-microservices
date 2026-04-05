"""Main NEXUS Agent Class."""

import time
from langchain_core.messages import HumanMessage
from app.agent.graph import nexus_graph
from app.agent.state import AgentState
from app.memory import get_memory_manager, get_session_memory
from app.core.logging import get_logger

logger = get_logger(__name__)


class NexusAgent:
    """
    NEXUS AI Co-Pilot for News Microservices Platform.

    Phase 4: With persistent memory and plan storage.
    """

    def __init__(self):
        self.graph = nexus_graph
        self.memory = get_memory_manager()
        self.session_memory = get_session_memory()  # Legacy fallback
        logger.info("nexus_agent_initialized", phase=4)

    async def chat(
        self,
        message: str,
        session_id: str = "default",
        user_id: str = "anonymous",
    ) -> dict:
        """
        Process a chat message and return a response.

        Phase 4: Integrates persistent memory.
        """
        start_time = time.time()

        # Initialize session in memory manager
        conversation_id = await self.memory.start_session(session_id, user_id)

        # Save user message to long-term memory
        await self.memory.save_message(
            session_id=session_id,
            role="user",
            content=message,
        )

        # Recall relevant memories for context
        memories = await self.memory.recall_relevant_memories(
            user_id=user_id,
            query=message,
            limit=3,
        )

        # Check for pending plan (persistent)
        pending_plan_db = await self.memory.get_pending_plan(session_id, user_id)

        # Fallback to in-memory session for backwards compatibility
        session_data = self.session_memory.get_session(session_id)
        pending_plan = pending_plan_db or session_data.get("pending_plan")

        # Create initial state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "session_id": session_id,
            "intent": "simple_query",
            "complexity_score": 0.0,
            "requires_tools": False,
            "current_node": "start",
            "iteration": 0,
            "max_iterations": 5,
            "final_response": None,
            "confidence": 0.0,
            "tokens_used": 0,
            "latency_ms": 0,
            "error": None,
            # Phase 3/4: Planning
            "pending_plan": pending_plan,
            "plan_confirmed": False,
            "plan_cancelled": False,
            "awaiting_confirmation": session_data.get("awaiting_confirmation", False),
            "current_step": session_data.get("current_step", 0),
            "step_results": session_data.get("step_results", []),
            # Phase 4: Memory context
            "memory_context": memories if memories.get("messages") or memories.get("facts") else None,
        }

        try:
            # Run the graph
            result = await self.graph.ainvoke(initial_state)

            latency_ms = int((time.time() - start_time) * 1000)

            # Save assistant response to long-term memory
            final_response = result.get("final_response", "")
            if final_response:
                await self.memory.save_message(
                    session_id=session_id,
                    role="assistant",
                    content=final_response,
                    intent=result.get("intent"),
                    tokens_used=result.get("tokens_used", 0),
                )

            # Handle plan persistence
            if result.get("awaiting_confirmation") and result.get("pending_plan"):
                # Save plan to persistent storage
                plan = result.get("pending_plan")
                await self.memory.save_plan(session_id, user_id, plan)

                # Also keep in session for quick access
                self.session_memory.update_session(session_id, {
                    "pending_plan": plan,
                    "awaiting_confirmation": True,
                    "current_step": 0,
                    "step_results": [],
                })
            elif result.get("execution_status") == "running":
                self.session_memory.update_session(session_id, {
                    "pending_plan": result.get("pending_plan"),
                    "awaiting_confirmation": False,
                    "current_step": result.get("current_step", 0),
                    "step_results": result.get("step_results", []),
                })
            else:
                # Clear session when plan is completed or cancelled
                self.session_memory.clear(session_id)

            logger.info(
                "nexus_chat_completed",
                session_id=session_id,
                user_id=user_id,
                intent=result.get("intent"),
                tokens=result.get("tokens_used", 0),
                latency_ms=latency_ms,
                memory_used=bool(memories.get("messages") or memories.get("facts")),
            )

            return {
                "response": result.get("final_response", "Keine Antwort generiert."),
                "intent": result.get("intent", "unknown"),
                "tokens_used": result.get("tokens_used", 0),
                "latency_ms": latency_ms,
                "confidence": result.get("confidence", 0.0),
                "error": result.get("error"),
                # Phase 3 additions
                "awaiting_confirmation": result.get("awaiting_confirmation", False),
                "pending_plan": result.get("pending_plan"),
                "execution_progress": {
                    "current_step": result.get("current_step", 0),
                    "total_steps": len(result.get("pending_plan", {}).get("steps", [])) if result.get("pending_plan") else 0,
                    "status": result.get("execution_status"),
                } if result.get("execution_status") else None,
                "synthesized_result": result.get("synthesized_result"),
                # Phase 4 additions
                "memory_used": bool(memories.get("messages") or memories.get("facts")),
            }

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error("nexus_chat_error", error=str(e))

            return {
                "response": "Entschuldigung, ein Fehler ist aufgetreten. Bitte versuche es erneut.",
                "intent": "error",
                "tokens_used": 0,
                "latency_ms": latency_ms,
                "confidence": 0.0,
                "error": str(e),
            }


# Singleton instance
_agent: NexusAgent | None = None


def get_nexus_agent() -> NexusAgent:
    """Get or create NEXUS agent singleton."""
    global _agent
    if _agent is None:
        _agent = NexusAgent()
    return _agent
