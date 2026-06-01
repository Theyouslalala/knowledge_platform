"""Top-level API router aggregation."""

from fastapi import APIRouter

from .auth import router as auth_router
from .conversation_search import router as search_router
from .conversations import router as conversations_router
from .data_export import router as export_router
from .documents import router as documents_router
from .projects import router as projects_router
from .tasks import router as tasks_router
from .traces import router as traces_router
from .users import router as users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(projects_router)
api_router.include_router(tasks_router)
api_router.include_router(documents_router)
api_router.include_router(conversations_router)
api_router.include_router(export_router)
api_router.include_router(search_router)
api_router.include_router(traces_router)
