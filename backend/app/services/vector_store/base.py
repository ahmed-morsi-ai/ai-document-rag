from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class VectorQueryResult:
    id: str
    distance: float
    text: str
    metadata: dict[str, str]


class VectorStore(ABC):
    """Provider-independent vector storage contract."""

    @abstractmethod
    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict[str, str]] | None = None,
    ) -> None:
        """Store vectors and their associated text and metadata."""

    @abstractmethod
    def query(
        self,
        embedding: list[float],
        top_k: int = 5,
    ) -> list[VectorQueryResult]:
        """Return nearest stored vectors in provider-independent form."""
