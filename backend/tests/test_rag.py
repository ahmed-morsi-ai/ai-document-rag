import unittest
from unittest.mock import Mock

from app.services.rag import RagContext, RagService
from app.services.retrieval import RetrievalResult


class FakeRetriever:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.calls = []

    def retrieve(self, query, top_k=5):
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
            }
        )
        return list(self.results)


class RagServiceTests(unittest.TestCase):
    def setUp(self):
        self.results = [
            RetrievalResult(
                text="first chunk",
                document_id="document-1",
                chunk_index=0,
                distance=0.1,
                metadata={
                    "document_id": "document-1",
                    "chunk_index": "0",
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
                },
            ),
        ]

        self.retriever = FakeRetriever(self.results)
        self.service = RagService(self.retriever)

    def test_build_context_calls_retriever_once(self):
        result = self.service.build_context(
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            self.retriever.calls,
            [
                {
                    "query": "hello",
                    "top_k": 2,
                }
            ],
        )
        self.assertEqual(len(result.sources), 2)

    def test_preserves_query_and_result_order(self):
        result = self.service.build_context(
            query="hello",
            top_k=2,
        )

        self.assertEqual(result.query, "hello")
        self.assertEqual(
            [source.text for source in result.sources],
            [
                "first chunk",
                "second chunk",
            ],
        )

    def test_assembles_deterministic_context(self):
        result = self.service.build_context(
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            result.context,
            "[Source 1]\n"
            "first chunk\n\n"
            "[Source 2]\n"
            "second chunk",
        )

    def test_preserves_full_retrieval_results_as_sources(self):
        result = self.service.build_context(
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            result.sources,
            self.results,
        )
        self.assertEqual(
            result.sources[0].distance,
            0.1,
        )
        self.assertEqual(
            result.sources[0].metadata,
            {
                "document_id": "document-1",
                "chunk_index": "0",
            },
        )

    def test_empty_retrieval_returns_explicit_empty_context(self):
        retriever = FakeRetriever([])
        service = RagService(retriever)

        result = service.build_context("missing")

        self.assertEqual(
            result,
            RagContext(
                query="missing",
                context="",
                sources=[],
            ),
        )

    def test_retriever_errors_propagate(self):
        retriever = Mock()
        retriever.retrieve.side_effect = RuntimeError(
            "retrieval failure"
        )

        service = RagService(retriever)

        with self.assertRaisesRegex(
            RuntimeError,
            "retrieval failure",
        ):
            service.build_context("hello")

    def test_repeated_calls_are_deterministic(self):
        first = self.service.build_context(
            query="hello",
            top_k=2,
        )
        second = self.service.build_context(
            query="hello",
            top_k=2,
        )

        self.assertEqual(first, second)

    def test_does_not_call_embeddings_or_vector_store_directly(
        self,
    ):
        retriever = Mock()
        retriever.retrieve.return_value = self.results

        service = RagService(retriever)

        result = service.build_context(
            query="hello",
            top_k=2,
        )

        retriever.retrieve.assert_called_once_with(
            query="hello",
            top_k=2,
        )
        self.assertEqual(
            result.sources,
            self.results,
        )


if __name__ == "__main__":
    unittest.main()
