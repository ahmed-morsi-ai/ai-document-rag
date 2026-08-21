from dataclasses import dataclass

from app.services.embeddings.base import EmbeddingProvider
from app.services.vector_store.base import VectorStore


@dataclass(frozen=True)
class RetrievalResult:
    text: str
    document_id: str
    chunk_index: int
    distance: float
    metadata: dict[str, str]


class Retriever:
    """Retrieve indexed document chunks through existing abstractions."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError("query must not be empty")

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        query_embedding = self.embedding_provider.embed(query)

        vector_results = self.vector_store.query(
            embedding=query_embedding,
            top_k=top_k,
        )

        return [
            self._map_result(result)
            for result in vector_results
        ]

    @staticmethod
    def _map_result(result):
        metadata = dict(result.metadata)

        return RetrievalResult(
            text=result.text,
            document_id=metadata["document_id"],
            chunk_index=int(metadata["chunk_index"]),
            distance=result.distance,
            metadata=metadata,
        )
