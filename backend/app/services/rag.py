from dataclasses import dataclass

from app.services.retrieval import RetrievalResult, Retriever


@dataclass(frozen=True)
class RagContext:
    query: str
    context: str
    sources: list[RetrievalResult]


class RagService:
    """Build deterministic RAG context from retrieved document chunks."""

    def __init__(
        self,
        retriever: Retriever,
    ) -> None:
        self.retriever = retriever

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
