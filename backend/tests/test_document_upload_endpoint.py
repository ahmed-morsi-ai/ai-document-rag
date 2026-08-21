import os
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock
from uuid import uuid4

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_document_rag",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from fastapi import UploadFile
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from app.api.dependencies.auth import get_current_user
from app.db.database import get_db
from app.api.routes.documents import upload_document
from app.db.models import Document, User
from app.main import app


class DocumentUploadEndpointTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.owner_id = uuid4()
        self.user = mock.Mock(
            id=self.owner_id,
            is_active=True,
        )
        self.mock_db = mock.Mock()
        self.mock_db.commit = mock.AsyncMock()
        self.mock_db.refresh = mock.AsyncMock()
        self.mock_db.rollback = mock.AsyncMock()

        app.dependency_overrides[get_current_user] = (
            lambda: self.user
        )

        async def override_get_db():
            yield self.mock_db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_accepts_authenticated_valid_pdf_upload(self):
        with mock.patch(
            "app.api.routes.documents.get_document_indexer",
        ) as mock_get_indexer:
            mock_get_indexer.return_value.index_document.return_value = 1

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

        self.assertEqual(response.status_code, 201)

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

    async def test_authenticated_upload_persists_document_and_indexes_it(self):
        content = b"test document content"

        storage_path = (
            Path(str(self.owner_id))
            / "document.pdf"
        )

        mock_user = mock.Mock(
            id=self.owner_id,
        )

        mock_db = mock.Mock()
        mock_db.commit = mock.AsyncMock()
        mock_db.refresh = mock.AsyncMock()
        mock_db.rollback = mock.AsyncMock()

        mock_indexer = mock.Mock()

        with (
            mock.patch(
                "app.api.routes.documents.store_document",
                new_callable=mock.AsyncMock,
                return_value=str(storage_path),
            ) as mock_store_document,
            mock.patch(
                "app.api.routes.documents.validate_document_upload",
            ) as mock_validate,
            mock.patch(
                "app.api.routes.documents.get_document_indexer",
                return_value=mock_indexer,
            ) as mock_get_indexer,
            mock.patch(
                "app.api.routes.documents.get_storage_root",
                return_value=Path("/tmp/document-storage"),
            ),
        ):
            file = UploadFile(
                filename="document.pdf",
                file=BytesIO(content),
                headers=Headers(
                    {"content-type": "application/pdf"}
                ),
            )

            result = await upload_document(
                file=file,
                current_user=mock_user,
                db=mock_db,
            )

        mock_validate.assert_called_once_with(file)
        mock_store_document.assert_awaited_once_with(
            file,
            self.owner_id,
        )
        mock_db.add.assert_called_once_with(result)
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once_with(result)
        mock_get_indexer.assert_called_once_with()

        mock_indexer.index_document.assert_called_once_with(
            document_id=str(result.id),
            file_path=Path(
                "/tmp/document-storage"
            ) / str(storage_path),
        )

        self.assertIsInstance(result, Document)
        self.assertEqual(result.owner_id, self.owner_id)
        self.assertEqual(
            result.original_filename,
            "document.pdf",
        )
        self.assertEqual(
            result.mime_type,
            "application/pdf",
        )
        self.assertEqual(
            result.storage_path,
            str(storage_path),
        )

    async def test_indexing_failure_propagates(self):
        storage_path = (
            Path(str(self.owner_id))
            / "document.pdf"
        )

        mock_db = mock.Mock()
        mock_db.commit = mock.AsyncMock()
        mock_db.refresh = mock.AsyncMock()
        mock_db.rollback = mock.AsyncMock()

        mock_indexer = mock.Mock()
        mock_indexer.index_document.side_effect = RuntimeError(
            "indexing failed"
        )

        with (
            mock.patch(
                "app.api.routes.documents.store_document",
                new_callable=mock.AsyncMock,
                return_value=str(storage_path),
            ),
            mock.patch(
                "app.api.routes.documents.get_document_indexer",
                return_value=mock_indexer,
            ),
            mock.patch(
                "app.api.routes.documents.get_storage_root",
                return_value=Path("/tmp/document-storage"),
            ),
        ):
            file = UploadFile(
                filename="document.pdf",
                file=BytesIO(b"document"),
                headers=Headers(
                    {"content-type": "application/pdf"}
                ),
            )

            with self.assertRaisesRegex(
                RuntimeError,
                "indexing failed",
            ):
                await upload_document(
                    file=file,
                    current_user=self.user,
                    db=mock_db,
                )

        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    async def test_storage_failure_does_not_invoke_indexing(self):
        mock_indexer = mock.Mock()

        with (
            mock.patch(
                "app.api.routes.documents.store_document",
                new_callable=mock.AsyncMock,
                side_effect=RuntimeError("storage failed"),
            ),
            mock.patch(
                "app.api.routes.documents.get_document_indexer",
                return_value=mock_indexer,
            ),
        ):
            file = UploadFile(
                filename="document.pdf",
                file=BytesIO(b"document"),
                headers=Headers(
                    {"content-type": "application/pdf"}
                ),
            )

            with self.assertRaisesRegex(
                RuntimeError,
                "storage failed",
            ):
                await upload_document(
                    file=file,
                    current_user=self.user,
                    db=self.mock_db,
                )

        mock_indexer.index_document.assert_not_called()

    async def test_database_failure_does_not_invoke_indexing(self):
        storage_path = (
            Path(str(self.owner_id))
            / "document.pdf"
        )

        mock_db = mock.Mock()
        mock_db.commit = mock.AsyncMock(
            side_effect=RuntimeError(
                "database commit failed"
            )
        )
        mock_db.rollback = mock.AsyncMock()
        mock_db.refresh = mock.AsyncMock()

        mock_indexer = mock.Mock()

        with (
            mock.patch(
                "app.api.routes.documents.store_document",
                new_callable=mock.AsyncMock,
                return_value=str(storage_path),
            ),
            mock.patch(
                "app.api.routes.documents.delete_document",
            ),
            mock.patch(
                "app.api.routes.documents.get_document_indexer",
                return_value=mock_indexer,
            ),
        ):
            file = UploadFile(
                filename="document.pdf",
                file=BytesIO(b"document"),
                headers=Headers(
                    {"content-type": "application/pdf"}
                ),
            )

            with self.assertRaisesRegex(
                RuntimeError,
                "database commit failed",
            ):
                await upload_document(
                    file=file,
                    current_user=self.user,
                    db=mock_db,
                )

        mock_db.rollback.assert_awaited_once()
        mock_indexer.index_document.assert_not_called()

    async def test_database_failure_removes_stored_file(self):
        content = b"test document content"
        storage_path = (
            Path(str(self.owner_id))
            / "document.pdf"
        )

        mock_db = mock.Mock()
        mock_db.commit = mock.AsyncMock(
            side_effect=Exception(
                "database commit failed"
            )
        )
        mock_db.rollback = mock.AsyncMock()

        with (
            mock.patch(
                "app.api.routes.documents.store_document",
                new_callable=mock.AsyncMock,
                return_value=str(storage_path),
            ),
            mock.patch(
                "app.api.routes.documents.delete_document",
            ) as mock_delete_document,
        ):
            file = UploadFile(
                filename="document.pdf",
                file=BytesIO(content),
                headers=Headers(
                    {
                        "content-type":
                        "application/pdf"
                    }
                ),
            )

            with self.assertRaisesRegex(
                Exception,
                "database commit failed",
            ):
                await upload_document(
                    file=file,
                    current_user=self.user,
                    db=mock_db,
                )

        mock_db.rollback.assert_awaited_once()
        mock_delete_document.assert_called_once_with(
            str(storage_path)
        )


if __name__ == "__main__":
    unittest.main()