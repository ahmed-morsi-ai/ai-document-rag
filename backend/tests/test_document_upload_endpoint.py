import os
import unittest
from unittest import mock
from uuid import uuid4

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_document_rag",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.main import app


class DocumentUploadEndpointTests(unittest.TestCase):
    def setUp(self):
        self.user = mock.Mock(
            id=uuid4(),
            is_active=True,
        )

        app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_accepts_authenticated_valid_pdf_upload(self):
        response = self.client.post(
            "/documents/upload",
            files={
                "file": (
                    "document.pdf",
                    b"%PDF-test-content",
                    "application/pdf",
                )
            },
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.json(),
            {"detail": "Document upload accepted"},
        )

    def test_rejects_unsupported_document_type(self):
        response = self.client.post(
            "/documents/upload",
            files={
                "file": (
                    "malware.exe",
                    b"test content",
                    "application/octet-stream",
                )
            },
        )

        self.assertEqual(response.status_code, 415)
        self.assertEqual(
            response.json()["detail"],
            "Unsupported document type",
        )

    def test_requires_authentication(self):
        app.dependency_overrides.clear()

        response = self.client.post(
            "/documents/upload",
            files={
                "file": (
                    "document.pdf",
                    b"%PDF-test-content",
                    "application/pdf",
                )
            },
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()