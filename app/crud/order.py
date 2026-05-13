from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate, OrderUpdate


async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Order]:
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, order_id: int) -> Order | None:
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, data: OrderCreate) -> Order:
    order = Order(user_id=data.user_id)
    db.add(order)
    await db.flush()  # отримуємо order.id

    for item_data in data.items:
        item = OrderItem(order_id=order.id, **item_data.model_dump())
        db.add(item)

    await db.commit()
    await db.refresh(order)
    # перезавантажуємо з items
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
    )
    return result.scalar_one()


async def update(db: AsyncSession, order_id: int, data: OrderUpdate) -> Order | None:
    order = await get_by_id(db, order_id)
    if not order:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(order, key, value)
    await db.commit()
    await db.refresh(order)
    return order


async def delete(db: AsyncSession, order_id: int) -> bool:
    order = await get_by_id(db, order_id)
    if not order:
        return False
    await db.delete(order)
    await db.commit()
    return True
