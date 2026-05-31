"""Shared API utilities."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_resource(
    db: AsyncSession,
    model,
    resource_id: str,
    user_id: str,
    *,
    resource_name: str | None = None,
):
    """Fetch a resource by ID, enforcing user ownership. Raises 404 if not found."""
    name = resource_name or model.__name__
    result = await db.execute(
        select(model).where(model.id == resource_id, model.user_id == user_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return obj
