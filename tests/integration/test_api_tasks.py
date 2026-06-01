"""Integration tests for tasks API."""

import pytest


async def _create_project(client, headers):
    resp = await client.post(
        "/api/v1/projects", json={"name": "Task Test Proj"}, headers=headers
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_task(client, auth_headers):
    project_id = await _create_project(client, auth_headers)
    response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Test Task", "task_type": "research"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_tasks(client, auth_headers):
    project_id = await _create_project(client, auth_headers)
    await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Task 1", "task_type": "research"},
        headers=auth_headers,
    )
    response = await client.get(
        f"/api/v1/projects/{project_id}/tasks", headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_get_task(client, auth_headers):
    project_id = await _create_project(client, auth_headers)
    create = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Get Task", "task_type": "analysis"},
        headers=auth_headers,
    )
    task_id = create.json()["id"]
    response = await client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Get Task"
