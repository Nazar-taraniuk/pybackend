"""Тести CRUD функцій напряму (без HTTP) — тестуємо шар роботи з БД."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user as user_crud
from app.crud import category as category_crud
from app.crud import product as product_crud
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.product import ProductCreate, ProductUpdate
from decimal import Decimal


# ── User CRUD ─────────────────────────────────────────────────────────────────

async def test_crud_create_user(db_session: AsyncSession):
    user = await user_crud.create(db_session, UserCreate(name="Ivan", email="ivan@test.com"))
    assert user.id is not None
    assert user.name == "Ivan"
    assert user.email == "ivan@test.com"


async def test_crud_get_user_by_id(db_session: AsyncSession):
    created = await user_crud.create(db_session, UserCreate(name="Test", email="t@test.com"))
    found = await user_crud.get_by_id(db_session, created.id)
    assert found is not None
    assert found.id == created.id


async def test_crud_get_user_by_id_not_found(db_session: AsyncSession):
    result = await user_crud.get_by_id(db_session, 99999)
    assert result is None


async def test_crud_get_user_by_email(db_session: AsyncSession):
    await user_crud.create(db_session, UserCreate(name="Email User", email="email@test.com"))
    found = await user_crud.get_by_email(db_session, "email@test.com")
    assert found is not None
    assert found.email == "email@test.com"


async def test_crud_get_user_by_email_not_found(db_session: AsyncSession):
    result = await user_crud.get_by_email(db_session, "nobody@test.com")
    assert result is None


async def test_crud_get_all_users(db_session: AsyncSession):
    await user_crud.create(db_session, UserCreate(name="U1", email="u1@test.com"))
    await user_crud.create(db_session, UserCreate(name="U2", email="u2@test.com"))
    users = await user_crud.get_all(db_session)
    assert len(users) == 2


async def test_crud_update_user(db_session: AsyncSession):
    created = await user_crud.create(db_session, UserCreate(name="Old", email="old@test.com"))
    updated = await user_crud.update(db_session, created.id, UserUpdate(name="New"))
    assert updated.name == "New"
    assert updated.email == "old@test.com"  # email не змінився


async def test_crud_update_user_not_found(db_session: AsyncSession):
    result = await user_crud.update(db_session, 99999, UserUpdate(name="X"))
    assert result is None


async def test_crud_delete_user(db_session: AsyncSession):
    created = await user_crud.create(db_session, UserCreate(name="Del", email="del@test.com"))
    result = await user_crud.delete(db_session, created.id)
    assert result is True
    assert await user_crud.get_by_id(db_session, created.id) is None


async def test_crud_delete_user_not_found(db_session: AsyncSession):
    result = await user_crud.delete(db_session, 99999)
    assert result is False


# ── Category CRUD ─────────────────────────────────────────────────────────────

async def test_crud_create_category(db_session: AsyncSession):
    cat = await category_crud.create(db_session, CategoryCreate(name="Electronics"))
    assert cat.id is not None
    assert cat.name == "Electronics"


async def test_crud_get_category_by_id(db_session: AsyncSession):
    created = await category_crud.create(db_session, CategoryCreate(name="Clothing"))
    found = await category_crud.get_by_id(db_session, created.id)
    assert found is not None


async def test_crud_update_category(db_session: AsyncSession):
    created = await category_crud.create(db_session, CategoryCreate(name="Old"))
    updated = await category_crud.update(db_session, created.id, CategoryUpdate(name="New"))
    assert updated.name == "New"


async def test_crud_delete_category(db_session: AsyncSession):
    created = await category_crud.create(db_session, CategoryCreate(name="ToDelete"))
    assert await category_crud.delete(db_session, created.id) is True
    assert await category_crud.get_by_id(db_session, created.id) is None


# ── Product CRUD ──────────────────────────────────────────────────────────────

async def test_crud_create_product(db_session: AsyncSession):
    cat = await category_crud.create(db_session, CategoryCreate(name="Cat"))
    product = await product_crud.create(db_session, ProductCreate(
        name="Laptop", price=Decimal("999.99"), stock=5, category_id=cat.id,
    ))
    assert product.id is not None
    assert product.name == "Laptop"


async def test_crud_get_products_by_category(db_session: AsyncSession):
    cat = await category_crud.create(db_session, CategoryCreate(name="CatFilter"))
    await product_crud.create(db_session, ProductCreate(name="P1", price=Decimal("1.00"), stock=1, category_id=cat.id))
    await product_crud.create(db_session, ProductCreate(name="P2", price=Decimal("2.00"), stock=2, category_id=cat.id))
    products = await product_crud.get_by_category(db_session, cat.id)
    assert len(products) == 2


async def test_crud_update_product(db_session: AsyncSession):
    cat = await category_crud.create(db_session, CategoryCreate(name="CatUpd"))
    created = await product_crud.create(db_session, ProductCreate(name="Old", price=Decimal("1.00"), stock=1, category_id=cat.id))
    updated = await product_crud.update(db_session, created.id, ProductUpdate(name="New", stock=99))
    assert updated.name == "New"
    assert updated.stock == 99


async def test_crud_delete_product(db_session: AsyncSession):
    cat = await category_crud.create(db_session, CategoryCreate(name="CatDel"))
    created = await product_crud.create(db_session, ProductCreate(name="Del", price=Decimal("1.00"), stock=1, category_id=cat.id))
    assert await product_crud.delete(db_session, created.id) is True
    assert await product_crud.get_by_id(db_session, created.id) is None
