from app.services.chat import ChatService
from app.services.rag_factory import get_rag_service
from app.services.retrieval_factory import get_retriever


def get_chat_service() -> ChatService:
    return ChatService(
        rag_service=get_rag_service(
            retriever=get_retriever(),
        ),
    )
