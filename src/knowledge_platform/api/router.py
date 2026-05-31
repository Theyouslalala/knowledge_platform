"""Top-level API router aggregation."""

from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# Routers will be added as they are implemented:
# api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
# api_router.include_router(users_router, prefix="/users", tags=["Users"])
# api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
# api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
# api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
# api_router.include_router(conversations_router, prefix="/conversations", tags=["Conversations"])
# api_router.include_router(tools_router, prefix="/tools", tags=["Tools"])
