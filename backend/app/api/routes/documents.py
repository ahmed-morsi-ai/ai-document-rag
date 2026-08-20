from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.dependencies.auth import get_current_user
from app.db.models import User
from app.services.document_validation import validate_document_upload


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    validate_document_upload(file)

    return {
        "detail": "Document upload accepted",
    }