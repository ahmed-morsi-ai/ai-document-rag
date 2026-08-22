import unittest
from unittest.mock import AsyncMock, Mock

from app.db.models import Conversation, Message
from app.services.chat_persistence import ChatPersistenceService


class AsyncScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class AsyncScalarsResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values


class ChatPersistenceServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = Mock()

        self.db.commit = AsyncMock()
        self.db.refresh = AsyncMock()

        self.service = ChatPersistenceService(
            self.db,
        )

    async def test_create_conversation_persists_for_owner(self):
        owner_id = "11111111-1111-4111-8111-111111111111"

        conversation = await self.service.create_conversation(
            owner_id=__import__("uuid").UUID(owner_id),
        )

        self.db.add.assert_called_once()

        persisted = self.db.add.call_args.args[0]

        self.assertIsInstance(
            persisted,
            Conversation,
        )
        self.assertEqual(
            persisted.owner_id,
            __import__("uuid").UUID(owner_id),
        )
        self.assertIs(
            conversation,
            persisted,
        )

        self.db.commit.assert_awaited_once_with()
        self.db.refresh.assert_awaited_once_with(
            persisted,
        )

    async def test_get_conversation_returns_owned_conversation(self):
        from uuid import UUID

        owner_id = UUID(
            "11111111-1111-4111-8111-111111111111"
        )
        conversation_id = UUID(
            "22222222-2222-4222-8222-222222222222"
        )

        conversation = Conversation(
            id=conversation_id,
            owner_id=owner_id,
        )

        self.db.execute = AsyncMock(
            return_value=AsyncScalarResult(
                conversation,
            )
        )

        result = await self.service.get_conversation(
            owner_id=owner_id,
            conversation_id=conversation_id,
        )

        self.assertIs(
            result,
            conversation,
        )
        self.db.execute.assert_awaited_once()

    async def test_get_conversation_missing_is_explicit(self):
        from uuid import UUID

        self.db.execute = AsyncMock(
            return_value=AsyncScalarResult(None),
        )

        with self.assertRaisesRegex(
            ValueError,
            "conversation not found",
        ):
            await self.service.get_conversation(
                owner_id=UUID(
                    "11111111-1111-4111-8111-111111111111"
                ),
                conversation_id=UUID(
                    "22222222-2222-4222-8222-222222222222"
                ),
            )

    async def test_wrong_owner_cannot_retrieve_conversation(self):
        from uuid import UUID

        self.db.execute = AsyncMock(
            return_value=AsyncScalarResult(None),
        )

        with self.assertRaisesRegex(
            ValueError,
            "conversation not found",
        ):
            await self.service.get_conversation(
                owner_id=UUID(
                    "33333333-3333-4333-8333-333333333333"
                ),
                conversation_id=UUID(
                    "22222222-2222-4222-8222-222222222222"
                ),
            )

    async def test_append_user_message(self):
        from uuid import UUID

        owner_id = UUID(
            "11111111-1111-4111-8111-111111111111"
        )
        conversation_id = UUID(
            "22222222-2222-4222-8222-222222222222"
        )

        conversation = Conversation(
            id=conversation_id,
            owner_id=owner_id,
        )

        self.db.execute = AsyncMock(
            return_value=AsyncScalarResult(
                conversation,
            )
        )

        message = await self.service.append_message(
            owner_id=owner_id,
            conversation_id=conversation_id,
            role="user",
            content="hello",
            sequence_number=1,
        )

        persisted = self.db.add.call_args.args[0]

        self.assertIsInstance(
            persisted,
            Message,
        )
        self.assertIs(
            message,
            persisted,
        )
        self.assertEqual(
            persisted.conversation_id,
            conversation_id,
        )
        self.assertEqual(
            persisted.role,
            "user",
        )
        self.assertEqual(
            persisted.content,
            "hello",
        )
        self.assertEqual(
            persisted.sequence_number,
            1,
        )

        self.db.commit.assert_awaited_once_with()
        self.db.refresh.assert_awaited_once_with(
            persisted,
        )

    async def test_append_message_rejects_missing_or_foreign_conversation(
        self,
    ):
        from uuid import UUID

        self.db.execute = AsyncMock(
            return_value=AsyncScalarResult(None),
        )

        with self.assertRaisesRegex(
            ValueError,
            "conversation not found",
        ):
            await self.service.append_message(
                owner_id=UUID(
                    "33333333-3333-4333-8333-333333333333"
                ),
                conversation_id=UUID(
                    "22222222-2222-4222-8222-222222222222"
                ),
                role="assistant",
                content="answer",
                sequence_number=2,
            )

        self.db.add.assert_not_called()
        self.db.commit.assert_not_awaited()

    async def test_get_messages_returns_deterministic_sequence_order(self):
        from uuid import UUID

        owner_id = UUID(
            "11111111-1111-4111-8111-111111111111"
        )
        conversation_id = UUID(
            "22222222-2222-4222-8222-222222222222"
        )

        conversation = Conversation(
            id=conversation_id,
            owner_id=owner_id,
        )

        messages = [
            Message(
                conversation_id=conversation_id,
                role="user",
                content="first",
                sequence_number=1,
            ),
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content="second",
                sequence_number=2,
            ),
        ]

        self.db.execute = AsyncMock(
            side_effect=[
                AsyncScalarResult(conversation),
                AsyncScalarsResult(messages),
            ],
        )

        result = await self.service.get_messages(
            owner_id=owner_id,
            conversation_id=conversation_id,
        )

        self.assertEqual(
            result,
            messages,
        )
        self.assertEqual(
            [message.sequence_number for message in result],
            [1, 2],
        )

        self.assertEqual(
            self.db.execute.await_count,
            2,
        )

    async def test_empty_history_returns_empty_list(self):
        from uuid import UUID

        conversation_id = UUID(
            "22222222-2222-4222-8222-222222222222"
        )

        conversation = Conversation(
            id=conversation_id,
            owner_id=UUID(
                "11111111-1111-4111-8111-111111111111"
            ),
        )

        self.db.execute = AsyncMock(
            side_effect=[
                AsyncScalarResult(conversation),
                AsyncScalarsResult([]),
            ],
        )

        result = await self.service.get_messages(
            owner_id=conversation.owner_id,
            conversation_id=conversation_id,
        )

        self.assertEqual(
            result,
            [],
        )

    async def test_database_failures_propagate(self):
        self.db.commit = AsyncMock(
            side_effect=RuntimeError("database failure"),
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "database failure",
        ):
            await self.service.create_conversation(
                owner_id=__import__("uuid").UUID(
                    "11111111-1111-4111-8111-111111111111"
                ),
            )

    async def test_service_can_be_instantiated_with_async_session(self):
        from sqlalchemy.ext.asyncio import AsyncSession

        session = Mock(spec=AsyncSession)

        service = ChatPersistenceService(
            db=session,
        )

        self.assertIs(
            service.db,
            session,
        )


if __name__ == "__main__":
    unittest.main()
