from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import get_current_user
from app.db.models import User
from app.schemas.conversation_history import (
    ConversationHistoryConversationResponse,
    ConversationHistoryMessageResponse,
    ConversationHistoryResponse,
    ConversationListResponse,
)
from app.services.chat_factory import (
    get_chat_persistence_service,
)
from app.services.chat_persistence import (
    ChatPersistenceService,
)


router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.get(
    "",
    response_model=ConversationListResponse,
)
async def list_conversations(
    search: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: User = Depends(get_current_user),
    persistence_service: ChatPersistenceService = Depends(
        get_chat_persistence_service,
    ),
) -> ConversationListResponse:
    conversations, total_count = (
        await persistence_service.get_conversations(
            owner_id=current_user.id,
            search=search,
            page=page,
            page_size=page_size,
        )
    )

    return ConversationListResponse(
        conversations=[
            ConversationHistoryConversationResponse.model_validate(
                conversation,
            )
            for conversation in conversations
        ],
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    persistence_service: ChatPersistenceService = Depends(
        get_chat_persistence_service,
    ),
):
    try:
        await persistence_service.delete_conversation(
            owner_id=current_user.id,
            conversation_id=conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc

@router.get(
    "/{conversation_id}/messages",
    response_model=ConversationHistoryResponse,
)
async def get_conversation_history(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    persistence_service: ChatPersistenceService = Depends(
        get_chat_persistence_service,
    ),
):
    try:
        conversation = (
            await persistence_service.get_conversation(
                owner_id=current_user.id,
                conversation_id=conversation_id,
            )
        )
        messages = (
            await persistence_service.get_messages(
                owner_id=current_user.id,
                conversation_id=conversation_id,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc

    return ConversationHistoryResponse(
        conversation=(
            ConversationHistoryConversationResponse.model_validate(
                conversation,
            )
        ),
        messages=[
            ConversationHistoryMessageResponse.model_validate(
                message,
            )
            for message in messages
        ],
    )
