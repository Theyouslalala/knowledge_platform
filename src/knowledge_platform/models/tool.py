"""Tool model."""

from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class Tool(BaseModel):
    __tablename__ = "tools"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tool_type: Mapped[str] = mapped_column(String(30), nullable=False)
    parameters_schema: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
