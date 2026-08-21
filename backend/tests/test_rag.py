import unittest
from unittest.mock import Mock

from app.services.llm import LLMProvider
from app.services.rag import RagContext, RagResponse, RagService
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


class FakeLLMProvider(LLMProvider):
    """Deterministic test-only LLM provider."""

    def __init__(self):
        self.calls = []

    def _generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        return f"ANSWER: {prompt}"


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

        self.assertEqual(result.sources, self.results)
        self.assertEqual(result.sources[0].distance, 0.1)
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

    def test_repeated_build_context_calls_are_deterministic(self):
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
        self.assertEqual(result.sources, self.results)

    def test_generate_answer_calls_retriever_once(self):
        llm = FakeLLMProvider()
        service = RagService(
            self.retriever,
            llm_provider=llm,
        )

        result = service.generate_answer(
            query="hello",
            top_k=2,
        )

        self.assertEqual(len(self.retriever.calls), 1)
        self.assertEqual(
            self.retriever.calls[0],
            {
                "query": "hello",
                "top_k": 2,
            },
        )
        self.assertEqual(len(llm.calls), 1)
        self.assertIsInstance(result, RagResponse)

    def test_generate_answer_reuses_context_assembly(self):
        llm = FakeLLMProvider()
        service = RagService(
            self.retriever,
            llm_provider=llm,
        )

        result = service.generate_answer(
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            result.context.context,
            "[Source 1]\n"
            "first chunk\n\n"
            "[Source 2]\n"
            "second chunk",
        )
        self.assertEqual(
            result.context.sources,
            self.results,
        )

    def test_generate_answer_prompt_contains_query_and_context(self):
        llm = FakeLLMProvider()
        service = RagService(
            self.retriever,
            llm_provider=llm,
        )

        service.generate_answer(
            query="what is this?",
            top_k=2,
        )

        self.assertEqual(
            llm.calls,
            [
                "Question:\n"
                "what is this?\n\n"
                "Context:\n"
                "[Source 1]\n"
                "first chunk\n\n"
                "[Source 2]\n"
                "second chunk"
            ],
        )

    def test_generate_answer_prompt_is_deterministic(self):
        llm = FakeLLMProvider()
        service = RagService(
            self.retriever,
            llm_provider=llm,
        )

        first = service.generate_answer(
            query="hello",
            top_k=2,
        )
        second = service.generate_answer(
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            first,
            RagResponse(
                query="hello",
                answer=(
                    "ANSWER: Question:\n"
                    "hello\n\n"
                    "Context:\n"
                    "[Source 1]\n"
                    "first chunk\n\n"
                    "[Source 2]\n"
                    "second chunk"
                ),
                context=first.context,
            ),
        )
        self.assertEqual(first, second)

    def test_generate_answer_returns_exact_provider_answer(self):
        llm = FakeLLMProvider()
        service = RagService(
            self.retriever,
            llm_provider=llm,
        )

        result = service.generate_answer("hello")

        self.assertEqual(
            result.answer,
            llm.calls[0].replace(
                "Question:\nhello\n\nContext:\n",
                "ANSWER: Question:\nhello\n\nContext:\n",
            ),
        )

    def test_generate_answer_preserves_query(self):
        llm = FakeLLMProvider()
        service = RagService(
            self.retriever,
            llm_provider=llm,
        )

        result = service.generate_answer(
            query="hello",
            top_k=2,
        )

        self.assertEqual(result.query, "hello")

    def test_generate_answer_with_empty_retrieval_still_calls_llm(
        self,
    ):
        retriever = FakeRetriever([])
        llm = FakeLLMProvider()
        service = RagService(
            retriever,
            llm_provider=llm,
        )

        result = service.generate_answer("missing")

        self.assertEqual(
            result.context,
            RagContext(
                query="missing",
                context="",
                sources=[],
            ),
        )
        self.assertEqual(
            llm.calls,
            [
                "Question:\n"
                "missing\n\n"
                "Context:\n"
            ],
        )

    def test_generate_answer_requires_llm_provider(self):
        with self.assertRaisesRegex(
            ValueError,
            "LLM provider is required",
        ):
            self.service.generate_answer("hello")

    def test_llm_failure_propagates(self):
        llm = Mock(spec=LLMProvider)
        llm.generate.side_effect = RuntimeError(
            "generation failure"
        )

        service = RagService(
            self.retriever,
            llm_provider=llm,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "generation failure",
        ):
            service.generate_answer("hello")

        llm.generate.assert_called_once()

    def test_repeated_generation_with_deterministic_fakes_is_identical(
        self,
    ):
        first_llm = FakeLLMProvider()
        second_llm = FakeLLMProvider()

        first_service = RagService(
            FakeRetriever(self.results),
            llm_provider=first_llm,
        )
        second_service = RagService(
            FakeRetriever(self.results),
            llm_provider=second_llm,
        )

        first = first_service.generate_answer(
            "hello",
            top_k=2,
        )
        second = second_service.generate_answer(
            "hello",
            top_k=2,
        )

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
