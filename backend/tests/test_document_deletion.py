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

    async def test_deletes_vector_file_and_database_record_in_order(self):
        events = []

        self.vector_store.delete_by_document_id.side_effect = (
            lambda document_id: events.append(("vector", document_id))
        )

        with __import__(
            "unittest.mock",
            fromlist=["patch"],
        ).patch(
            "app.services.document_deletion.delete_document",
            side_effect=lambda storage_path: events.append(
                ("file", storage_path)
            ),
        ):
            async def delete_document(document):
                events.append(("db_delete", document))
            self.db.delete.side_effect = delete_document

            await DocumentDeletionService(
                db=self.db,
                vector_store=self.vector_store,
            ).delete_owned_document(self.document)

        events.append(("commit",))
        self.db.commit.assert_awaited_once()
        self.assertEqual(
            events,
            [
                ("vector", str(self.document.id)),
                ("file", self.document.storage_path),
                ("db_delete", self.document),
                ("commit",),
            ],
        )

    async def test_vector_failure_stops_before_file_and_database_cleanup(self):
        self.vector_store.delete_by_document_id.side_effect = RuntimeError(
            "vector failed"
        )

        with __import__(
            "unittest.mock",
            fromlist=["patch"],
        ).patch(
            "app.services.document_deletion.delete_document"
        ) as delete_file:
            with self.assertRaisesRegex(
                RuntimeError,
                "vector failed",
            ):
                await DocumentDeletionService(
                    db=self.db,
                    vector_store=self.vector_store,
                ).delete_owned_document(self.document)

        delete_file.assert_not_called()
        self.db.delete.assert_not_awaited()
        self.db.commit.assert_not_awaited()

    async def test_file_failure_stops_before_database_deletion(self):
        with __import__(
            "unittest.mock",
            fromlist=["patch"],
        ).patch(
            "app.services.document_deletion.delete_document",
            side_effect=RuntimeError("file failed"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "file failed",
            ):
                await DocumentDeletionService(
                    db=self.db,
                    vector_store=self.vector_store,
                ).delete_owned_document(self.document)

        self.vector_store.delete_by_document_id.assert_called_once_with(
            str(self.document.id)
        )
        self.db.delete.assert_not_awaited()
        self.db.commit.assert_not_awaited()

    async def test_database_failure_is_propagated_after_external_cleanup(self):
        self.db.commit.side_effect = RuntimeError("db failed")

        with __import__(
            "unittest.mock",
            fromlist=["patch"],
        ).patch(
            "app.services.document_deletion.delete_document"
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "db failed",
            ):
                await DocumentDeletionService(
                    db=self.db,
                    vector_store=self.vector_store,
                ).delete_owned_document(self.document)

        self.vector_store.delete_by_document_id.assert_called_once_with(
            str(self.document.id)
        )
        self.db.delete.assert_awaited_once_with(self.document)
        self.db.commit.assert_awaited_once()


if __name__ == "__main__":
    import unittest

    unittest.main()
