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
        owner_id: str | None = None,
    ) -> list[VectorQueryResult]:
        """Return nearest stored vectors in provider-independent form.

        When ``owner_id`` is provided, results must be restricted to that
        owner at the vector-store level.
        """


    @abstractmethod
    def delete_by_document_id(self, document_id: str) -> None:
        """Delete all vectors belonging to the specified document."""
