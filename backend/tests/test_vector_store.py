import tempfile
import unittest
from pathlib import Path

from app.services.vector_store.base import VectorStore
from app.services.vector_store.chroma import ChromaVectorStore


class VectorStoreTests(unittest.TestCase):
    def test_vector_store_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            VectorStore()

    def test_chroma_store_initializes_with_temporary_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ChromaVectorStore(
                persist_directory=Path(temp_dir),
                collection_name="test_collection",
            )

            self.assertEqual(
                store.collection.count(),
                0,
            )

    def test_add_preserves_ids_texts_and_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ChromaVectorStore(
                persist_directory=Path(temp_dir),
                collection_name="test_collection",
            )

            ids = ["chunk-1", "chunk-2"]
            embeddings = [
                [1.0, 0.0],
                [0.0, 1.0],
            ]
            texts = [
                "first chunk",
                "second chunk",
            ]
            metadatas = [
                {"source": "one"},
                {"source": "two"},
            ]

            store.add(
                ids=ids,
                embeddings=embeddings,
                texts=texts,
                metadatas=metadatas,
            )

            result = store.collection.get(
                ids=ids,
                include=["documents", "metadatas"],
            )

            self.assertEqual(
                result["ids"],
                ids,
            )
            self.assertEqual(
                result["documents"],
                texts,
            )
            self.assertEqual(
                result["metadatas"],
                metadatas,
            )

    def test_query_returns_nearest_items_with_provider_independent_results(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ChromaVectorStore(
                persist_directory=Path(temp_dir),
                collection_name="test_collection",
            )

            store.add(
                ids=["x", "y"],
                embeddings=[
                    [1.0, 0.0],
                    [0.0, 1.0],
                ],
                texts=[
                    "x text",
                    "y text",
                ],
                metadatas=[
                    {"label": "x"},
                    {"label": "y"},
                ],
            )

            results = store.query(
                embedding=[0.9, 0.0],
                top_k=1,
            )

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].id, "x")
            self.assertEqual(results[0].text, "x text")
            self.assertEqual(
                results[0].metadata,
                {"label": "x"},
            )
            self.assertIsInstance(
                results[0].distance,
                float,
            )

    def test_query_order_and_top_k_are_respected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ChromaVectorStore(
                persist_directory=Path(temp_dir),
                collection_name="test_collection",
            )

            store.add(
                ids=["x", "y", "z"],
                embeddings=[
                    [1.0, 0.0],
                    [0.8, 0.0],
                    [0.0, 1.0],
                ],
                texts=[
                    "x",
                    "y",
                    "z",
                ],
            )

            results = store.query(
                embedding=[1.0, 0.0],
                top_k=2,
            )

            self.assertEqual(
                [result.id for result in results],
                ["x", "y"],
            )
            self.assertEqual(
                [result.text for result in results],
                ["x", "y"],
            )

    def test_query_empty_store_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ChromaVectorStore(
                persist_directory=Path(temp_dir),
                collection_name="test_collection",
            )

            results = store.query(
                embedding=[1.0, 0.0],
                top_k=5,
            )

            self.assertEqual(results, [])

    def test_store_persists_across_reopening(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)

            first_store = ChromaVectorStore(
                persist_directory=path,
                collection_name="test_collection",
            )

            first_store.add(
                ids=["persisted"],
                embeddings=[[1.0, 0.0]],
                texts=["persisted text"],
                metadatas=[{"source": "test"}],
            )

            second_store = ChromaVectorStore(
                persist_directory=path,
                collection_name="test_collection",
            )

            results = second_store.query(
                embedding=[1.0, 0.0],
                top_k=1,
            )

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].id, "persisted")
            self.assertEqual(
                results[0].text,
                "persisted text",
            )
            self.assertEqual(
                results[0].metadata,
                {"source": "test"},
            )

    def test_rejects_mismatched_lengths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ChromaVectorStore(
                persist_directory=Path(temp_dir),
                collection_name="test_collection",
            )

            with self.assertRaisesRegex(
                ValueError,
                "ids, embeddings, and texts must have the same length",
            ):
                store.add(
                    ids=["one"],
                    embeddings=[
                        [1.0, 0.0],
                        [0.0, 1.0],
                    ],
                    texts=["one"],
                )

    def test_rejects_invalid_top_k(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ChromaVectorStore(
                persist_directory=Path(temp_dir),
                collection_name="test_collection",
            )

            with self.assertRaisesRegex(
                ValueError,
                "top_k must be greater than 0",
            ):
                store.query(
                    embedding=[1.0, 0.0],
                    top_k=0,
                )


if __name__ == "__main__":
    unittest.main()
