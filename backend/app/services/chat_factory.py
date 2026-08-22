from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.chat import ChatService
from app.services.chat_persistence import ChatPersistenceService
from app.services.rag_factory import get_rag_service
from app.services.retrieval_factory import get_retriever


def get_chat_persistence_service(
    db: AsyncSession = Depends(get_db),
) -> ChatPersistenceService:
    return ChatPersistenceService(
        db=db,
    )


def get_chat_service(
    db: AsyncSession = Depends(get_db),
) -> ChatService:
    return ChatService(
        rag_service=get_rag_service(
            retriever=get_retriever(),
        ),
        persistence_service=ChatPersistenceService(
            db=db,
        ),
    )
