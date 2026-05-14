from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileUpdate


async def get_by_id(db: AsyncSession, profile_id: int) -> Profile | None:
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    return result.scalar_one_or_none()


async def get_by_user_id(db: AsyncSession, user_id: int) -> Profile | None:
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, data: ProfileCreate) -> Profile:
    profile = Profile(**data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update(db: AsyncSession, profile_id: int, data: ProfileUpdate) -> Profile | None:
    profile = await get_by_id(db, profile_id)
    if not profile:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile


async def delete(db: AsyncSession, profile_id: int) -> bool:
    profile = await get_by_id(db, profile_id)
    if not profile:
        return False
    await db.delete(profile)
    await db.commit()
    return True
