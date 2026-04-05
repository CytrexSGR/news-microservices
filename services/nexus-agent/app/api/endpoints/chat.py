"""Chat Endpoint."""

from fastapi import APIRouter, Request, HTTPException
from app.models.chat import ChatRequest, ChatResponse, PlanConfirmation
from app.agent.nexus import get_nexus_agent
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: Request, chat_request: ChatRequest) -> ChatResponse:
    """
    Process a chat message and return AI response.

    Args:
        request: FastAPI request object
        chat_request: Chat request with message and optional session_id

    Returns:
        ChatResponse with AI response and metadata
    """
    # Extract user_id from auth header if available (Phase 2)
    user_id = request.headers.get("X-User-ID", "anonymous")

    logger.info(
        "chat_request_received",
        session_id=chat_request.session_id,
        user_id=user_id,
        message_length=len(chat_request.message),
    )

    try:
        agent = get_nexus_agent()
        result = await agent.chat(
            message=chat_request.message,
            session_id=chat_request.session_id or "default",
            user_id=user_id,
        )

        return ChatResponse(
            response=result["response"],
            intent=result.get("intent", "unknown"),
            tokens_used=result.get("tokens_used", 0),
            latency_ms=result.get("latency_ms", 0),
            confidence=result.get("confidence", 0.0),
            error=result.get("error"),
            # Phase 3 additions
            awaiting_confirmation=result.get("awaiting_confirmation", False),
            pending_plan=result.get("pending_plan"),
            execution_progress=result.get("execution_progress"),
            structured_data=result.get("synthesized_result"),
        )

    except Exception as e:
        logger.error("chat_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/confirm", response_model=ChatResponse, tags=["Chat"])
async def confirm_plan(
    request: Request,
    confirmation: PlanConfirmation
) -> ChatResponse:
    """
    Confirm, modify, or cancel a pending execution plan.

    Args:
        request: FastAPI request object
        confirmation: Plan confirmation with action

    Returns:
        ChatResponse with execution result or cancellation message
    """
    user_id = request.headers.get("X-User-ID", "anonymous")

    logger.info(
        "plan_confirmation_received",
        session_id=confirmation.session_id,
        user_id=user_id,
        action=confirmation.action,
    )

    try:
        agent = get_nexus_agent()

        # Handle confirmation as a special message
        if confirmation.action == "confirm":
            message = "ja, Plan ausführen"
        elif confirmation.action == "cancel":
            message = "abbrechen"
        elif confirmation.action == "modify":
            mods = ", ".join(confirmation.modifications or [])
            message = f"anpassen: {mods}"
        else:
            message = confirmation.action

        result = await agent.chat(
            message=message,
            session_id=confirmation.session_id,
            user_id=user_id,
        )

        return ChatResponse(
            response=result["response"],
            intent=result.get("intent", "unknown"),
            tokens_used=result.get("tokens_used", 0),
            latency_ms=result.get("latency_ms", 0),
            confidence=result.get("confidence", 0.0),
            error=result.get("error"),
            awaiting_confirmation=result.get("awaiting_confirmation", False),
            pending_plan=result.get("pending_plan"),
            execution_progress=result.get("execution_progress"),
            structured_data=result.get("synthesized_result"),
        )

    except Exception as e:
        logger.error("confirm_endpoint_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
