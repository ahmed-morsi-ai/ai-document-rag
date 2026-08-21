import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_document_rag",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from app.services.llm import LLMProvider, OllamaLLMProvider
from app.services.rag import RagService
from app.services.rag_factory import (
    get_llm_provider,
    get_rag_service,
)


class RagDependencyTests(unittest.TestCase):
    def test_get_llm_provider_returns_ollama_provider_from_settings(self):
        with patch(
            "app.services.rag_factory.settings.OLLAMA_BASE_URL",
            "http://test-ollama:11434",
        ), patch(
            "app.services.rag_factory.settings.OLLAMA_MODEL",
            "test-model",
        ), patch(
            "app.services.rag_factory.settings.OLLAMA_TIMEOUT_SECONDS",
            77.0,
        ):
            provider = get_llm_provider()

        self.assertIsInstance(provider, OllamaLLMProvider)
        self.assertIsInstance(provider, LLMProvider)
        self.assertEqual(
            provider.base_url,
            "http://test-ollama:11434",
        )
        self.assertEqual(
            provider.model_name,
            "test-model",
        )
        self.assertEqual(
            provider.timeout,
            77.0,
        )

    def test_get_rag_service_receives_existing_retriever(self):
        retriever = Mock()

        with patch(
            "app.services.rag_factory.get_llm_provider"
        ) as get_llm_provider_mock:
            llm_provider = Mock(spec=LLMProvider)
            get_llm_provider_mock.return_value = llm_provider

            service = get_rag_service(retriever)

        self.assertIsInstance(service, RagService)
        self.assertIs(service.retriever, retriever)
        self.assertIs(
            service.llm_provider,
            llm_provider,
        )
        get_llm_provider_mock.assert_called_once_with()

    def test_rag_service_contract_remains_provider_independent(self):
        retriever = Mock()
        llm_provider = Mock(spec=LLMProvider)

        service = RagService(
            retriever=retriever,
            llm_provider=llm_provider,
        )

        self.assertIs(service.retriever, retriever)
        self.assertIs(
            service.llm_provider,
            llm_provider,
        )
        self.assertNotIsInstance(
            service.llm_provider,
            OllamaLLMProvider,
        )

    def test_llm_dependency_can_be_replaced_with_fake(self):
        retriever = Mock()
        fake_provider = Mock(spec=LLMProvider)

        with patch(
            "app.services.rag_factory.get_llm_provider",
            return_value=fake_provider,
        ):
            service = get_rag_service(retriever)

        self.assertIs(
            service.llm_provider,
            fake_provider,
        )


if __name__ == "__main__":
    unittest.main()
