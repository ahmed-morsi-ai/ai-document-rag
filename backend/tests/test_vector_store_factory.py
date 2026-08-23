import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.vector_store.base import VectorStore
from app.services.vector_store.chroma import ChromaVectorStore
from app.services.vector_store_factory import get_vector_store


class VectorStoreFactoryTests(unittest.TestCase):
    def test_factory_returns_vector_store_abstraction(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "app.services.vector_store_factory.settings.VECTOR_STORE_DIR",
                Path(temp_dir),
            ):
                store = get_vector_store()

        self.assertIsInstance(store, VectorStore)
        self.assertIsInstance(store, ChromaVectorStore)

    def test_factory_reuses_configured_vector_store_settings(self):
        with patch(
            "app.services.vector_store_factory.ChromaVectorStore"
        ) as chroma_store:
            get_vector_store()

        chroma_store.assert_called_once_with(
            persist_directory=(
                __import__(
                    "app.services.vector_store_factory",
                    fromlist=["settings"],
                ).settings.VECTOR_STORE_DIR
            ),
            collection_name=(
                __import__(
                    "app.services.vector_store_factory",
                    fromlist=["settings"],
                ).settings.VECTOR_COLLECTION_NAME
            ),
        )

    def test_retrieval_and_indexing_factories_use_shared_vector_store_factory(self):
        with patch(
            "app.services.retrieval_factory.get_vector_store"
        ) as retrieval_store, patch(
            "app.services.document_indexing_factory.get_vector_store"
        ) as indexing_store:
            fake_store = object()
            retrieval_store.return_value = fake_store
            indexing_store.return_value = fake_store

            with patch(
                "app.services.retrieval_factory.SentenceTransformerEmbeddingProvider"
            ) as retrieval_embedding, patch(
                "app.services.document_indexing_factory.SentenceTransformerEmbeddingProvider"
            ) as indexing_embedding:
                retrieval_embedding.return_value = object()
                indexing_embedding.return_value = object()

                from app.services.retrieval_factory import get_retriever
                from app.services.document_indexing_factory import (
                    get_document_indexer,
                )

                retriever = get_retriever()
                indexer = get_document_indexer()

        self.assertIs(retriever.vector_store, fake_store)
        self.assertIs(indexer.vector_store, fake_store)
        retrieval_store.assert_called_once_with()
        indexing_store.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
