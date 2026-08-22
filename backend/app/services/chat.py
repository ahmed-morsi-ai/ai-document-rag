from dataclasses import dataclass

from app.services.rag import RagService


@dataclass(frozen=True)
class ChatResponse:
    query: str
    answer: str


class ChatService:
    """Application-level chat orchestration over the RAG service."""

    def __init__(
        self,
        rag_service: RagService,
    ) -> None:
        self.rag_service = rag_service

    def chat(
        self,
        query: str,
        top_k: int = 5,
    ) -> ChatResponse:
        response = self.rag_service.generate_answer(
            query=query,
            top_k=top_k,
        )

        return ChatResponse(
            query=query,
            answer=response.answer,
        )
