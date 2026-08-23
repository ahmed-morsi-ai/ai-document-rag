from app.core.config import settings
from app.services.vector_store.base import VectorStore
from app.services.vector_store.chroma import ChromaVectorStore


def get_vector_store() -> VectorStore:
    return ChromaVectorStore(
        persist_directory=settings.VECTOR_STORE_DIR,
        collection_name=settings.VECTOR_COLLECTION_NAME,
    )
