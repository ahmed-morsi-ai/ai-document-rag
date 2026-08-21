from pathlib import Path

import chromadb

from app.services.vector_store.base import (
    VectorQueryResult,
    VectorStore,
)


class ChromaVectorStore(VectorStore):
    """Local persistent Chroma implementation of the vector-store contract."""

    def __init__(
        self,
        persist_directory: Path,
        collection_name: str,
    ):
        self.client = chromadb.PersistentClient(
            path=str(persist_directory),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
        )

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict[str, str]] | None = None,
    ) -> None:
        if not ids:
            raise ValueError("ids must not be empty")

        if len(ids) != len(embeddings):
            raise ValueError(
                "ids, embeddings, and texts must have the same length"
            )

        if len(ids) != len(texts):
            raise ValueError(
                "ids, embeddings, and texts must have the same length"
            )

        if metadatas is not None and len(metadatas) != len(ids):
            raise ValueError(
                "metadatas must have the same length as ids"
            )

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    def query(
        self,
        embedding: list[float],
        top_k: int = 5,
    ) -> list[VectorQueryResult]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        return [
            VectorQueryResult(
                id=vector_id,
                distance=float(distance),
                text=document,
                metadata=metadata or {},
            )
            for vector_id, distance, document, metadata in zip(
                ids,
                distances,
                documents,
                metadatas,
            )
        ]
