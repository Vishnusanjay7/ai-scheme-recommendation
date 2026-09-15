"""
AI Government Scheme Chatbot API Endpoints
------------------------------------------
Provides natural-language conversational scheme discovery:
  - POST /api/chat
  - GET  /api/chat/history

SECURITY & ARCHITECTURAL INVARIANTS:
1. Authenticated citizen identity is resolved strictly via auth.uid().
2. Authenticated users' stored profile is authoritative.
3. Natural-language extraction merges temporary query context; it never permanently mutates user_profiles.
4. Deterministic eligibility engine (Phase 3), deadline activity filter (Phase 4),
   and recommendation ranking (Phase 5) are reused. The LLM does NOT decide eligibility.
5. All scheme data returned is grounded in the backend database; no hallucinated schemes or URLs.
6. Chat history is accessible only by its authenticated owner. Cross-user access is blocked.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryResponse,
)
from app.services.chat_service import ChatService
from app.utils.auth import get_authenticated_user_id

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])
chat_service = ChatService()


@router.post(
    "",
    response_model=ChatMessageResponse,
    summary="Chat with Government Scheme Assistant",
    description=(
        "Accepts natural-language queries in English or Tamil, extracts structured intent/entities, "
        "evaluates deterministic eligibility and registration deadlines, and returns verified "
        "scheme recommendations with an AI-synthesized explanation."
    ),
)
def send_chat_message(
    request: ChatMessageRequest,
    auth_user_id: Optional[str] = Depends(get_authenticated_user_id),
):
    try:
        return chat_service.process_chat_message(
            message=request.message,
            auth_user_id=auth_user_id,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(exc)}",
        )


@router.get(
    "/history",
    response_model=ChatHistoryResponse,
    summary="Get Citizen Chat History",
    description="Fetches recent conversation history for the authenticated citizen.",
)
def get_chat_history(
    limit: int = Query(default=50, ge=1, le=100),
    auth_user_id: Optional[str] = Depends(get_authenticated_user_id),
):
    if not auth_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view chat history.",
        )
    try:
        return chat_service.get_chat_history(
            user_id=auth_user_id,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chat history: {str(exc)}",
        )
