from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import get_all_records, get_by_id_record
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
    return await get_all_records(db, User, skip=skip, limit=limit)


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await get_by_id_record(db, User, user_id)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, data: UserCreate) -> User:
    user = User(**data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_with_password(
    db: AsyncSession,
    *,
    name: str,
    email: str,
    password_hash: str,
) -> User:
    """Створює користувача з bcrypt-хешем пароля (реєстрація через /auth)."""
    user = User(name=name, email=email, password_hash=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update(db: AsyncSession, user_id: int, data: UserUpdate) -> User | None:
    user = await get_by_id(db, user_id)
    if not user:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


async def delete(db: AsyncSession, user_id: int) -> bool:
    user = await get_by_id(db, user_id)
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True
