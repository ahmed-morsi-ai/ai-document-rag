import unittest
from unittest.mock import Mock

from app.services.retrieval import RetrievalResult, Retriever
from app.services.vector_store.base import VectorQueryResult


class FakeEmbeddingProvider:
    def __init__(self):
        self.calls = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return [1.0, 0.0]


class FakeVectorStore:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def query(self, embedding, top_k=5):
        self.calls.append(
            {
                "embedding": list(embedding),
                "top_k": top_k,
            }
        )
        return list(self.results)


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.vector_results = [
            VectorQueryResult(
                id="document-1:0",
                distance=0.1,
                text="first chunk",
                metadata={
                    "document_id": "document-1",
                    "chunk_index": "0",
                    "source": "test.txt",
                },
            ),
            VectorQueryResult(
                id="document-1:1",
                distance=0.2,
                text="second chunk",
                metadata={
                    "document_id": "document-1",
                    "chunk_index": "1",
                    "source": "test.txt",
                },
            ),
        ]

        self.embedding_provider = FakeEmbeddingProvider()
        self.vector_store = FakeVectorStore(
            self.vector_results
        )
        self.retriever = Retriever(
            embedding_provider=self.embedding_provider,
            vector_store=self.vector_store,
        )

    def test_retrieves_query_embedding_once(self):
        results = self.retriever.retrieve(
            query="hello world",
            top_k=2,
        )

        self.assertEqual(
            self.embedding_provider.calls,
            ["hello world"],
        )
        self.assertEqual(len(results), 2)

    def test_passes_query_embedding_and_top_k_to_vector_store(self):
        self.retriever.retrieve(
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            self.vector_store.calls,
            [
                {
                    "embedding": [1.0, 0.0],
                    "top_k": 2,
                }
            ],
        )

    def test_preserves_result_order(self):
        results = self.retriever.retrieve(
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            [result.text for result in results],
            [
                "first chunk",
                "second chunk",
            ],
        )

    def test_maps_metadata_and_distance(self):
        results = self.retriever.retrieve(
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            results,
            [
                RetrievalResult(
                    text="first chunk",
                    document_id="document-1",
                    chunk_index=0,
                    distance=0.1,
                    metadata={
                        "document_id": "document-1",
                        "chunk_index": "0",
                        "source": "test.txt",
                    },
                ),
                RetrievalResult(
                    text="second chunk",
                    document_id="document-1",
                    chunk_index=1,
                    distance=0.2,
                    metadata={
                        "document_id": "document-1",
                        "chunk_index": "1",
                        "source": "test.txt",
                    },
                ),
            ],
        )

    def test_empty_vector_store_results_return_empty_list(self):
        retriever = Retriever(
            embedding_provider=FakeEmbeddingProvider(),
            vector_store=FakeVectorStore([]),
        )

        self.assertEqual(
            retriever.retrieve("hello"),
            [],
        )

    def test_rejects_empty_query(self):
        with self.assertRaisesRegex(
            ValueError,
            "query must not be empty",
        ):
            self.retriever.retrieve("   ")

        self.assertEqual(
            self.embedding_provider.calls,
            [],
        )
        self.assertEqual(
            self.vector_store.calls,
            [],
        )

    def test_rejects_invalid_top_k(self):
        with self.assertRaisesRegex(
            ValueError,
            "top_k must be greater than 0",
        ):
            self.retriever.retrieve(
                "hello",
                top_k=0,
            )

        self.assertEqual(
            self.embedding_provider.calls,
            [],
        )
        self.assertEqual(
            self.vector_store.calls,
            [],
        )

    def test_embedding_failure_propagates(self):
        provider = Mock()
        provider.embed.side_effect = RuntimeError(
            "embedding failure"
        )

        retriever = Retriever(
            embedding_provider=provider,
            vector_store=Mock(),
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "embedding failure",
        ):
            retriever.retrieve("hello")

    def test_vector_store_failure_propagates(self):
        provider = FakeEmbeddingProvider()
        store = Mock()
        store.query.side_effect = RuntimeError(
            "vector store failure"
        )

        retriever = Retriever(
            embedding_provider=provider,
            vector_store=store,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "vector store failure",
        ):
            retriever.retrieve("hello")

        self.assertEqual(
            provider.calls,
            ["hello"],
        )


if __name__ == "__main__":
    unittest.main()
