"""Task API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..models.task import Task
from ..schemas.task import TaskCreate, TaskResponse, TaskUpdate
from .deps import CurrentUser, DatabaseSession
from ..models.project import Project

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(project_id: str, request: TaskCreate, user: CurrentUser, db: DatabaseSession):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

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
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/execute", response_model=TaskResponse)
async def execute_task(task_id: str, user: CurrentUser, db: DatabaseSession):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "executing"
    task.started_at = datetime.now(timezone.utc)
    await db.flush()

    try:
        from ..core.agents.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        state = await orchestrator.run(task_id=task.id, query=task.title)

        task.result = state.get("final_output", "")
        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)
    except Exception as e:
        task.status = "failed"
        task.error_message = str(e)
        task.completed_at = datetime.now(timezone.utc)

    await db.flush()
    return task
