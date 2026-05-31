"""Task API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, status
from sqlalchemy import select

from ..infrastructure.database import async_session_factory
from ..models.project import Project
from ..models.task import Task
from ..schemas.task import TaskCreate, TaskResponse
from .deps import CurrentUser, DatabaseSession
from .utils import get_user_resource

router = APIRouter(prefix="/tasks", tags=["Tasks"])

_orchestrator = None


def _get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from ..core.agents.orchestrator import AgentOrchestrator

        _orchestrator = AgentOrchestrator()
    return _orchestrator


async def _execute_task_background(task_id: str):
    """Uses a separate DB session since the request session is closed."""
    task = None
    async with async_session_factory() as db:
        try:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if task is None:
                return

            orchestrator = _get_orchestrator()
            state = await orchestrator.run(task_id=task.id, query=task.title)

            task.result = state.get("final_output", "")
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            await db.commit()
        except Exception as e:
            if task is not None:
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.now(timezone.utc)
                await db.commit()


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(project_id: str, request: TaskCreate, user: CurrentUser, db: DatabaseSession):
    await get_user_resource(db, Project, project_id, user.id, resource_name="Project")

    task = Task(
        project_id=project_id,
        user_id=user.id,
        title=request.title,
        description=request.description,
        task_type=request.task_type,
        priority=request.priority,
        agent_config=request.agent_config,
    )
    db.add(task)
    await db.flush()
    return task


@router.get("/projects/{project_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(project_id: str, user: CurrentUser, db: DatabaseSession):
    result = await db.execute(
        select(Task).where(Task.project_id == project_id, Task.user_id == user.id)
    )
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, user: CurrentUser, db: DatabaseSession):
    return await get_user_resource(db, Task, task_id, user.id)


@router.post("/{task_id}/execute", response_model=TaskResponse)
async def execute_task(
    task_id: str, user: CurrentUser, db: DatabaseSession, background_tasks: BackgroundTasks
):
    task = await get_user_resource(db, Task, task_id, user.id)

    task.status = "executing"
    task.started_at = datetime.now(timezone.utc)
    await db.flush()

    background_tasks.add_task(_execute_task_background, task.id)
    return task
