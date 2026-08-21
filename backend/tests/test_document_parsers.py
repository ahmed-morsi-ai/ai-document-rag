import unittest
from pathlib import Path

from app.services.document_parsers.base import DocumentParser
from app.services.document_parsers.parsers import (
    DOCXDocumentParser,
    PDFDocumentParser,
    TXTDocumentParser,
)
from app.services.document_parsers.selector import (
    get_document_parser,
)


class DocumentParserTests(unittest.TestCase):
    def test_document_parser_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            DocumentParser()

    def test_selects_pdf_parser(self):
        parser = get_document_parser(
            Path("document.pdf")
        )

        self.assertIsInstance(
            parser,
            PDFDocumentParser,
        )

    def test_selects_docx_parser(self):
        parser = get_document_parser(
            Path("document.docx")
        )

        self.assertIsInstance(
            parser,
            DOCXDocumentParser,
        )

    def test_selects_txt_parser(self):
        parser = get_document_parser(
            Path("document.txt")
        )

        self.assertIsInstance(
            parser,
            TXTDocumentParser,
        )

    def test_selects_parser_case_insensitively(self):
        parser = get_document_parser(
            Path("DOCUMENT.PDF")
        )

        self.assertIsInstance(
            parser,
            PDFDocumentParser,
        )

    def test_rejects_unsupported_document_type(self):
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported document type: .exe",
        ):
            get_document_parser(
                Path("document.exe")
            )


if __name__ == "__main__":
    unittest.main()
