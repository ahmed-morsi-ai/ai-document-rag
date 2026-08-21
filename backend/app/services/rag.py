from dataclasses import dataclass

from app.services.llm.base import LLMProvider
from app.services.retrieval import RetrievalResult, Retriever


@dataclass(frozen=True)
class RagContext:
    query: str
    context: str
    sources: list[RetrievalResult]


@dataclass(frozen=True)
class RagResponse:
    query: str
    answer: str
    context: RagContext


class RagService:
    """Build RAG context and optionally generate an answer."""

    def __init__(
        self,
        retriever: Retriever,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.retriever = retriever
        self.llm_provider = llm_provider

    def build_context(
        self,
        query: str,
        top_k: int = 5,
    ) -> RagContext:
        results = self.retriever.retrieve(
            query=query,
            top_k=top_k,
        )

        context = "\n\n".join(
            f"[Source {index}]\n{result.text}"
            for index, result in enumerate(results, start=1)
        )

        return RagContext(
            query=query,
            context=context,
            sources=list(results),
        )

    def generate_answer(
        self,
        query: str,
        top_k: int = 5,
    ) -> RagResponse:
        if self.llm_provider is None:
            raise ValueError("LLM provider is required")

        context = self.build_context(
            query=query,
            top_k=top_k,
        )

        prompt = (
            f"Question:\n{query}\n\n"
            f"Context:\n{context.context}"
        )

        answer = self.llm_provider.generate(prompt)

        return RagResponse(
            query=query,
            answer=answer,
            context=context,
        )
