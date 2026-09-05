from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException
import os
import unittest
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from unittest import mock
from uuid import uuid4

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_document_rag",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-key-32-bytes-long")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from fastapi import UploadFile
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from app.api.dependencies.auth import get_current_user
from app.db.database import get_db
from app.api.routes.documents import upload_document
from app.api.routes.documents import list_documents
from app.schemas.documents import DocumentListResponse
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
            owner_id=str(self.owner_id),
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

    async def test_indexing_failure_triggers_vector_cleanup_and_preserves_artifacts(
        self,
    ):
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

        mock_vector_store = mock.Mock()

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
                "app.api.routes.documents.get_vector_store",
                return_value=mock_vector_store,
            ),
            mock.patch(
                "app.api.routes.documents.get_storage_root",
                return_value=Path("/tmp/document-storage"),
            ),
            mock.patch(
                "app.api.routes.documents.delete_document",
            ) as mock_delete_document,
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
        mock_db.refresh.assert_awaited_once_with(
            mock.ANY,
        )
        mock_db.rollback.assert_not_awaited()
        mock_vector_store.delete_by_document_id.assert_called_once_with(
            mock.ANY,
        )
        self.assertEqual(
            mock_vector_store.delete_by_document_id.call_args.args[0],
            str(mock_db.refresh.call_args.args[0].id),
        )
        mock_delete_document.assert_not_called()


    async def test_vector_cleanup_failure_preserves_original_indexing_failure(
        self,
    ):
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

        mock_vector_store = mock.Mock()
        mock_vector_store.delete_by_document_id.side_effect = RuntimeError(
            "vector cleanup failed"
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
                "app.api.routes.documents.get_vector_store",
                return_value=mock_vector_store,
            ),
            mock.patch(
                "app.api.routes.documents.get_storage_root",
                return_value=Path("/tmp/document-storage"),
            ),
            mock.patch(
                "app.api.routes.documents.delete_document",
            ) as mock_delete_document,
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
        mock_db.rollback.assert_not_awaited()
        mock_vector_store.delete_by_document_id.assert_called_once()
        mock_delete_document.assert_not_called()

    def test_indexing_failure_returns_generic_500(self):
        storage_path = (
            Path(str(self.owner_id))
            / "document.pdf"
        )

        mock_indexer = mock.Mock()
        mock_indexer.index_document.side_effect = RuntimeError(
            "indexing failed secret"
        )

        mock_vector_store = mock.Mock()

        self.client = TestClient(
            app,
            raise_server_exceptions=False,
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
                "app.api.routes.documents.get_vector_store",
                return_value=mock_vector_store,
            ),
            mock.patch(
                "app.api.routes.documents.get_storage_root",
                return_value=Path("/tmp/document-storage"),
            ),
        ):
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

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {"detail": "Internal server error"},
        )
        self.assertNotIn(
            "indexing failed secret",
            response.text,
        )


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

class DocumentListEndpointTests(unittest.TestCase):
    def setUp(self):
        self.owner_id = uuid4()
        self.user = mock.Mock(
            id=self.owner_id,
            is_active=True,
        )

        self.mock_db = mock.Mock()
        self.mock_db.execute = mock.AsyncMock()

        app.dependency_overrides[get_current_user] = (
            lambda: self.user
        )

        async def override_get_db():
            yield self.mock_db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def _count_result(self, count):
        result = mock.Mock()
        result.scalar_one.return_value = count
        return result

    def _items_result(self, documents):
        scalars = mock.Mock()
        scalars.all.return_value = documents

        result = mock.Mock()
        result.scalars.return_value = scalars
        return result

    def test_requires_authentication(self):
        app.dependency_overrides.clear()

        response = self.client.get("/documents")

        self.assertEqual(response.status_code, 401)

    def test_returns_owned_documents(self):
        older = Document(
            id=uuid4(),
            owner_id=self.owner_id,
            original_filename="older.pdf",
            mime_type="application/pdf",
            storage_path="owned/older.pdf",
            processing_status="uploaded",
            created_at=datetime(
                2026,
                8,
                22,
                20,
                0,
                tzinfo=timezone.utc,
            ),
            updated_at=datetime(
                2026,
                8,
                22,
                20,
                0,
                tzinfo=timezone.utc,
            ),
        )
        newer = Document(
            id=uuid4(),
            owner_id=self.owner_id,
            original_filename="newer.pdf",
            mime_type="application/pdf",
            storage_path="owned/newer.pdf",
            processing_status="uploaded",
            created_at=datetime(
                2026,
                8,
                22,
                21,
                0,
                tzinfo=timezone.utc,
            ),
            updated_at=datetime(
                2026,
                8,
                22,
                21,
                0,
                tzinfo=timezone.utc,
            ),
        )

        self.mock_db.execute.side_effect = [
            self._count_result(2),
            self._items_result([newer, older]),
        ]

        response = self.client.get("/documents")

        self.assertEqual(response.status_code, 200)

        body = response.json()

        self.assertEqual(body["total_count"], 2)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["page_size"], 20)
        self.assertEqual(
            [item["original_filename"] for item in body["items"]],
            ["newer.pdf", "older.pdf"],
        )
        self.assertNotIn("owner_id", body["items"][0])
        self.assertNotIn("storage_path", body["items"][0])

    def test_empty_document_list_returns_empty_collection(self):
        self.mock_db.execute.side_effect = [
            self._count_result(0),
            self._items_result([]),
        ]

        response = self.client.get("/documents")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "items": [],
                "total_count": 0,
                "page": 1,
                "page_size": 20,
            },
        )

    def test_filename_search_returns_filtered_results_and_count(self):
        matching = Document(
            id=uuid4(),
            owner_id=self.owner_id,
            original_filename="Quarterly-Report.pdf",
            mime_type="application/pdf",
            storage_path="owned/report.pdf",
            processing_status="uploaded",
            created_at=datetime(
                2026,
                8,
                22,
                21,
                0,
                tzinfo=timezone.utc,
            ),
            updated_at=datetime(
                2026,
                8,
                22,
                21,
                0,
                tzinfo=timezone.utc,
            ),
        )

        self.mock_db.execute.side_effect = [
            self._count_result(1),
            self._items_result([matching]),
        ]

        response = self.client.get(
            "/documents",
            params={
                "search": "quarterly",
                "page": 1,
                "page_size": 20,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_count"], 1)
        self.assertEqual(
            response.json()["items"][0]["original_filename"],
            "Quarterly-Report.pdf",
        )

    def test_filename_search_can_be_case_insensitive(self):
        matching = Document(
            id=uuid4(),
            owner_id=self.owner_id,
            original_filename="Quarterly-Report.pdf",
            mime_type="application/pdf",
            storage_path="owned/report.pdf",
            processing_status="uploaded",
            created_at=datetime(
                2026,
                8,
                22,
                21,
                0,
                tzinfo=timezone.utc,
            ),
            updated_at=datetime(
                2026,
                8,
                22,
                21,
                0,
                tzinfo=timezone.utc,
            ),
        )

        self.mock_db.execute.side_effect = [
            self._count_result(1),
            self._items_result([matching]),
        ]

        response = self.client.get(
            "/documents",
            params={"search": "REPORT"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_count"], 1)
        self.assertEqual(
            response.json()["items"][0]["original_filename"],
            "Quarterly-Report.pdf",
        )

    def test_missing_search_behaves_as_unfiltered_list(self):
        self.mock_db.execute.side_effect = [
            self._count_result(0),
            self._items_result([]),
        ]

        response = self.client.get("/documents")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_count"], 0)

    def test_empty_search_behaves_as_unfiltered_list(self):
        self.mock_db.execute.side_effect = [
            self._count_result(0),
            self._items_result([]),
        ]

        response = self.client.get(
            "/documents",
            params={"search": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_count"], 0)

    def test_page_and_page_size_are_returned(self):
        self.mock_db.execute.side_effect = [
            self._count_result(3),
            self._items_result([]),
        ]

        response = self.client.get(
            "/documents",
            params={"page": 2, "page_size": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["page"],
            2,
        )
        self.assertEqual(
            response.json()["page_size"],
            2,
        )

    def test_beyond_range_returns_empty_items(self):
        self.mock_db.execute.side_effect = [
            self._count_result(3),
            self._items_result([]),
        ]

        response = self.client.get(
            "/documents",
            params={"page": 3, "page_size": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])
        self.assertEqual(response.json()["total_count"], 3)

    def test_page_below_one_is_rejected(self):
        response = self.client.get(
            "/documents",
            params={"page": 0},
        )

        self.assertEqual(response.status_code, 422)

    def test_page_size_below_one_is_rejected(self):
        response = self.client.get(
            "/documents",
            params={"page_size": 0},
        )

        self.assertEqual(response.status_code, 422)

    def test_page_size_above_maximum_is_rejected(self):
        response = self.client.get(
            "/documents",
            params={"page_size": 101},
        )

        self.assertEqual(response.status_code, 422)

    def test_authenticated_list_keeps_owner_filter_and_deterministic_order(self):
        self.mock_db.execute.side_effect = [
            self._count_result(0),
            self._items_result([]),
        ]

        response = self.client.get("/documents")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.mock_db.execute.await_count, 2)

        count_statement = self.mock_db.execute.await_args_list[0].args[0]
        items_statement = self.mock_db.execute.await_args_list[1].args[0]

        count_sql = str(
            count_statement.compile(compile_kwargs={"literal_binds": True})
        )
        items_sql = str(
            items_statement.compile(compile_kwargs={"literal_binds": True})
        )

        self.assertIn("owner_id", count_sql)
        self.assertIn("owner_id", items_sql)
        self.assertIn(self.owner_id.hex, count_sql)
        self.assertIn(self.owner_id.hex, items_sql)
        self.assertIn("created_at DESC", items_sql)
        self.assertIn("id DESC", items_sql)

    def test_search_total_count_is_filtered_population(self):
        self.mock_db.execute.side_effect = [
            self._count_result(4),
            self._items_result([]),
        ]

        response = self.client.get(
            "/documents",
            params={
                "search": "report",
                "page": 1,
                "page_size": 2,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_count"], 4)

        count_statement = self.mock_db.execute.await_args_list[0].args[0]
        items_statement = self.mock_db.execute.await_args_list[1].args[0]

        count_sql = str(
            count_statement.compile(compile_kwargs={"literal_binds": True})
        )
        items_sql = str(
            items_statement.compile(compile_kwargs={"literal_binds": True})
        )

        self.assertIn("original_filename", count_sql)
        self.assertIn("original_filename", items_sql)
        self.assertIn("report", count_sql.lower())
        self.assertIn("report", items_sql.lower())


class DocumentDeleteEndpointTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_delete_route_exists_and_requires_authentication(self):
        response = self.client.delete(
            "/documents/00000000-0000-4000-8000-000000000001"
        )
        self.assertEqual(response.status_code, 401)

    async def test_owned_document_deletion_uses_service(self):
        from unittest.mock import AsyncMock, patch
        from uuid import UUID

        owner_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        document_id = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
        user = Mock(id=owner_id, is_active=True)
        document = Mock(
            id=document_id,
            owner_id=owner_id,
            storage_path="owner/document.pdf",
        )

        db = AsyncMock()

        result = Mock()
        result.scalar_one_or_none.return_value = document
        db.execute.return_value = result

        service = Mock()
        service.delete_owned_document = AsyncMock()

        with patch(
            "app.api.routes.documents.get_vector_store",
        ), patch(
            "app.api.routes.documents.DocumentDeletionService",
            return_value=service,
        ):
            from app.api.routes.documents import delete_document_route

            await delete_document_route(
                str(document_id),
                current_user=user,
                db=db,
            )

        service.delete_owned_document.assert_awaited_once_with(document)

    async def test_other_user_document_is_not_accessible(self):
        from uuid import UUID

        owner_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        other_id = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
        document_id = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")

        user = Mock(id=other_id, is_active=True)
        db = AsyncMock()
        result = Mock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        from app.api.routes.documents import delete_document_route

        with self.assertRaises(HTTPException) as context:
            await delete_document_route(
                str(document_id),
                current_user=user,
                db=db,
            )

        self.assertEqual(context.exception.status_code, 404)

    async def test_missing_document_is_not_found(self):
        from uuid import UUID

        user = Mock(
            id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
            is_active=True,
        )

        db = AsyncMock()
        result = Mock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        from app.api.routes.documents import delete_document_route

        with self.assertRaises(HTTPException) as context:
            await delete_document_route(
                "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                current_user=user,
                db=db,
            )

        self.assertEqual(context.exception.status_code, 404)
