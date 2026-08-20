import unittest
from io import BytesIO

from fastapi import HTTPException, UploadFile

from app.services.document_validation import validate_document_upload


class DocumentUploadValidationTests(unittest.TestCase):
    def create_upload_file(
        self,
        filename: str | None,
        content_type: str,
    ) -> UploadFile:
        return UploadFile(
            filename=filename,
            file=BytesIO(b"test document content"),
            headers={"content-type": content_type},
        )

    def test_accepts_valid_pdf(self):
        file = self.create_upload_file(
            "document.pdf",
            "application/pdf",
        )

        validate_document_upload(file)

    def test_accepts_valid_docx(self):
        file = self.create_upload_file(
            "document.docx",
            (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )

        validate_document_upload(file)

    def test_accepts_valid_txt(self):
        file = self.create_upload_file(
            "document.txt",
            "text/plain",
        )

        validate_document_upload(file)

    def test_accepts_uppercase_extension(self):
        file = self.create_upload_file(
            "DOCUMENT.PDF",
            "application/pdf",
        )

        validate_document_upload(file)

    def test_rejects_missing_filename(self):
        file = self.create_upload_file(
            None,
            "application/pdf",
        )

        with self.assertRaises(HTTPException) as context:
            validate_document_upload(file)

        self.assertEqual(
            context.exception.status_code,
            400,
        )

        self.assertEqual(
            context.exception.detail,
            "Filename is required",
        )

    def test_rejects_blank_filename(self):
        file = self.create_upload_file(
            "   ",
            "application/pdf",
        )

        with self.assertRaises(HTTPException) as context:
            validate_document_upload(file)

        self.assertEqual(
            context.exception.status_code,
            400,
        )
    def test_accepts_filename_at_database_limit(self):
        filename = f"{'a' * 251}.pdf"

        file = self.create_upload_file(
            filename,
            "application/pdf",
        )

        validate_document_upload(file)
    def test_rejects_filename_longer_than_database_limit(self):
        filename = f"{'a' * 252}.pdf"

        file = self.create_upload_file(
            filename,
            "application/pdf",
        )

        with self.assertRaises(HTTPException) as context:
            validate_document_upload(file)

        self.assertEqual(
            context.exception.status_code,
            400,
        )

        self.assertEqual(
            context.exception.detail,
            "Filename is too long",
        )

    def test_rejects_unsupported_extension(self):
        file = self.create_upload_file(
            "malware.exe",
            "application/octet-stream",
        )

        with self.assertRaises(HTTPException) as context:
            validate_document_upload(file)

        self.assertEqual(
            context.exception.status_code,
            415,
        )

        self.assertEqual(
            context.exception.detail,
            "Unsupported document type",
        )

    def test_rejects_mismatched_extension_and_content_type(self):
        file = self.create_upload_file(
            "document.pdf",
            "text/plain",
        )

        with self.assertRaises(HTTPException) as context:
            validate_document_upload(file)

        self.assertEqual(
            context.exception.status_code,
            415,
        )

        self.assertEqual(
            context.exception.detail,
            "Filename extension does not match content type",
        )

    def test_rejects_forward_slash_in_filename(self):
        file = self.create_upload_file(
            "../document.pdf",
            "application/pdf",
        )

        with self.assertRaises(HTTPException) as context:
            validate_document_upload(file)

        self.assertEqual(
            context.exception.status_code,
            400,
        )

        self.assertEqual(
            context.exception.detail,
            "Filename must not contain path separators",
        )

    def test_rejects_backslash_in_filename(self):
        file = self.create_upload_file(
            "..\\document.pdf",
            "application/pdf",
        )

        with self.assertRaises(HTTPException) as context:
            validate_document_upload(file)

        self.assertEqual(
            context.exception.status_code,
            400,
        )

        self.assertEqual(
            context.exception.detail,
            "Filename must not contain path separators",
        )

    def test_rejects_filename_with_invalid_characters(self):
        file = self.create_upload_file(
            "document.pdf\n",
            "application/pdf",
        )

        with self.assertRaises(HTTPException) as context:
            validate_document_upload(file)

        self.assertEqual(
            context.exception.status_code,
            400,
        )

        self.assertEqual(
            context.exception.detail,
            "Filename contains invalid characters",
        )


if __name__ == "__main__":
    unittest.main()