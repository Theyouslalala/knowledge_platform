"""Conversation history semantic search API."""

from fastapi import APIRouter
from sqlalchemy import or_, select

from ..models.conversation import Conversation
from ..models.message import Message
from .deps import CurrentUser, DatabaseSession

router = APIRouter(prefix="/search", tags=["Search"])


def _escape_like(query: str) -> str:
    """Escape special LIKE pattern characters."""
    return query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("/messages")
async def search_messages(query: str, user: CurrentUser, db: DatabaseSession, limit: int = 20):
    limit = min(limit, 100)
    escaped = _escape_like(query)
    result = await db.execute(
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            Conversation.user_id == user.id,
            or_(
                Message.content.ilike(f"%{escaped}%", escape="\\"),
                Message.agent_name.ilike(f"%{escaped}%", escape="\\"),
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
