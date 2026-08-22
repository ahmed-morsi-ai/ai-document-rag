import unittest
from uuid import UUID

from app.services.chat import ChatResponse, ChatService


USER_ID = UUID("11111111-1111-4111-8111-111111111111")
CONVERSATION_ID = UUID("22222222-2222-4222-8222-222222222222")


class FakeRagService:
    def __init__(self, answer="generated answer"):
        self.answer = answer
        self.calls = []

    def generate_answer(self, query, top_k=5):
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
            }
        )

        class FakeRagResponse:
            def __init__(self, answer):
                self.answer = answer

        return FakeRagResponse(self.answer)


class FakePersistenceService:
    def __init__(
        self,
        conversation=None,
        next_sequences=None,
    ):
        self.conversation = conversation
        self.next_sequences = list(
            next_sequences or []
        )
        self.next_sequence_number = 1
        self.calls = []
        self.events = []
        self.create_error = None
        self.get_error = None
        self.user_message_error = None
        self.assistant_message_error = None

    async def create_conversation(self, owner_id):
        if self.create_error:
            raise self.create_error

        self.events.append("create_conversation")
        self.calls.append(
            {
                "operation": "create_conversation",
                "owner_id": owner_id,
            }
        )

        class Conversation:
            id = CONVERSATION_ID

        self.conversation = Conversation()
        return self.conversation

    async def get_conversation(
        self,
        owner_id,
        conversation_id,
    ):
        if self.get_error:
            raise self.get_error

        self.events.append("get_conversation")
        self.calls.append(
            {
                "operation": "get_conversation",
                "owner_id": owner_id,
                "conversation_id": conversation_id,
            }
        )

        class Conversation:
            id = conversation_id

        return Conversation()

    async def get_next_sequence_number(
        self,
        owner_id,
        conversation_id,
    ):
        if self.next_sequences:
            value = self.next_sequences.pop(0)
        else:
            value = self.next_sequence_number
            self.next_sequence_number += 1

        self.events.append(
            f"get_next_sequence_number:{value}"
        )
        return value

    async def append_message(
        self,
        owner_id,
        conversation_id,
        role,
        content,
        sequence_number,
    ):
        if role == "user" and self.user_message_error:
            raise self.user_message_error

        if (
            role == "assistant"
            and self.assistant_message_error
        ):
            raise self.assistant_message_error

        self.events.append(
            f"append_message:{role}"
        )
        self.calls.append(
            {
                "operation": "append_message",
                "owner_id": owner_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "sequence_number": sequence_number,
            }
        )


class ChatServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.rag_service = FakeRagService(
            answer="the answer",
        )
        self.persistence = FakePersistenceService()

        self.chat_service = ChatService(
            rag_service=self.rag_service,
            persistence_service=self.persistence,
        )

    async def test_new_conversation_is_created(self):
        result = await self.chat_service.chat(
            user_id=USER_ID,
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            result,
            ChatResponse(
                query="hello",
                answer="the answer",
            ),
        )

        self.assertIn(
            "create_conversation",
            self.persistence.events,
        )

    async def test_existing_conversation_is_reused(self):
        result = await self.chat_service.chat(
            user_id=USER_ID,
            query="hello",
            top_k=2,
            conversation_id=CONVERSATION_ID,
        )

        self.assertEqual(
            result.answer,
            "the answer",
        )

        self.assertEqual(
            self.persistence.calls[0],
            {
                "operation": "get_conversation",
                "owner_id": USER_ID,
                "conversation_id": CONVERSATION_ID,
            },
        )

    async def test_user_message_is_persisted_before_rag(self):
        await self.chat_service.chat(
            user_id=USER_ID,
            query="hello",
        )

        self.assertEqual(
            self.persistence.events,
            [
                "create_conversation",
                "get_next_sequence_number:1",
                "append_message:user",
                "get_next_sequence_number:2",
                "append_message:assistant",
            ],
        )

        self.assertEqual(
            self.rag_service.calls,
            [
                {
                    "query": "hello",
                    "top_k": 5,
                }
            ],
        )

    async def test_exact_query_is_persisted_as_user_message(self):
        query = "  preserve whitespace  "

        await self.chat_service.chat(
            user_id=USER_ID,
            query=query,
        )

        user_message = next(
            call
            for call in self.persistence.calls
            if call["operation"] == "append_message"
            and call["role"] == "user"
        )

        self.assertEqual(
            user_message["content"],
            query,
        )
        self.assertEqual(
            user_message["sequence_number"],
            1,
        )

    async def test_assistant_answer_is_persisted_after_rag(self):
        await self.chat_service.chat(
            user_id=USER_ID,
            query="hello",
        )

        assistant_message = next(
            call
            for call in self.persistence.calls
            if call["operation"] == "append_message"
            and call["role"] == "assistant"
        )

        self.assertEqual(
            assistant_message["content"],
            "the answer",
        )
        self.assertEqual(
            assistant_message["sequence_number"],
            2,
        )

    async def test_rag_is_called_exactly_once(self):
        await self.chat_service.chat(
            user_id=USER_ID,
            query="hello",
        )

        self.assertEqual(
            self.rag_service.calls,
            [
                {
                    "query": "hello",
                    "top_k": 5,
                }
            ],
        )

    async def test_user_message_failure_prevents_rag(self):
        self.persistence.user_message_error = RuntimeError(
            "user message persistence failure"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "user message persistence failure",
        ):
            await self.chat_service.chat(
                user_id=USER_ID,
                query="hello",
            )

        self.assertEqual(
            self.rag_service.calls,
            [],
        )

    async def test_rag_failure_does_not_persist_assistant(self):
        self.rag_service.generate_answer = (
            self._failing_rag
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "rag failure",
        ):
            await self.chat_service.chat(
                user_id=USER_ID,
                query="hello",
            )

        roles = [
            call["role"]
            for call in self.persistence.calls
            if call["operation"] == "append_message"
        ]

        self.assertEqual(
            roles,
            ["user"],
        )

    async def test_assistant_persistence_failure_is_propagated(self):
        self.persistence.assistant_message_error = (
            RuntimeError("assistant persistence failure")
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "assistant persistence failure",
        ):
            await self.chat_service.chat(
                user_id=USER_ID,
                query="hello",
            )

        self.assertEqual(
            len(self.rag_service.calls),
            1,
        )

    async def test_ownership_failure_propagates_before_user_message(self):
        self.persistence.get_error = ValueError(
            "conversation not found"
        )

        with self.assertRaisesRegex(
            ValueError,
            "conversation not found",
        ):
            await self.chat_service.chat(
                user_id=USER_ID,
                query="hello",
                conversation_id=CONVERSATION_ID,
            )

        self.assertEqual(
            self.rag_service.calls,
            [],
        )

    async def test_repeated_deterministic_calls_preserve_behavior(self):
        first = await self.chat_service.chat(
            user_id=USER_ID,
            query="hello",
        )
        second = await self.chat_service.chat(
            user_id=USER_ID,
            query="hello",
        )

        self.assertEqual(
            first,
            second,
        )

    async def test_chat_service_has_no_database_session_attribute(self):
        self.assertFalse(
            hasattr(self.chat_service, "db")
        )

    async def _failing_rag(self, query, top_k=5):
        raise RuntimeError("rag failure")


if __name__ == "__main__":
    unittest.main()
