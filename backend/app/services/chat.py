from dataclasses import dataclass
from uuid import UUID

from app.services.chat_persistence import ChatPersistenceService
from app.services.rag import RagService


@dataclass(frozen=True)
class ChatResponse:
    query: str
    answer: str


class ChatService:
    """Application-level orchestration over RAG and chat persistence."""

    def __init__(
        self,
        rag_service: RagService,
        persistence_service: ChatPersistenceService,
    ) -> None:
        self.rag_service = rag_service
        self.persistence_service = persistence_service

    async def chat(
        self,
        user_id: UUID,
        query: str,
        top_k: int = 5,
        conversation_id: UUID | None = None,
    ) -> ChatResponse:
        if conversation_id is None:
            conversation = (
                await self.persistence_service.create_conversation(
                    owner_id=user_id,
                )
            )
        else:
            conversation = (
                await self.persistence_service.get_conversation(
                    owner_id=user_id,
                    conversation_id=conversation_id,
                )
            )

        user_sequence_number = (
            await self.persistence_service.get_next_sequence_number(
                owner_id=user_id,
                conversation_id=conversation.id,
            )
        )

        await self.persistence_service.append_message(
            owner_id=user_id,
            conversation_id=conversation.id,
            role="user",
            content=query,
            sequence_number=user_sequence_number,
        )

        rag_response = await _maybe_await(
            self.rag_service.generate_answer(
                query=query,
                top_k=top_k,
            )
        )

        assistant_sequence_number = (
            await self.persistence_service.get_next_sequence_number(
                owner_id=user_id,
                conversation_id=conversation.id,
            )
        )

        await self.persistence_service.append_message(
            owner_id=user_id,
            conversation_id=conversation.id,
            role="assistant",
            content=rag_response.answer,
            sequence_number=assistant_sequence_number,
        )

        return ChatResponse(
            query=query,
            answer=rag_response.answer,
        )


async def _maybe_await(value):
    """Support the existing synchronous RAG contract during migration."""
    if hasattr(value, "__await__"):
        return await value

    return value
