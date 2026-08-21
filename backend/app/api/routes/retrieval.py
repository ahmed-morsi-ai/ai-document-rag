from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.db.models import User
from app.schemas.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResultResponse,
)
from app.services.retrieval_factory import get_retriever
from app.services.retrieval import Retriever


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


@router.post(
    "/search",
    response_model=RetrievalResponse,
)
async def search_documents(
    request: RetrievalRequest,
    current_user: User = Depends(get_current_user),
    retriever: Retriever = Depends(get_retriever),
):
    results = retriever.retrieve(
        query=request.query,
        top_k=request.top_k,
    )

    return RetrievalResponse(
        results=[
            RetrievalResultResponse(
                text=result.text,
                document_id=result.document_id,
                chunk_index=result.chunk_index,
                distance=result.distance,
                metadata=result.metadata,
            )
            for result in results
        ]
    )
