"""Project API endpoints."""

import asyncio

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from ..models.project import Project
from ..schemas.common import PaginatedResponse
from ..schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from .deps import CurrentUser, DatabaseSession
from .utils import get_user_resource

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(request: ProjectCreate, user: CurrentUser, db: DatabaseSession):
    project = Project(
        user_id=user.id,
        name=request.name,
        description=request.description,
    )
    db.add(project)
    await db.flush()
    return project


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    user: CurrentUser,
    db: DatabaseSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    base_filter = Project.user_id == user.id, Project.status != "archived"

    count_result, result = await asyncio.gather(
        db.execute(select(func.count()).select_from(Project).where(*base_filter)),
        db.execute(select(Project).where(*base_filter).offset(offset).limit(page_size)),
    )
    total = count_result.scalar() or 0
    items = result.scalars().all()

    return PaginatedResponse(
        items=[ProjectResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, user: CurrentUser, db: DatabaseSession):
    return await get_user_resource(db, Project, project_id, user.id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str, update: ProjectUpdate, user: CurrentUser, db: DatabaseSession
):
    project = await get_user_resource(db, Project, project_id, user.id)

    if update.name is not None:
        project.name = update.name
    if update.description is not None:
        project.description = update.description
    if update.status is not None:
        project.status = update.status

    await db.flush()
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, user: CurrentUser, db: DatabaseSession):
    project = await get_user_resource(db, Project, project_id, user.id)

    project.status = "archived"
    await db.flush()
