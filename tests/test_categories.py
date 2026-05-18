"""Тести для CRUD ендпоінтів категорій: /categories"""
import pytest
from httpx import AsyncClient

CAT_PAYLOAD = {"name": "Електроніка", "description": "Гаджети та пристрої"}


async def test_get_categories_empty(client: AsyncClient):
    response = await client.get("/categories/")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_category(client: AsyncClient):
    response = await client.post("/categories/", json=CAT_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Електроніка"
    assert data["description"] == "Гаджети та пристрої"
    assert "id" in data


async def test_get_category_by_id(client: AsyncClient):
    created = await client.post("/categories/", json=CAT_PAYLOAD)
    cat_id = created.json()["id"]
    response = await client.get(f"/categories/{cat_id}")
    assert response.status_code == 200
    assert response.json()["id"] == cat_id


async def test_get_category_not_found(client: AsyncClient):
    response = await client.get("/categories/99999")
    assert response.status_code == 404


async def test_update_category(client: AsyncClient):
    created = await client.post("/categories/", json=CAT_PAYLOAD)
    cat_id = created.json()["id"]
    response = await client.put(f"/categories/{cat_id}", json={"name": "Оновлена"})
    assert response.status_code == 200
    assert response.json()["name"] == "Оновлена"


async def test_delete_category(client: AsyncClient):
    created = await client.post("/categories/", json=CAT_PAYLOAD)
    cat_id = created.json()["id"]
    response = await client.delete(f"/categories/{cat_id}")
    assert response.status_code == 204
    check = await client.get(f"/categories/{cat_id}")
    assert check.status_code == 404


async def test_delete_category_not_found(client: AsyncClient):
    response = await client.delete("/categories/99999")
    assert response.status_code == 404
