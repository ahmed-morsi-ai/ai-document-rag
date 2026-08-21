from pathlib import Path

from app.services.document_chunking import chunk_text
from app.services.document_parsers.selector import get_document_parser
from app.services.embeddings.base import EmbeddingProvider
from app.services.vector_store.base import VectorStore


class DocumentIndexer:
    """Orchestrate document parsing, chunking, embedding, and vector storage."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    def index_document(
        self,
        document_id: str,
        file_path: Path,
    ) -> int:
        if not document_id:
            raise ValueError("document_id must not be empty")

        parser = get_document_parser(file_path)
        extracted_text = parser.parse(file_path)
        chunks = chunk_text(extracted_text)

        if not chunks:
            return 0

        embeddings = self.embedding_provider.embed_many(
            chunks
        )

        vector_ids = [
            f"{document_id}:{chunk_index}"
            for chunk_index in range(len(chunks))
        ]

        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": str(chunk_index),
            }
            for chunk_index in range(len(chunks))
        ]

        self.vector_store.add(
            ids=vector_ids,
            embeddings=embeddings,
            texts=chunks,
            metadatas=metadatas,
        )

        return len(chunks)
