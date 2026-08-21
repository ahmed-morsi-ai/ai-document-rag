from abc import ABC, abstractmethod
from pathlib import Path


class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> str:
        """Extract text content from a document."""
