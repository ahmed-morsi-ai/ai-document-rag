from pathlib import PurePath

from fastapi import HTTPException, UploadFile, status


SUPPORTED_DOCUMENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ),
    ".txt": "text/plain",
}


def validate_document_upload(file: UploadFile) -> None:
    filename = file.filename

    if filename is None or not filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    if len(filename) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is too long",
        )

    if "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must not contain path separators",
        )

    if any(character in filename for character in ("\x00", "\r", "\n")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename contains invalid characters",
        )

    suffix = PurePath(filename).suffix.lower()

    if suffix not in SUPPORTED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported document type",
        )

    expected_mime_type = SUPPORTED_DOCUMENT_TYPES[suffix]

    if file.content_type != expected_mime_type:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Filename extension does not match content type",
        )