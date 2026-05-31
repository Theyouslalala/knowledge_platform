"""FastAPI application factory with lifespan management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.router import api_router
from .config import get_settings
from .infrastructure.database import init_db
from .infrastructure.exceptions import (
    AppError,
)
from .infrastructure.health import router as health_router
from .infrastructure.logging import setup_logging

ERROR_STATUS_MAP = {
    "NOT_FOUND": 404,
    "AUTHENTICATION_ERROR": 401,
    "AUTHORIZATION_ERROR": 403,
    "VALIDATION_ERROR": 422,
    "RATE_LIMIT_ERROR": 429,
    "LLM_PROVIDER_ERROR": 502,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Knowledge Platform",
        description="Knowledge-Enhanced Multi-Agent Collaboration Platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health_router, tags=["Health"])
    application.include_router(api_router)

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        status_code = ERROR_STATUS_MAP.get(exc.code, 400)
        return JSONResponse(
            status_code=status_code,
            content={"error": exc.code, "message": exc.message},
        )

    @application.get("/")
    async def root():
        return {
            "name": "Knowledge Platform",
            "version": "0.1.0",
            "docs": "/docs",
        }

    return application


app = create_app()
