import os
import tempfile
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

from app.services.document_storage import (
    delete_document,
    generate_storage_path,
    get_storage_root,
    store_document,
)


class DocumentStorageTests(unittest.IsolatedAsyncioTestCase):
    def create_upload_file(
        self,
        filename: str,
        content: bytes = b"test document content",
    ) -> UploadFile:
        return UploadFile(
            filename=filename,
            file=BytesIO(content),
        )

    def test_get_storage_root_returns_absolute_path(self):
        storage_root = get_storage_root()

        self.assertTrue(storage_root.is_absolute())

    def test_generate_storage_path_is_relative_and_scoped_to_owner(self):
        owner_id = uuid4()

        storage_path = generate_storage_path(
            owner_id,
            "document.pdf",
        )

        self.assertFalse(storage_path.is_absolute())
        self.assertEqual(
            storage_path.parent,
            Path(str(owner_id)),
        )
        self.assertEqual(
            storage_path.suffix,
            ".pdf",
        )

    def test_generate_storage_path_produces_unique_filenames(self):
        owner_id = uuid4()

        first_path = generate_storage_path(
            owner_id,
            "document.pdf",
        )
        second_path = generate_storage_path(
            owner_id,
            "document.pdf",
        )

        self.assertNotEqual(
            first_path,
            second_path,
        )

    async def test_store_document_creates_directory_and_writes_file(self):
        owner_id = uuid4()
        content = b"stored document content"

        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir)

            with mock.patch(
                "app.services.document_storage.get_storage_root",
                return_value=storage_root,
            ):
                file = self.create_upload_file(
                    "document.pdf",
                    content,
                )

                relative_path = await store_document(
                    file,
                    owner_id,
                )

            destination = storage_root / relative_path

            self.assertFalse(
                Path(relative_path).is_absolute()
            )
            self.assertTrue(
                destination.exists()
            )
            self.assertEqual(
                destination.read_bytes(),
                content,
            )
            self.assertEqual(
                destination.parent,
                storage_root / str(owner_id),
            )

    async def test_store_document_does_not_overwrite_existing_file(self):
        owner_id = uuid4()

        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir)

            relative_path = (
                Path(str(owner_id))
                / "existing.pdf"
            )
            destination = storage_root / relative_path

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            destination.write_bytes(
                b"original content"
            )

            with (
                mock.patch(
                    "app.services.document_storage.get_storage_root",
                    return_value=storage_root,
                ),
                mock.patch(
                    "app.services.document_storage.generate_storage_path",
                    return_value=relative_path,
                ),
            ):
                file = self.create_upload_file(
                    "document.pdf",
                    b"replacement content",
                )

                with self.assertRaises(
                    FileExistsError
                ):
                    await store_document(
                        file,
                        owner_id,
                    )

            self.assertEqual(
                destination.read_bytes(),
                b"original content",
            )

    async def test_store_document_removes_partial_file_on_write_error(self):
        owner_id = uuid4()

        relative_path = (
            Path(str(owner_id))
            / "partial.pdf"
        )

        original_open = Path.open

        class FailingFile:
            def __init__(self, path: Path):
                self.path = path
                self.file = original_open(
                    path,
                    "xb",
                )

            def write(self, data: bytes):
                self.file.write(data[:1])
                self.file.flush()

                raise OSError(
                    "simulated write error"
                )

            def __enter__(self):
                return self

            def __exit__(
                self,
                exc_type,
                exc_value,
                traceback,
            ):
                self.file.close()
                return False

        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir)
            destination = (
                storage_root / relative_path
            )

            def open_with_partial_write(
                path: Path,
                mode="r",
                *args,
                **kwargs,
            ):
                return FailingFile(path)

            with (
                mock.patch(
                    "app.services.document_storage.get_storage_root",
                    return_value=storage_root,
                ),
                mock.patch(
                    "app.services.document_storage.generate_storage_path",
                    return_value=relative_path,
                ),
                mock.patch(
                    "pathlib.Path.open",
                    side_effect=open_with_partial_write,
                ),
            ):
                file = self.create_upload_file(
                    "document.pdf",
                    b"partial content",
                )

                with self.assertRaises(OSError):
                    await store_document(
                        file,
                        owner_id,
                    )

            self.assertFalse(
                destination.exists()
            )

    def test_delete_document_removes_existing_file(self):
        owner_id = uuid4()

        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir)
            relative_path = (
                Path(str(owner_id))
                / "document.pdf"
            )
            destination = (
                storage_root / relative_path
            )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            destination.write_bytes(
                b"document content"
            )

            with mock.patch(
                "app.services.document_storage.get_storage_root",
                return_value=storage_root,
            ):
                delete_document(
                    str(relative_path)
                )

            self.assertFalse(
                destination.exists()
            )

    def test_delete_document_ignores_missing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir)

            with mock.patch(
                "app.services.document_storage.get_storage_root",
                return_value=storage_root,
            ):
                delete_document(
                    "missing/document.pdf"
                )

    def test_delete_document_rejects_path_outside_storage_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir)

            with mock.patch(
                "app.services.document_storage.get_storage_root",
                return_value=storage_root,
            ):
                with self.assertRaises(ValueError):
                    delete_document(
                        "../outside.pdf"
                    )


if __name__ == "__main__":
    unittest.main()