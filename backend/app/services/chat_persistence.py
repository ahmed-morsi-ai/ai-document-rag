from uuid import UUID

from sqlalchemy import delete, func, select
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
        title: str | None = None,
        *,
        commit: bool = True,
    ) -> Conversation:
        """Create a conversation, optionally deferring transaction commit."""
        conversation = Conversation(
            owner_id=owner_id,
            title=title,
        )

        self.db.add(conversation)

        if commit:
            await self.db.commit()
            await self.db.refresh(conversation)
        else:
            await self.db.flush()

        return conversation

    async def get_conversations(
        self,
        owner_id: UUID,
    ) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.owner_id == owner_id,
            )
            .order_by(
                Conversation.created_at.desc(),
                Conversation.id.desc(),
            )
        )

        return list(result.scalars().all())

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

    async def delete_conversation(
        self,
        owner_id: UUID,
        conversation_id: UUID,
    ) -> None:
        conversation = await self.get_conversation(
            owner_id=owner_id,
            conversation_id=conversation_id,
        )

        await self.db.execute(
            delete(Message).where(
                Message.conversation_id == conversation.id,
            )
        )
        await self.db.delete(conversation)
        await self.db.commit()

    async def append_message(
        self,
        owner_id: UUID,
        conversation_id: UUID,
        role: str,
        content: str,
        sequence_number: int,
        *,
        commit: bool = True,
    ) -> Message:
        """Append a message, optionally deferring transaction commit."""
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

        if commit:
            await self.db.commit()
            await self.db.refresh(message)
        else:
            await self.db.flush()

        return message

    async def commit_transaction(self) -> None:
        await self.db.commit()

    async def rollback_transaction(self) -> None:
        await self.db.rollback()

    async def get_next_sequence_number(
        self,
        owner_id: UUID,
        conversation_id: UUID,
    ) -> int:
        await self.get_conversation(
            owner_id=owner_id,
            conversation_id=conversation_id,
        )

        result = await self.db.execute(
            select(
                func.coalesce(
                    func.max(Message.sequence_number),
                    0,
                )
            ).where(
                Message.conversation_id == conversation_id,
            )
        )

        return int(result.scalar_one()) + 1

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
