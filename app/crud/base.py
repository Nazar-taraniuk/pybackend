"""Спільні утиліти для CRUD-шару."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase


async def get_all_records(
    db: AsyncSession,
    model: type[DeclarativeBase],
    *,
    skip: int = 0,
    limit: int = 100,
) -> list:
    result = await db.execute(select(model).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_by_id_record(
    db: AsyncSession,
    model: type[DeclarativeBase],
    record_id: int,
):
    result = await db.execute(select(model).where(model.id == record_id))
    return result.scalar_one_or_none()


async def delete_record(db: AsyncSession, instance) -> None:
    await db.delete(instance)
    await db.commit()
