import os
import unittest
from unittest import mock

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_document_rag",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.main import app
from app.services.retrieval import RetrievalResult
from app.services.retrieval_factory import get_retriever


class RetrievalEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        self.fake_user = mock.Mock(
            id="user-1",
            is_active=True,
        )

        self.fake_retriever = mock.Mock()
        self.fake_retriever.retrieve.return_value = [
            RetrievalResult(
                text="first chunk",
                document_id="document-1",
                chunk_index=0,
                distance=0.1,
                metadata={
                    "document_id": "document-1",
                    "chunk_index": "0",
                },
            ),
            RetrievalResult(
                text="second chunk",
                document_id="document-1",
                chunk_index=1,
                distance=0.2,
                metadata={
                    "document_id": "document-1",
                    "chunk_index": "1",
                },
            ),
        ]

        async def override_current_user():
            return self.fake_user

        def override_retriever():
            return self.fake_retriever

        app.dependency_overrides[get_current_user] = (
            override_current_user
        )
        app.dependency_overrides[get_retriever] = (
            override_retriever
        )

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_unauthenticated_request_is_rejected(self):
        app.dependency_overrides.clear()

        response = self.client.post(
            "/documents/search",
            json={
                "query": "hello",
                "top_k": 5,
            },
        )

        self.assertEqual(
            response.status_code,
            401,
        )

        self.fake_retriever.retrieve.assert_not_called()

    def test_authenticated_request_succeeds(self):
        response = self.client.post(
            "/documents/search",
            json={
                "query": "hello",
                "top_k": 2,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_query_and_top_k_reach_retriever_unchanged(self):
        response = self.client.post(
            "/documents/search",
            json={
                "query": "what is the refund policy?",
                "top_k": 7,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.fake_retriever.retrieve.assert_called_once_with(
            query="what is the refund policy?",
            top_k=7,
        )

    def test_multiple_results_preserve_order_and_fields(self):
        response = self.client.post(
            "/documents/search",
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
                "results": [
                    {
                        "text": "first chunk",
                        "document_id": "document-1",
                        "chunk_index": 0,
                        "distance": 0.1,
                        "metadata": {
                            "document_id": "document-1",
                            "chunk_index": "0",
                        },
                    },
                    {
                        "text": "second chunk",
                        "document_id": "document-1",
                        "chunk_index": 1,
                        "distance": 0.2,
                        "metadata": {
                            "document_id": "document-1",
                            "chunk_index": "1",
                        },
                    },
                ]
            },
        )

    def test_empty_results_return_successful_empty_collection(self):
        self.fake_retriever.retrieve.return_value = []

        response = self.client.post(
            "/documents/search",
            json={
                "query": "missing",
                "top_k": 5,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json(),
            {
                "results": [],
            },
        )

    def test_empty_query_is_rejected(self):
        response = self.client.post(
            "/documents/search",
            json={
                "query": "",
                "top_k": 5,
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )
        self.fake_retriever.retrieve.assert_not_called()

    def test_whitespace_query_is_rejected(self):
        response = self.client.post(
            "/documents/search",
            json={
                "query": "   ",
                "top_k": 5,
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )
        self.fake_retriever.retrieve.assert_not_called()

    def test_non_positive_top_k_is_rejected(self):
        response = self.client.post(
            "/documents/search",
            json={
                "query": "hello",
                "top_k": 0,
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )
        self.fake_retriever.retrieve.assert_not_called()

    def test_negative_top_k_is_rejected(self):
        response = self.client.post(
            "/documents/search",
            json={
                "query": "hello",
                "top_k": -1,
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )
        self.fake_retriever.retrieve.assert_not_called()

    def test_retriever_failure_does_not_return_success(self):
        self.fake_retriever.retrieve.side_effect = RuntimeError(
            "retrieval failure"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "retrieval failure",
        ):
            self.client.post(
                "/documents/search",
                json={
                    "query": "hello",
                    "top_k": 5,
                },
            )

    def test_response_does_not_expose_provider_specific_data(self):
        response = self.client.post(
            "/documents/search",
            json={
                "query": "hello",
                "top_k": 1,
            },
        )

        body = response.json()

        self.assertNotIn(
            "embedding",
            body,
        )
        self.assertNotIn(
            "collection",
            body,
        )
        self.assertNotIn(
            "chromadb",
            str(body).lower(),
        )

    def test_existing_upload_route_remains_registered(self):
        paths = app.openapi()["paths"]

        self.assertIn(
            "/documents/upload",
            paths,
        )


if __name__ == "__main__":
    unittest.main()
