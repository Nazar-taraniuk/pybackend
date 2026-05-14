"""Тести для кореневих ендпоінтів: GET / та GET /health"""
import pytest
from httpx import AsyncClient


async def test_root_returns_hello(client: AsyncClient):
    """GET / повертає привітальне повідомлення."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from PyBackend!"}


async def test_health_returns_ok(client: AsyncClient):
    """GET /health повертає статус ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
