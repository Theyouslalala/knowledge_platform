"""Shared test fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient

from src.knowledge_platform.infrastructure.database import Base, engine
from src.knowledge_platform.main import app


@pytest.fixture(scope="session")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client):
    """Register a user and return auth headers."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "fixture@example.com",
            "username": "fixtureuser",
            "password": "fixturepass123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
