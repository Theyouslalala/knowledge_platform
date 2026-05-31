"""Document API endpoints."""

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from sqlalchemy import select

from ..config import get_settings
from ..models.document import Document
from ..models.project import Project
from ..schemas.document import DocumentResponse
from .deps import CurrentUser, DatabaseSession

router = APIRouter(prefix="/documents", tags=["Documents"])
settings = get_settings()


@router.post("/projects/{project_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(project_id: str, file: UploadFile = File(...), user: CurrentUser = None, db: DatabaseSession = None):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    upload_dir = Path(settings.upload_dir) / project_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    suffix = Path(file.filename).suffix.lower().lstrip(".")
    doc = Document(
        project_id=project_id,
        user_id=user.id,
        filename=file.filename,
        file_path=str(file_path),
        file_type=suffix,
        file_size_bytes=file_path.stat().st_size,
        status="pending",
    )
    db.add(doc)
    await db.flush()
    return doc


@router.get("/projects/{project_id}/documents", response_model=list[DocumentResponse])
async def list_documents(project_id: str, user: CurrentUser, db: DatabaseSession):
    result = await db.execute(
        select(Document).where(Document.project_id == project_id)
    )
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, user: CurrentUser, db: DatabaseSession):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, user: CurrentUser, db: DatabaseSession):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink()

    await db.delete(doc)
    await db.flush()
