"""
conftest.py — конфігурація тестів.

Ключові принципи:
1. ТЕСТОВА БД (pybackend_test) — окремо від прод (pybackend)
2. Підтримка двох середовищ:
   - Локально (Docker): підключення до контейнера db, читаємо з .env
   - CI (GitHub Actions): БД вже існує як service container, пропускаємо створення
3. Dependency override: get_db підмінюється на тестову сесію
4. Після кожного тесту: TRUNCATE всіх таблиць (ізоляція)
5. Після всіх тестів: DROP TABLE
"""
import asyncio
import asyncpg
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import get_db, Base
from app.config import settings
import app.models  # noqa: F401 — реєструємо моделі в Base.metadata

# ── Тестова БД ────────────────────────────────────────────────────────────────
# У CI (GitHub Actions) DATABASE_URL вже вказує на тестову БД через env var.
# Локально — підключаємося до docker-сервісу 'db' (кредали з .env/settings).
TEST_DB_NAME = "pybackend_test"
_ci_url = os.environ.get("DATABASE_URL")  # виставляється GitHub Actions

if _ci_url:
    TEST_DATABASE_URL = _ci_url
else:
    # Будуємо URL з settings (читає з .env) — не хардкодимо паролі
    TEST_DATABASE_URL = (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{TEST_DB_NAME}"
    )

# Прапорець: чи треба створювати БД (локально — так, у CI — ні)
IS_CI = bool(_ci_url)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

# Порядок для TRUNCATE (від дочірніх до батьківських)
TRUNCATE_SQL = """
TRUNCATE TABLE order_items, orders, profiles, products, categories, users
RESTART IDENTITY CASCADE
"""


# ── Створення тестової БД ─────────────────────────────────────────────────────
async def _create_test_db() -> None:
    """Створює тестову БД локально. В CI пропускається — БД вже існує."""
    if IS_CI:
        return  # У GitHub Actions БД вже створена як service container
    conn = await asyncpg.connect(
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database="postgres",
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()


# ── Dependency override ───────────────────────────────────────────────────────
async def override_get_db() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


# ── Session fixtures ──────────────────────────────────────────────────────────
@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def setup_test_db():
    """Одноразова ініціалізація тестової БД для всієї сесії тестів."""
    await _create_test_db()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


# ── Function fixtures ─────────────────────────────────────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Очищення таблиць після кожного тесту через TRUNCATE CASCADE."""
    yield
    # Окреме з'єднання для cleanup щоб не конфліктувати з тестом
    async with test_engine.connect() as conn:
        await conn.execute(text(TRUNCATE_SQL))
        await conn.commit()


@pytest_asyncio.fixture()
async def db_session() -> AsyncSession:
    """Пряме з'єднання з тестовою БД для unit-тестів CRUD функцій."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture()
async def client() -> AsyncClient:
    """HTTP клієнт FastAPI з підміненою залежністю get_db."""
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def auth_client(client: AsyncClient) -> AsyncClient:
    """HTTP клієнт з активною авторизацією (JWT у куці)."""
    await client.post("/auth/register", json={
        "name": "Auth User", "email": "auth@test.com", "password": "password123",
    })
    await client.post("/auth/login", json={
        "email": "auth@test.com", "password": "password123",
    })
    return client
