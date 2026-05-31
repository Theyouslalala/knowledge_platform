"""Message schemas."""

from datetime import datetime

from pydantic import BaseModel


class MessageCreate(BaseModel):
    content: str
    message_type: str = "text"


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    agent_name: str | None
    content: str
    message_type: str
    token_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
