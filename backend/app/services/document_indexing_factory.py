from app.core.config import settings
from app.services.document_indexing import DocumentIndexer
from app.services.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)
from app.services.vector_store_factory import get_vector_store


def get_document_indexer() -> DocumentIndexer:
    return DocumentIndexer(
        embedding_provider=SentenceTransformerEmbeddingProvider(
            settings.EMBEDDING_MODEL,
        ),
        vector_store=get_vector_store(),
    )
