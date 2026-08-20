from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.database import get_db
from app.db.models import Document, User
from app.services.document_storage import (
    delete_document,
    store_document,
)
from app.services.document_validation import validate_document_upload


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    validate_document_upload(file)

    storage_path = await store_document(
        file,
        current_user.id,
    )

    document = Document(
        owner_id=current_user.id,
        original_filename=file.filename,
        mime_type=file.content_type,
        storage_path=storage_path,
    )

    try:
        db.add(document)
        await db.commit()
        await db.refresh(document)
    except Exception:
        await db.rollback()
        delete_document(storage_path)
        raise

    return document
