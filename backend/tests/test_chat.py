import unittest

from app.services.chat import ChatResponse, ChatService


class FakeRagService:
    def __init__(self, answer="generated answer"):
        self.answer = answer
        self.calls = []

    def generate_answer(self, query, top_k=5):
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
            }
        )

        class FakeRagResponse:
            def __init__(self, answer):
                self.answer = answer

        return FakeRagResponse(self.answer)


class ChatServiceTests(unittest.TestCase):
    def setUp(self):
        self.rag_service = FakeRagService(
            answer="the answer",
        )
        self.chat_service = ChatService(
            self.rag_service,
        )

    def test_normal_query_returns_provider_independent_chat_response(self):
        result = self.chat_service.chat(
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            result,
            ChatResponse(
                query="hello",
                answer="the answer",
            ),
        )
        self.assertIsInstance(
            result,
            ChatResponse,
        )

    def test_calls_rag_service_exactly_once(self):
        self.chat_service.chat(
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            len(self.rag_service.calls),
            1,
        )

    def test_passes_query_unchanged_to_rag_service(self):
        query = "  preserve whitespace  "

        self.chat_service.chat(
            query=query,
            top_k=3,
        )

        self.assertEqual(
            self.rag_service.calls,
            [
                {
                    "query": query,
                    "top_k": 3,
                }
            ],
        )

    def test_preserves_answer_unchanged(self):
        answer = "Exact answer from RagService"
        rag_service = FakeRagService(answer=answer)
        service = ChatService(rag_service)

        result = service.chat("hello")

        self.assertEqual(
            result.answer,
            answer,
        )

    def test_rag_service_failure_propagates(self):
        class FailingRagService:
            def generate_answer(self, query, top_k=5):
                raise RuntimeError(
                    "rag failure"
                )

        service = ChatService(
            FailingRagService(),
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "rag failure",
        ):
            service.chat("hello")

    def test_repeated_calls_are_deterministic(self):
        first = self.chat_service.chat(
            query="hello",
            top_k=2,
        )
        second = self.chat_service.chat(
            query="hello",
            top_k=2,
        )

        self.assertEqual(
            first,
            second,
        )

    def test_top_k_defaults_to_five(self):
        self.chat_service.chat("hello")

        self.assertEqual(
            self.rag_service.calls,
            [
                {
                    "query": "hello",
                    "top_k": 5,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
