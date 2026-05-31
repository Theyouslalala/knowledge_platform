"""Project API endpoints."""

from fastapi import APIRouter, status
from sqlalchemy import select

from ..models.project import Project
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


@router.get("", response_model=list[ProjectResponse])
async def list_projects(user: CurrentUser, db: DatabaseSession):
    result = await db.execute(
        select(Project).where(Project.user_id == user.id, Project.status != "archived")
    )
    return result.scalars().all()


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
