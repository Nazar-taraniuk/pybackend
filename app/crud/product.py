from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Product]:
    result = await db.execute(select(Product).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def get_by_category(db: AsyncSession, category_id: int) -> list[Product]:
    result = await db.execute(select(Product).where(Product.category_id == category_id))
    return list(result.scalars().all())


async def create(db: AsyncSession, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update(db: AsyncSession, product_id: int, data: ProductUpdate) -> Product | None:
    product = await get_by_id(db, product_id)
    if not product:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return product


async def delete(db: AsyncSession, product_id: int) -> bool:
    product = await get_by_id(db, product_id)
    if not product:
        return False
    await db.delete(product)
    await db.commit()
    return True
