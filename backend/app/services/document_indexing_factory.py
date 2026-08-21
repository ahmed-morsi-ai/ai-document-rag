from app.core.config import settings
from app.services.document_indexing import DocumentIndexer
from app.services.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)
from app.services.vector_store.chroma import ChromaVectorStore


def get_document_indexer() -> DocumentIndexer:
    return DocumentIndexer(
        embedding_provider=SentenceTransformerEmbeddingProvider(
            settings.EMBEDDING_MODEL,
        ),
        vector_store=ChromaVectorStore(
            persist_directory=settings.VECTOR_STORE_DIR,
            collection_name=settings.VECTOR_COLLECTION_NAME,
        ),
    )
