from pathlib import Path

from app.services.document_parsers.base import DocumentParser
from app.services.document_parsers.parsers import (
    DOCXDocumentParser,
    PDFDocumentParser,
    TXTDocumentParser,
)


def get_document_parser(
    file_path: Path,
) -> DocumentParser:
    suffix = file_path.suffix.lower()

    parsers = {
        ".pdf": PDFDocumentParser,
        ".docx": DOCXDocumentParser,
        ".txt": TXTDocumentParser,
    }

    parser_class = parsers.get(suffix)

    if parser_class is None:
        raise ValueError(
            f"Unsupported document type: {suffix}"
        )

    return parser_class()
