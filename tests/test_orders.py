"""Тести для замовлень: /orders"""
import pytest
from httpx import AsyncClient


async def setup_data(client: AsyncClient) -> tuple[int, int]:
    user = await client.post("/users/", json={"name": "User", "email": "u@test.com"})
    cat = await client.post("/categories/", json={"name": "Cat"})
    product = await client.post("/products/", json={
        "name": "Product", "price": "10.00", "stock": 100,
        "category_id": cat.json()["id"],
    })
    return user.json()["id"], product.json()["id"]


async def test_get_orders_empty(client: AsyncClient):
    response = await client.get("/orders/")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_order(client: AsyncClient):
    user_id, product_id = await setup_data(client)
    response = await client.post("/orders/", json={
        "user_id": user_id,
        "items": [{"product_id": product_id, "quantity": 2}],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user_id
    assert data["status"] == "pending"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2


async def test_get_order_by_id(client: AsyncClient):
    user_id, product_id = await setup_data(client)
    created = await client.post("/orders/", json={
        "user_id": user_id, "items": [{"product_id": product_id, "quantity": 1}],
    })
    order_id = created.json()["id"]
    response = await client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id


async def test_get_order_not_found(client: AsyncClient):
    response = await client.get("/orders/99999")
    assert response.status_code == 404


async def test_update_order_status(client: AsyncClient):
    user_id, product_id = await setup_data(client)
    created = await client.post("/orders/", json={
        "user_id": user_id, "items": [{"product_id": product_id, "quantity": 1}],
    })
    order_id = created.json()["id"]
    response = await client.put(f"/orders/{order_id}", json={"status": "completed"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


async def test_delete_order(client: AsyncClient):
    user_id, product_id = await setup_data(client)
    created = await client.post("/orders/", json={
        "user_id": user_id, "items": [{"product_id": product_id, "quantity": 1}],
    })
    order_id = created.json()["id"]
    response = await client.delete(f"/orders/{order_id}")
    assert response.status_code == 204
    assert (await client.get(f"/orders/{order_id}")).status_code == 404
