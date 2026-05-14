"""Тести для CRUD ендпоінтів товарів: /products"""
import pytest
from httpx import AsyncClient


async def create_category(client: AsyncClient) -> int:
    """Хелпер: створює категорію і повертає її id."""
    r = await client.post("/categories/", json={"name": "Test Cat"})
    return r.json()["id"]


async def test_create_product(client: AsyncClient):
    """POST /products — успішне створення товару."""
    cat_id = await create_category(client)
    response = await client.post("/products/", json={
        "name": "Ноутбук", "price": "999.99", "stock": 5, "category_id": cat_id,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ноутбук"
    assert float(data["price"]) == 999.99
    assert data["category_id"] == cat_id


async def test_get_products_empty(client: AsyncClient):
    response = await client.get("/products/")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_product_by_id(client: AsyncClient):
    cat_id = await create_category(client)
    created = await client.post("/products/", json={
        "name": "Phone", "price": "499.99", "stock": 10, "category_id": cat_id,
    })
    product_id = created.json()["id"]
    response = await client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["id"] == product_id


async def test_get_product_not_found(client: AsyncClient):
    response = await client.get("/products/99999")
    assert response.status_code == 404


async def test_update_product(client: AsyncClient):
    cat_id = await create_category(client)
    created = await client.post("/products/", json={
        "name": "Old Name", "price": "100.00", "stock": 1, "category_id": cat_id,
    })
    product_id = created.json()["id"]
    response = await client.put(f"/products/{product_id}", json={"name": "New Name", "stock": 50})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    assert response.json()["stock"] == 50


async def test_delete_product(client: AsyncClient):
    cat_id = await create_category(client)
    created = await client.post("/products/", json={
        "name": "Delete Me", "price": "1.00", "stock": 0, "category_id": cat_id,
    })
    product_id = created.json()["id"]
    response = await client.delete(f"/products/{product_id}")
    assert response.status_code == 204
    check = await client.get(f"/products/{product_id}")
    assert check.status_code == 404


async def test_get_products_by_category(client: AsyncClient):
    """GET /products/category/{id} — товари певної категорії."""
    cat_id = await create_category(client)
    await client.post("/products/", json={"name": "P1", "price": "10.00", "stock": 1, "category_id": cat_id})
    await client.post("/products/", json={"name": "P2", "price": "20.00", "stock": 2, "category_id": cat_id})
    response = await client.get(f"/products/category/{cat_id}")
    assert response.status_code == 200
    assert len(response.json()) == 2
