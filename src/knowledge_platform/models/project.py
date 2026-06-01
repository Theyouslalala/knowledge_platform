"""Project model."""

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Project(BaseModel):
    __tablename__ = "projects"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    user = relationship("User", back_populates="projects", lazy="raise")
    tasks = relationship("Task", back_populates="project", lazy="raise")
    documents = relationship("Document", back_populates="project", lazy="raise")
