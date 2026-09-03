from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, call
from uuid import uuid4

from app.db.models import Document
from app.services.document_deletion import DocumentDeletionService


class DocumentDeletionServiceTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = AsyncMock()
        self.vector_store = Mock()
        self.document = Mock(spec=Document)
        self.document.id = uuid4()
        self.document.storage_path = "owner/document.pdf"

    async def test_deletes_database_then_vectors_then_file(self):
        events = []

        async def db_delete(document):
            events.append(("db_delete", document))

        async def db_commit():
            events.append(("commit",))

        def vector_delete(document_id):
            events.append(("vector", document_id))

        def file_delete(storage_path):
            events.append(("file", storage_path))

        self.db.delete.side_effect = db_delete
        self.db.commit.side_effect = db_commit
        self.vector_store.delete_by_document_id.side_effect = vector_delete

        with __import__(
            "unittest.mock",
            fromlist=["patch"],
        ).patch(
            "app.services.document_deletion.delete_document",
            side_effect=file_delete,
        ):
            await DocumentDeletionService(
                db=self.db,
                vector_store=self.vector_store,
            ).delete_owned_document(self.document)

        self.assertEqual(
            events,
            [
                ("db_delete", self.document),
                ("commit",),
                ("vector", str(self.document.id)),
                ("file", self.document.storage_path),
            ],
        )
        self.db.delete.assert_awaited_once_with(self.document)
        self.db.commit.assert_awaited_once()
        self.db.rollback.assert_not_awaited()

    async def test_vector_failure_after_db_commit_does_not_touch_file(self):
        self.vector_store.delete_by_document_id.side_effect = RuntimeError(
            "vector failed"
        )

        with __import__(
            "unittest.mock",
            fromlist=["patch"],
        ).patch(
            "app.services.document_deletion.delete_document",
        ) as delete_file:
            with self.assertRaisesRegex(
                RuntimeError,
                "vector failed",
            ):
                await DocumentDeletionService(
                    db=self.db,
                    vector_store=self.vector_store,
                ).delete_owned_document(self.document)

        self.db.delete.assert_awaited_once_with(self.document)
        self.db.commit.assert_awaited_once()
        self.db.rollback.assert_not_awaited()
        self.vector_store.delete_by_document_id.assert_called_once_with(
            str(self.document.id)
        )
        delete_file.assert_not_called()

    async def test_file_failure_after_vector_delete_propagates(self):
        with __import__(
            "unittest.mock",
            fromlist=["patch"],
        ).patch(
            "app.services.document_deletion.delete_document",
            side_effect=RuntimeError("file failed"),
        ) as delete_file:
            with self.assertRaisesRegex(
                RuntimeError,
                "file failed",
            ):
                await DocumentDeletionService(
                    db=self.db,
                    vector_store=self.vector_store,
                ).delete_owned_document(self.document)

        self.db.delete.assert_awaited_once_with(self.document)
        self.db.commit.assert_awaited_once()
        self.db.rollback.assert_not_awaited()
        self.vector_store.delete_by_document_id.assert_called_once_with(
            str(self.document.id)
        )
        delete_file.assert_called_once_with(
            self.document.storage_path,
        )

    async def test_db_delete_failure_rolls_back_without_external_cleanup(self):
        self.db.delete.side_effect = RuntimeError(
            "db delete failed"
        )

        with __import__(
            "unittest.mock",
            fromlist=["patch"],
        ).patch(
            "app.services.document_deletion.delete_document",
        ) as delete_file:
            with self.assertRaisesRegex(
                RuntimeError,
                "db delete failed",
            ):
                await DocumentDeletionService(
                    db=self.db,
                    vector_store=self.vector_store,
                ).delete_owned_document(self.document)

        self.db.delete.assert_awaited_once_with(self.document)
        self.db.commit.assert_not_awaited()
        self.db.rollback.assert_awaited_once()
        self.vector_store.delete_by_document_id.assert_not_called()
        delete_file.assert_not_called()

    async def test_db_commit_failure_rolls_back_without_external_cleanup(self):
        self.db.commit.side_effect = RuntimeError(
            "db commit failed"
        )

        with __import__(
            "unittest.mock",
            fromlist=["patch"],
        ).patch(
            "app.services.document_deletion.delete_document",
        ) as delete_file:
            with self.assertRaisesRegex(
                RuntimeError,
                "db commit failed",
            ):
                await DocumentDeletionService(
                    db=self.db,
                    vector_store=self.vector_store,
                ).delete_owned_document(self.document)

        self.db.delete.assert_awaited_once_with(self.document)
        self.db.commit.assert_awaited_once()
        self.db.rollback.assert_awaited_once()
        self.vector_store.delete_by_document_id.assert_not_called()
        delete_file.assert_not_called()


if __name__ == "__main__":
    import unittest

    unittest.main()
