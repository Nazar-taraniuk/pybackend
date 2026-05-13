from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Async engine
engine = create_async_engine(settings.database_url, echo=False)

# Фабрика сесій
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Базовий клас для всіх моделей."""
    pass


async def get_db() -> AsyncSession:
    """Dependency для FastAPI — повертає сесію БД."""
    async with AsyncSessionLocal() as session:
        yield session
