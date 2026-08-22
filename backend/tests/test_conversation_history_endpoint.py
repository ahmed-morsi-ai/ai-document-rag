import os
import unittest
from datetime import datetime, timezone
from unittest import mock
from uuid import UUID

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_document_rag",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.main import app
from app.services.chat_factory import (
    get_chat_persistence_service,
)
from app.services.chat_persistence import ChatPersistenceService
from app.db.models import Conversation, Message


USER_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_USER_ID = UUID("33333333-3333-4333-8333-333333333333")
CONVERSATION_ID = UUID("22222222-2222-4222-8222-222222222222")


class FakePersistenceService:
    def __init__(self):
        self.conversations = []
        self.messages = []
        self.conversation_error = None

    async def get_conversations(self, owner_id):
        return [
            conversation
            for conversation in self.conversations
            if conversation.owner_id == owner_id
        ]

    async def get_conversation(
        self,
        owner_id,
        conversation_id,
    ):
        if self.conversation_error:
            raise self.conversation_error

        for conversation in self.conversations:
            if (
                conversation.id == conversation_id
                and conversation.owner_id == owner_id
            ):
                return conversation

        raise ValueError("conversation not found")

    async def get_messages(
        self,
        owner_id,
        conversation_id,
    ):
        await self.get_conversation(
            owner_id=owner_id,
            conversation_id=conversation_id,
        )

        messages = [
            message
            for message in self.messages
            if message.conversation_id == conversation_id
        ]

        return sorted(
            messages,
            key=lambda message: message.sequence_number,
        )


class ConversationHistoryEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        self.fake_user = mock.Mock(
            id=USER_ID,
            is_active=True,
        )

        self.other_user = mock.Mock(
            id=OTHER_USER_ID,
            is_active=True,
        )

        self.persistence = FakePersistenceService()

        async def override_current_user():
            return self.fake_user

        def override_persistence_service():
            return self.persistence

        app.dependency_overrides[get_current_user] = (
            override_current_user
        )
        app.dependency_overrides[
            get_chat_persistence_service
        ] = override_persistence_service

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_route_paths_are_registered(self):
        paths = app.openapi()["paths"]

        self.assertIn(
            "/conversations",
            paths,
        )
        self.assertIn(
            "get",
            paths["/conversations"],
        )
        self.assertIn(
            "/conversations/{conversation_id}/messages",
            paths,
        )
        self.assertIn(
            "get",
            paths[
                "/conversations/{conversation_id}/messages"
            ],
        )

    def test_unauthenticated_conversation_list_is_rejected(self):
        app.dependency_overrides.clear()

        response = self.client.get(
            "/conversations",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_empty_conversation_list_returns_empty_collection(self):
        response = self.client.get(
            "/conversations",
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json(),
            {
                "conversations": [],
            },
        )

    def test_conversation_list_returns_only_authenticated_users_conversations(
        self,
    ):
        owned = Conversation(
            id=CONVERSATION_ID,
            owner_id=USER_ID,
            created_at=datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            ),
            updated_at=datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            ),
        )

        other = Conversation(
            id=UUID(
                "44444444-4444-4444-8444-444444444444"
            ),
            owner_id=OTHER_USER_ID,
            created_at=datetime(
                2026,
                1,
                3,
                tzinfo=timezone.utc,
            ),
            updated_at=datetime(
                2026,
                1,
                3,
                tzinfo=timezone.utc,
            ),
        )

        self.persistence.conversations = [
            other,
            owned,
        ]

        response = self.client.get(
            "/conversations",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            len(body["conversations"]),
            1,
        )
        self.assertEqual(
            body["conversations"][0]["id"],
            str(CONVERSATION_ID),
        )
        self.assertNotIn(
            "owner_id",
            body["conversations"][0],
        )

    def test_conversation_history_returns_ordered_messages(self):
        conversation = Conversation(
            id=CONVERSATION_ID,
            owner_id=USER_ID,
            created_at=datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            ),
            updated_at=datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            ),
        )

        first = Message(
            id=UUID(
                "55555555-5555-4555-8555-555555555555"
            ),
            conversation_id=CONVERSATION_ID,
            role="user",
            content="hello",
            sequence_number=1,
            created_at=datetime(
                2026,
                1,
                2,
                1,
                tzinfo=timezone.utc,
            ),
        )

        second = Message(
            id=UUID(
                "66666666-6666-4666-8666-666666666666"
            ),
            conversation_id=CONVERSATION_ID,
            role="assistant",
            content="hello back",
            sequence_number=2,
            created_at=datetime(
                2026,
                1,
                2,
                2,
                tzinfo=timezone.utc,
            ),
        )

        self.persistence.conversations = [
            conversation,
        ]
        self.persistence.messages = [
            second,
            first,
        ]

        response = self.client.get(
            f"/conversations/{CONVERSATION_ID}/messages",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            body["conversation"]["id"],
            str(CONVERSATION_ID),
        )
        self.assertEqual(
            [message["sequence_number"] for message in body["messages"]],
            [1, 2],
        )

    def test_empty_conversation_history_returns_empty_collection(self):
        conversation = Conversation(
            id=CONVERSATION_ID,
            owner_id=USER_ID,
            created_at=datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            ),
            updated_at=datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            ),
        )

        self.persistence.conversations = [
            conversation,
        ]

        response = self.client.get(
            f"/conversations/{CONVERSATION_ID}/messages",
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json()["messages"],
            [],
        )

    def test_unknown_conversation_returns_404(self):
        response = self.client.get(
            f"/conversations/{CONVERSATION_ID}/messages",
        )

        self.assertEqual(
            response.status_code,
            404,
        )
        self.assertEqual(
            response.json(),
            {
                "detail": "Conversation not found",
            },
        )

    def test_other_users_conversation_returns_404(self):
        other_conversation = Conversation(
            id=CONVERSATION_ID,
            owner_id=OTHER_USER_ID,
            created_at=datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            ),
            updated_at=datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            ),
        )

        self.persistence.conversations = [
            other_conversation,
        ]

        response = self.client.get(
            f"/conversations/{CONVERSATION_ID}/messages",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_response_does_not_expose_internal_fields(self):
        conversation = Conversation(
            id=CONVERSATION_ID,
            owner_id=USER_ID,
            created_at=datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            ),
            updated_at=datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            ),
        )

        message = Message(
            id=UUID(
                "55555555-5555-4555-8555-555555555555"
            ),
            conversation_id=CONVERSATION_ID,
            role="user",
            content="hello",
            sequence_number=1,
            created_at=datetime(
                2026,
                1,
                2,
                1,
                tzinfo=timezone.utc,
            ),
        )

        self.persistence.conversations = [
            conversation,
        ]
        self.persistence.messages = [
            message,
        ]

        response = self.client.get(
            f"/conversations/{CONVERSATION_ID}/messages",
        )

        body = response.json()

        self.assertEqual(
            set(body["conversation"]),
            {
                "id",
                "created_at",
                "updated_at",
            },
        )

        self.assertEqual(
            set(body["messages"][0]),
            {
                "id",
                "role",
                "content",
                "sequence_number",
                "created_at",
            },
        )


if __name__ == "__main__":
    unittest.main()
