"""Document API endpoints."""

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status
from sqlalchemy import select

from ..config import get_settings
from ..infrastructure.database import async_session_factory
from ..models.document import Document
from ..models.project import Project
from ..schemas.document import DocumentResponse
from .deps import CurrentUser, DatabaseSession

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def _sanitize_filename(filename: str) -> str:
    """Remove path components and dangerous characters from filename."""
    name = Path(filename).name
    name = "".join(c for c in name if c.isalnum() or c in "._- ")
    return name.strip() or "upload"


async def _process_document_rag(document_id: str, file_path: str):
    """Background task: process document through RAG pipeline."""
    async with async_session_factory() as db:
        try:
            from ..core.rag.pipeline import RAGPipeline

            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if doc is None:
                return

            doc.status = "processing"
            await db.commit()

            pipeline = RAGPipeline()
            ingest_result = await pipeline.ingest(file_path)

            doc.chunk_count = ingest_result.get("chunks", 0)
            doc.status = "completed"
            await db.commit()
        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)[:500]
            await db.commit()


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    user: CurrentUser = None,
    db: DatabaseSession = None,
    background_tasks: BackgroundTasks = None,
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    safe_name = _sanitize_filename(file.filename)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail=f"File type {suffix} not allowed")

    settings = get_settings()
    upload_dir = Path(settings.upload_dir) / project_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{uuid.uuid4().hex}{suffix}"

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        project_id=project_id,
        user_id=user.id,
        filename=safe_name,
        file_path=str(file_path),
        file_type=suffix.lstrip("."),
        file_size_bytes=len(content),
        status="pending",
    )
    db.add(doc)
    await db.flush()

    if background_tasks:
        background_tasks.add_task(_process_document_rag, doc.id, str(file_path))

    return doc


@router.get("/projects/{project_id}/documents", response_model=list[DocumentResponse])
async def list_documents(project_id: str, user: CurrentUser, db: DatabaseSession):
    result = await db.execute(
        select(Document).where(Document.project_id == project_id, Document.user_id == user.id)
    )
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, user: CurrentUser, db: DatabaseSession):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, user: CurrentUser, db: DatabaseSession):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink()

    await db.delete(doc)
    await db.flush()
