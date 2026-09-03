from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document
from app.services.document_storage import delete_document
from app.services.vector_store.base import VectorStore


class DocumentDeletionService:
    """Coordinate safe deletion of one owned document."""

    def __init__(
        self,
        db: AsyncSession,
        vector_store: VectorStore,
    ) -> None:
        self.db = db
        self.vector_store = vector_store

    async def delete_owned_document(
        self,
        document: Document,
    ) -> None:
        """Commit DB deletion before removing external artifacts."""

        try:
            await self.db.delete(document)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        self.vector_store.delete_by_document_id(
            str(document.id)
        )
        delete_document(document.storage_path)
