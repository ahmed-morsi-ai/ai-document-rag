from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, gt=0)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be empty")

        return value


class ChatResponse(BaseModel):
    query: str
    answer: str
