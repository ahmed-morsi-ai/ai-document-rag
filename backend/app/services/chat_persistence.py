from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, Message


class ChatPersistenceService:
    """Persist and retrieve conversations and messages."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def create_conversation(
        self,
        owner_id: UUID,
    ) -> Conversation:
        conversation = Conversation(
            owner_id=owner_id,
        )

        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def get_conversation(
        self,
        owner_id: UUID,
        conversation_id: UUID,
    ) -> Conversation:
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.owner_id == owner_id,
            )
        )

        conversation = result.scalar_one_or_none()

        if conversation is None:
            raise ValueError("conversation not found")

        return conversation

    async def append_message(
        self,
        owner_id: UUID,
        conversation_id: UUID,
        role: str,
        content: str,
        sequence_number: int,
    ) -> Message:
        await self.get_conversation(
            owner_id=owner_id,
            conversation_id=conversation_id,
        )

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sequence_number=sequence_number,
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def get_messages(
        self,
        owner_id: UUID,
        conversation_id: UUID,
    ) -> list[Message]:
        await self.get_conversation(
            owner_id=owner_id,
            conversation_id=conversation_id,
        )

        result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
            )
            .order_by(
                Message.sequence_number,
            )
        )

        return list(result.scalars().all())
