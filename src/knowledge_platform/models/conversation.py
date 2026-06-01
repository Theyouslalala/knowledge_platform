"""Conversation model."""

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Conversation(BaseModel):
    __tablename__ = "conversations"

    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tasks.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    conversation_type: Mapped[str] = mapped_column(String(20), nullable=False, default="user_chat")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    task = relationship("Task", back_populates="conversations", lazy="raise")
    messages = relationship("Message", back_populates="conversation", lazy="raise")
