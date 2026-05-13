import os

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:secret@db:5432/pybackend")

engine = create_async_engine(DATABASE_URL)

app = FastAPI(
    title="PyBackend",
    description="FastAPI college project",
    version="0.1.0",
)


@app.get("/", tags=["root"])
async def root():
    """Health check endpoint."""
    return {"message": "Hello from PyBackend!"}


@app.get("/health", tags=["root"])
async def health():
    """Health status."""
    return {"status": "ok"}


@app.get("/db-check", tags=["database"])
async def db_check():
    """Перевірка підключення до PostgreSQL."""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version()"))
        version = result.scalar()
    return {"postgres_version": version}
