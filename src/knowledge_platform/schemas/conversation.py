"""Conversation schemas."""

from datetime import datetime

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str | None = None
    conversation_type: str = "user_chat"


class ConversationResponse(BaseModel):
    id: str
    task_id: str
    title: str | None
    conversation_type: str
    created_at: datetime

    model_config = {"from_attributes": True}
