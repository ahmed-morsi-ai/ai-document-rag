from pathlib import Path

from app.services.document_parsers.base import DocumentParser


class PDFDocumentParser(DocumentParser):
    def parse(self, file_path: Path) -> str:
        raise NotImplementedError


class DOCXDocumentParser(DocumentParser):
    def parse(self, file_path: Path) -> str:
        raise NotImplementedError


class TXTDocumentParser(DocumentParser):
    def parse(self, file_path: Path) -> str:
        raise NotImplementedError
