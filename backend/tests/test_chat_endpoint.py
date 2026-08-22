import os
import unittest
from unittest import mock
from unittest.mock import AsyncMock

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_document_rag",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.api.routes.chat import router as chat_router
from app.main import app
from app.services.chat import ChatResponse
from app.services.chat_factory import get_chat_service


class ChatEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        self.fake_user = mock.Mock(
            id="user-1",
            is_active=True,
        )

        self.fake_chat_service = mock.Mock()
        self.fake_chat_service.chat = AsyncMock(
            return_value=ChatResponse(
                query="hello",
                answer="hello answer",
            )
        )

        async def override_current_user():
            return self.fake_user

        def override_chat_service():
            return self.fake_chat_service

        app.dependency_overrides[get_current_user] = (
            override_current_user
        )
        app.dependency_overrides[get_chat_service] = (
            override_chat_service
        )

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_route_is_registered(self):
        paths = app.openapi()["paths"]

        self.assertIn(
            "/chat",
            paths,
        )
        self.assertIn(
            "post",
            paths["/chat"],
        )

    def test_unauthenticated_request_is_rejected(self):
        app.dependency_overrides.clear()

        response = self.client.post(
            "/chat",
            json={
                "query": "hello",
            },
        )

        self.assertEqual(
            response.status_code,
            401,
        )

        self.fake_chat_service.chat.assert_not_called()

    def test_authenticated_valid_request_succeeds(self):
        response = self.client.post(
            "/chat",
            json={
                "query": "hello",
                "top_k": 2,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json(),
            {
                "query": "hello",
                "answer": "hello answer",
            },
        )

    def test_query_and_top_k_reach_chat_service_unchanged(self):
        response = self.client.post(
            "/chat",
            json={
                "query": "  preserve whitespace  ",
                "top_k": 7,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.fake_chat_service.chat.assert_called_once_with(
            user_id=self.fake_user.id,
            query="  preserve whitespace  ",
            top_k=7,
            conversation_id=None,
        )

    def test_conversation_id_is_forwarded_to_chat_service(self):
        conversation_id = (
            "22222222-2222-4222-8222-222222222222"
        )

        response = self.client.post(
            "/chat",
            json={
                "query": "continue",
                "conversation_id": conversation_id,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        from uuid import UUID

        self.fake_chat_service.chat.assert_called_once_with(
            user_id=self.fake_user.id,
            query="continue",
            top_k=5,
            conversation_id=UUID(conversation_id),
        )

    def test_invalid_conversation_id_is_rejected(self):
        response = self.client.post(
            "/chat",
            json={
                "query": "hello",
                "conversation_id": "not-a-uuid",
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )

        self.fake_chat_service.chat.assert_not_called()

    def test_response_is_provider_independent(self):
        response = self.client.post(
            "/chat",
            json={
                "query": "hello",
            },
        )

        body = response.json()

        self.assertEqual(
            set(body),
            {
                "query",
                "answer",
            },
        )

        self.assertNotIn(
            "embedding",
            body,
        )
        self.assertNotIn(
            "chromadb",
            str(body).lower(),
        )
        self.assertNotIn(
            "ollama",
            str(body).lower(),
        )

    def test_missing_query_is_rejected(self):
        response = self.client.post(
            "/chat",
            json={},
        )

        self.assertEqual(
            response.status_code,
            422,
        )

        self.fake_chat_service.chat.assert_not_called()

    def test_empty_query_is_rejected(self):
        response = self.client.post(
            "/chat",
            json={
                "query": "",
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )

        self.fake_chat_service.chat.assert_not_called()

    def test_whitespace_query_is_rejected(self):
        response = self.client.post(
            "/chat",
            json={
                "query": "   ",
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )

        self.fake_chat_service.chat.assert_not_called()

    def test_invalid_top_k_is_rejected(self):
        response = self.client.post(
            "/chat",
            json={
                "query": "hello",
                "top_k": 0,
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )

        self.fake_chat_service.chat.assert_not_called()

    def test_chat_service_failure_is_not_silently_converted(self):
        self.fake_chat_service.chat.side_effect = RuntimeError(
            "chat failure"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "chat failure",
        ):
            self.client.post(
                "/chat",
                json={
                    "query": "hello",
                },
            )

    def test_existing_upload_and_retrieval_routes_remain_registered(self):
        paths = app.openapi()["paths"]

        self.assertIn(
            "/documents/upload",
            paths,
        )
        self.assertIn(
            "/documents/search",
            paths,
        )


if __name__ == "__main__":
    unittest.main()
