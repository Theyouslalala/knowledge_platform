"""Document schemas."""

from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    chunk_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    content: str
    token_count: int | None

    model_config = {"from_attributes": True}
