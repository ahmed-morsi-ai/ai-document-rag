from app.core.config import settings
from app.services.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)
from app.services.retrieval import Retriever
from app.services.vector_store_factory import get_vector_store


def get_retriever() -> Retriever:
    return Retriever(
        embedding_provider=SentenceTransformerEmbeddingProvider(
            settings.EMBEDDING_MODEL,
        ),
        vector_store=get_vector_store(),
    )
