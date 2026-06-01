"""Conversation and message API endpoints."""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from ..models.conversation import Conversation
from ..models.message import Message
from ..models.task import Task
from ..schemas.conversation import ConversationCreate, ConversationResponse
from ..schemas.message import MessageCreate, MessageResponse
from .deps import CurrentUser, DatabaseSession
from .utils import get_user_resource

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post(
    "/tasks/{task_id}/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    task_id: str, request: ConversationCreate, user: CurrentUser, db: DatabaseSession
):
    task = await get_user_resource(db, Task, task_id, user.id)
    conversation = Conversation(
        task_id=task.id,
        user_id=user.id,
        title=request.title,
        conversation_type=request.conversation_type,
    )
    db.add(conversation)
    await db.flush()
    return conversation


@router.get("/tasks/{task_id}/conversations", response_model=list[ConversationResponse])
async def list_conversations(task_id: str, user: CurrentUser, db: DatabaseSession):
    await get_user_resource(db, Task, task_id, user.id)
    result = await db.execute(
        select(Conversation).where(
            Conversation.task_id == task_id, Conversation.user_id == user.id
        )
    )
    return result.scalars().all()


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, user: CurrentUser, db: DatabaseSession):
    return await get_user_resource(db, Conversation, conversation_id, user.id)


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    conversation_id: str, request: MessageCreate, user: CurrentUser, db: DatabaseSession
):
    await get_user_resource(db, Conversation, conversation_id, user.id)
    message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.content,
        message_type=request.message_type,
    )
    db.add(message)
    await db.flush()
    return message


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: str,
    user: CurrentUser,
    db: DatabaseSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    await get_user_resource(db, Conversation, conversation_id, user.id)
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()
