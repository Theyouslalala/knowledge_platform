"""Conversation history semantic search API."""

from fastapi import APIRouter
from sqlalchemy import select, or_

from ..models.message import Message
from ..models.conversation import Conversation
from .deps import CurrentUser, DatabaseSession

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/messages")
async def search_messages(query: str, user: CurrentUser, db: DatabaseSession, limit: int = 20):
    result = await db.execute(
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            Conversation.user_id == user.id,
            or_(
                Message.content.ilike(f"%{query}%"),
                Message.agent_name.ilike(f"%{query}%"),
            ),
        )
        .limit(limit)
    )
    messages = result.scalars().all()

    return [
        {
            "id": m.id,
            "conversation_id": m.conversation_id,
            "role": m.role,
            "agent_name": m.agent_name,
            "content": m.content[:500],
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]
