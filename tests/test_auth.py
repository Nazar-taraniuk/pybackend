"""Тести для auth ендпоінтів: register, login, logout, me, my-orders"""
import pytest
from httpx import AsyncClient


# ── Register ──────────────────────────────────────────────────────────────────

async def test_register_success(client: AsyncClient):
    """Реєстрація нового юзера — має повернути 201 і дані юзера."""
    response = await client.post("/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data
    assert "password" not in data       # пароль не повертається
    assert "password_hash" not in data  # хеш теж не повертається


async def test_register_duplicate_email(client: AsyncClient):
    """Реєстрація з вже існуючим email — має повернути 400."""
    payload = {"name": "User", "email": "dup@example.com", "password": "pass123"}
    await client.post("/auth/register", json=payload)
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "вже зареєстровано" in response.json()["detail"]


async def test_register_invalid_email(client: AsyncClient):
    """Реєстрація з невалідним email — має повернути 422."""
    response = await client.post("/auth/register", json={
        "name": "User",
        "email": "not-an-email",
        "password": "pass123",
    })
    assert response.status_code == 422


async def test_register_short_password(client: AsyncClient):
    """Реєстрація з паролем менше 6 символів — має повернути 422."""
    response = await client.post("/auth/register", json={
        "name": "User",
        "email": "user@example.com",
        "password": "123",
    })
    assert response.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient):
    """Успішний вхід — має повернути 200 і JWT токен, встановити куку."""
    await client.post("/auth/register", json={
        "name": "Login User",
        "email": "login@example.com",
        "password": "password123",
    })
    response = await client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["name"] == "Login User"
    # Перевіряємо що кука встановлена
    assert "access_token" in response.cookies


async def test_login_wrong_password(client: AsyncClient):
    """Вхід з невірним паролем — має повернути 401."""
    await client.post("/auth/register", json={
        "name": "User", "email": "u@example.com", "password": "correct123",
    })
    response = await client.post("/auth/login", json={
        "email": "u@example.com",
        "password": "wrong_password",
    })
    assert response.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    """Вхід неіснуючого юзера — має повернути 401."""
    response = await client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert response.status_code == 401


# ── Protected endpoints ───────────────────────────────────────────────────────

async def test_me_authenticated(auth_client: AsyncClient):
    """GET /auth/me з валідною кукою — має повернути дані поточного юзера."""
    response = await auth_client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "auth@test.com"
    assert data["name"] == "Auth User"


async def test_me_unauthenticated(client: AsyncClient):
    """GET /auth/me без куки — має повернути 401."""
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_my_orders_authenticated(auth_client: AsyncClient):
    """GET /auth/my-orders — має повернути список замовлень (порожній на початку)."""
    response = await auth_client.get("/auth/my-orders")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_my_orders_unauthenticated(client: AsyncClient):
    """GET /auth/my-orders без куки — має повернути 401."""
    response = await client.get("/auth/my-orders")
    assert response.status_code == 401


async def test_logout(auth_client: AsyncClient):
    """POST /auth/logout — має очистити куку."""
    response = await auth_client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
    # Після logout /me повинен повернути 401
    response = await auth_client.get("/auth/me")
    assert response.status_code == 401
