"""Base SQLAlchemy model with common columns."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, event, func
from sqlalchemy.orm import Mapped, mapped_column

from ..infrastructure.database import Base


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


@event.listens_for(BaseModel, "before_update")
def _set_updated_at(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)
