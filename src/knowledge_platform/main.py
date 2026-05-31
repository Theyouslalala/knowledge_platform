"""FastAPI application factory with lifespan management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .infrastructure.database import init_db
from .infrastructure.exceptions import AppError
from .infrastructure.health import router as health_router
from .infrastructure.logging import setup_logging
from .api.router import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    yield


app = FastAPI(
    title="Knowledge Platform",
    description="Knowledge-Enhanced Multi-Agent Collaboration Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["Health"])
app.include_router(api_router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=400,
        content={"error": exc.code, "message": exc.message},
    )


@app.get("/")
async def root():
    return {
        "name": "Knowledge Platform",
        "version": "0.1.0",
        "docs": "/docs",
    }
