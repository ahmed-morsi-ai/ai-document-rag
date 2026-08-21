from app.core.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.ollama import OllamaLLMProvider
from app.services.rag import RagService
from app.services.retrieval import Retriever


def get_llm_provider() -> LLMProvider:
    return OllamaLLMProvider(
        base_url=settings.OLLAMA_BASE_URL,
        model_name=settings.OLLAMA_MODEL,
        timeout=settings.OLLAMA_TIMEOUT_SECONDS,
    )


def get_rag_service(
    retriever: Retriever,
) -> RagService:
    return RagService(
        retriever=retriever,
        llm_provider=get_llm_provider(),
    )
