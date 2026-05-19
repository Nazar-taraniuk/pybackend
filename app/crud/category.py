from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import get_all_records, get_by_id_record
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Category]:
    return await get_all_records(db, Category, skip=skip, limit=limit)


async def get_by_id(db: AsyncSession, category_id: int) -> Category | None:
    return await get_by_id_record(db, Category, category_id)


async def create(db: AsyncSession, data: CategoryCreate) -> Category:
    category = Category(**data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def update(db: AsyncSession, category_id: int, data: CategoryUpdate) -> Category | None:
    category = await get_by_id(db, category_id)
    if not category:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    await db.commit()
    await db.refresh(category)
    return category


async def delete(db: AsyncSession, category_id: int) -> bool:
    category = await get_by_id(db, category_id)
    if not category:
        return False
    await db.delete(category)
    await db.commit()
    return True
