"""User API endpoints."""

from fastapi import APIRouter

from ..schemas.user import UserResponse, UserUpdate
from .deps import CurrentUser, DatabaseSession

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(user: CurrentUser, update: UserUpdate, db: DatabaseSession):
    if update.full_name is not None:
        user.full_name = update.full_name
    if update.username is not None:
        user.username = update.username
    await db.flush()
    return user
