"""Тести для CRUD ендпоінтів профілів: /profiles"""
import pytest
from httpx import AsyncClient


async def create_user(client: AsyncClient, email: str = "user@test.com") -> int:
    r = await client.post("/users/", json={"name": "Test User", "email": email})
    return r.json()["id"]


async def test_create_profile(client: AsyncClient):
    user_id = await create_user(client)
    response = await client.post("/profiles/", json={
        "user_id": user_id, "bio": "Розробник", "phone": "+380671234567",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user_id
    assert data["bio"] == "Розробник"


async def test_get_profile_by_user(client: AsyncClient):
    user_id = await create_user(client)
    await client.post("/profiles/", json={"user_id": user_id, "bio": "Bio text"})
    response = await client.get(f"/profiles/user/{user_id}")
    assert response.status_code == 200
    assert response.json()["user_id"] == user_id


async def test_get_profile_not_found(client: AsyncClient):
    response = await client.get("/profiles/user/99999")
    assert response.status_code == 404


async def test_update_profile(client: AsyncClient):
    user_id = await create_user(client)
    created = await client.post("/profiles/", json={"user_id": user_id, "bio": "Old bio"})
    profile_id = created.json()["id"]
    response = await client.put(f"/profiles/{profile_id}", json={"bio": "New bio"})
    assert response.status_code == 200
    assert response.json()["bio"] == "New bio"


async def test_delete_profile(client: AsyncClient):
    user_id = await create_user(client)
    created = await client.post("/profiles/", json={"user_id": user_id})
    profile_id = created.json()["id"]
    response = await client.delete(f"/profiles/{profile_id}")
    assert response.status_code == 204
    check = await client.get(f"/profiles/{profile_id}")
    assert check.status_code == 404


async def test_create_duplicate_profile(client: AsyncClient):
    """Один юзер — один профіль (one-to-one)."""
    user_id = await create_user(client)
    await client.post("/profiles/", json={"user_id": user_id})
    response = await client.post("/profiles/", json={"user_id": user_id})
    assert response.status_code == 400
