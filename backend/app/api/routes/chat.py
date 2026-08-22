from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.db.models import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService
from app.services.chat_factory import get_chat_service


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    response = await chat_service.chat(
        user_id=current_user.id,
        query=request.query,
        top_k=request.top_k,
        conversation_id=request.conversation_id,
    )

    return ChatResponse(
        query=response.query,
        answer=response.answer,
    )
