"""Data export API endpoints."""

import csv
import io
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from ..models.conversation import Conversation
from ..models.message import Message
from ..models.task import Task
from .deps import CurrentUser, DatabaseSession

router = APIRouter(prefix="/export", tags=["Export"])

MAX_EXPORT_LIMIT = 10000


@router.get("/tasks/json")
async def export_tasks_json(user: CurrentUser, db: DatabaseSession, limit: int = MAX_EXPORT_LIMIT):
    limit = min(limit, MAX_EXPORT_LIMIT)
    result = await db.execute(select(Task).where(Task.user_id == user.id).limit(limit))
    tasks = result.scalars().all()

    data = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "task_type": t.task_type,
            "status": t.status,
            "result": t.result,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tasks
    ]

    return StreamingResponse(
        io.BytesIO(json.dumps(data, indent=2, ensure_ascii=False).encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=tasks.json"},
    )


@router.get("/tasks/csv")
async def export_tasks_csv(user: CurrentUser, db: DatabaseSession, limit: int = MAX_EXPORT_LIMIT):
    limit = min(limit, MAX_EXPORT_LIMIT)
    result = await db.execute(select(Task).where(Task.user_id == user.id).limit(limit))
    tasks = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "title", "type", "status", "created_at"])

    for t in tasks:
        writer.writerow([t.id, t.title, t.task_type, t.status, t.created_at])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tasks.csv"},
    )


@router.get("/conversations/{conversation_id}/json")
async def export_conversation_json(conversation_id: str, user: CurrentUser, db: DatabaseSession):
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conv = conv_result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).limit(MAX_EXPORT_LIMIT)
    )
    messages = result.scalars().all()

    data = [
        {
            "role": m.role,
            "agent_name": m.agent_name,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]

    return StreamingResponse(
        io.BytesIO(json.dumps(data, indent=2, ensure_ascii=False).encode()),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=conversation_{conversation_id}.json"
        },
    )
