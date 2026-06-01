"""Message model."""

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Message(BaseModel):
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    tool_calls: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parent_message_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("messages.id"), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    conversation = relationship("Conversation", back_populates="messages", lazy="raise")
