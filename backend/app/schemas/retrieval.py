from pydantic import BaseModel, Field, field_validator


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, gt=0)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be empty")

        return value


class RetrievalResultResponse(BaseModel):
    text: str
    document_id: str
    chunk_index: int
    distance: float
    metadata: dict[str, str]


class RetrievalResponse(BaseModel):
    results: list[RetrievalResultResponse]
