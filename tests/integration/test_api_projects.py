"""Integration tests for projects API."""

import pytest


@pytest.mark.asyncio
async def test_create_project(client, auth_headers):
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Test Project", "description": "A test project"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_list_projects(client, auth_headers):
    await client.post(
        "/api/v1/projects",
        json={"name": "List Test"},
        headers=auth_headers,
    )
    response = await client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_project(client, auth_headers):
    create = await client.post(
        "/api/v1/projects",
        json={"name": "Get Test"},
        headers=auth_headers,
    )
    project_id = create.json()["id"]
    response = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test"


@pytest.mark.asyncio
async def test_update_project(client, auth_headers):
    create = await client.post(
        "/api/v1/projects",
        json={"name": "Update Test"},
        headers=auth_headers,
    )
    project_id = create.json()["id"]
    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_project(client, auth_headers):
    create = await client.post(
        "/api/v1/projects",
        json={"name": "Delete Test"},
        headers=auth_headers,
    )
    project_id = create.json()["id"]
    response = await client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_project_not_found(client, auth_headers):
    response = await client.get("/api/v1/projects/nonexistent", headers=auth_headers)
    assert response.status_code == 404
