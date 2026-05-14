"""Тести для CRUD ендпоінтів юзерів: GET, POST, PUT, DELETE /users"""
import pytest
from httpx import AsyncClient

USER_PAYLOAD = {"name": "Ivan Petrenko", "email": "ivan@example.com"}


async def test_get_users_empty(client: AsyncClient):
    """GET /users на порожній БД — має повернути порожній список."""
    response = await client.get("/users/")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_user(client: AsyncClient):
    """POST /users — успішне створення юзера."""
    response = await client.post("/users/", json=USER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ivan Petrenko"
    assert data["email"] == "ivan@example.com"
    assert "id" in data
    assert "created_at" in data


async def test_create_user_duplicate_email(client: AsyncClient):
    """POST /users з email що вже існує — має повернути 400."""
    await client.post("/users/", json=USER_PAYLOAD)
    response = await client.post("/users/", json=USER_PAYLOAD)
    assert response.status_code == 400


async def test_create_user_invalid_email(client: AsyncClient):
    """POST /users з невалідним email — має повернути 422."""
    response = await client.post("/users/", json={"name": "Test", "email": "bad-email"})
    assert response.status_code == 422


async def test_get_user_by_id(client: AsyncClient):
    """GET /users/{id} — повертає юзера по ID."""
    created = await client.post("/users/", json=USER_PAYLOAD)
    user_id = created.json()["id"]
    response = await client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["id"] == user_id


async def test_get_user_not_found(client: AsyncClient):
    """GET /users/99999 — повертає 404."""
    response = await client.get("/users/99999")
    assert response.status_code == 404


async def test_get_all_users(client: AsyncClient):
    """GET /users — повертає всіх юзерів."""
    await client.post("/users/", json={"name": "User 1", "email": "u1@example.com"})
    await client.post("/users/", json={"name": "User 2", "email": "u2@example.com"})
    response = await client.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_update_user(client: AsyncClient):
    """PUT /users/{id} — оновлення імені юзера."""
    created = await client.post("/users/", json=USER_PAYLOAD)
    user_id = created.json()["id"]
    response = await client.put(f"/users/{user_id}", json={"name": "Updated Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    assert response.json()["email"] == "ivan@example.com"  # email не змінився


async def test_update_user_not_found(client: AsyncClient):
    """PUT /users/99999 — повертає 404."""
    response = await client.put("/users/99999", json={"name": "X"})
    assert response.status_code == 404


async def test_delete_user(client: AsyncClient):
    """DELETE /users/{id} — видалення юзера."""
    created = await client.post("/users/", json=USER_PAYLOAD)
    user_id = created.json()["id"]
    response = await client.delete(f"/users/{user_id}")
    assert response.status_code == 204
    # Перевіряємо що дійсно видалено
    check = await client.get(f"/users/{user_id}")
    assert check.status_code == 404


async def test_delete_user_not_found(client: AsyncClient):
    """DELETE /users/99999 — повертає 404."""
    response = await client.delete("/users/99999")
    assert response.status_code == 404
