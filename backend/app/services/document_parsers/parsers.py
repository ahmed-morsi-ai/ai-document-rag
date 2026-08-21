from pathlib import Path

from app.services.document_parsers.base import DocumentParser


class PDFDocumentParser(DocumentParser):
    def parse(self, file_path: Path) -> str:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )


class DOCXDocumentParser(DocumentParser):
    def parse(self, file_path: Path) -> str:
        from docx import Document

        document = Document(file_path)
        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )


class TXTDocumentParser(DocumentParser):
    def parse(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8")
