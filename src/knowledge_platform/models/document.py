"""Document and DocumentChunk models."""

from sqlalchemy import JSON, BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Document(BaseModel):
    __tablename__ = "documents"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    project = relationship("Project", back_populates="documents", lazy="raise")
    chunks = relationship("DocumentChunk", back_populates="document", lazy="raise")


class DocumentChunk(BaseModel):
    __tablename__ = "document_chunks"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    document = relationship("Document", back_populates="chunks", lazy="raise")
