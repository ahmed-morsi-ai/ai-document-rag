from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConversationHistoryConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class ConversationHistoryMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    sequence_number: int
    created_at: datetime


class ConversationHistoryResponse(BaseModel):
    conversation: ConversationHistoryConversationResponse
    messages: list[ConversationHistoryMessageResponse]


class ConversationListResponse(BaseModel):
    conversations: list[ConversationHistoryConversationResponse]
