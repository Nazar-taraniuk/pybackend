from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Category]:
    result = await db.execute(select(Category).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, category_id: int) -> Category | None:
    result = await db.execute(select(Category).where(Category.id == category_id))
    return result.scalar_one_or_none()


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
