import tempfile
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


    def test_txt_parser_extracts_text_from_real_file(self):
        original_text = "Hello from a real UTF-8 text document.\nSecond line."

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "document.txt"
            file_path.write_text(
                original_text,
                encoding="utf-8",
            )

            result = TXTDocumentParser().parse(file_path)

        self.assertEqual(result, original_text)

    def test_pdf_parser_extracts_text_from_real_file(self):
        original_text = "Hello from a real PDF document."

        def create_pdf(text: str) -> bytes:
            escaped_text = (
                text.replace("\\", "\\\\")
                .replace("(", "\\(")
                .replace(")", "\\)")
            )

            objects = [
                b"<< /Type /Catalog /Pages 2 0 R >>",
                b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                b"/Resources << /Font << /F1 5 0 R >> >> "
                b"/Contents 4 0 R >>",
                (
                    f"<< /Length {len(('BT /F1 18 Tf 72 720 Td (' + escaped_text + ') Tj ET').encode('latin-1'))} >>"
                    .encode("latin-1")
                    + b"\nstream\n"
                    + (
                        f"BT /F1 18 Tf 72 720 Td ({escaped_text}) Tj ET"
                    ).encode("latin-1")
                    + b"\nendstream"
                ),
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            ]

            pdf = b"%PDF-1.4\n"
            offsets = [0]

            for index, obj in enumerate(objects, start=1):
                offsets.append(len(pdf))
                pdf += f"{index} 0 obj\n".encode("ascii")
                pdf += obj
                pdf += b"\nendobj\n"

            xref_offset = len(pdf)
            pdf += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
            pdf += b"0000000000 65535 f \n"

            for offset in offsets[1:]:
                pdf += f"{offset:010d} 00000 n \n".encode("ascii")

            pdf += (
                f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref_offset}\n%%EOF\n"
            ).encode("ascii")

            return pdf

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "document.pdf"
            file_path.write_bytes(create_pdf(original_text))

            result = PDFDocumentParser().parse(file_path)

        self.assertIn(original_text, result)

    def test_docx_parser_extracts_text_from_real_file(self):
        original_paragraphs = [
            "Hello from a real DOCX document.",
            "Second paragraph.",
        ]

        from docx import Document

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "document.docx"

            document = Document()
            for paragraph_text in original_paragraphs:
                document.add_paragraph(paragraph_text)
            document.save(file_path)

            result = DOCXDocumentParser().parse(file_path)

        self.assertEqual(
            result,
            "\n".join(original_paragraphs),
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
