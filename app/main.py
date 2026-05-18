import asyncio
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import CollectorRegistry

from app.routers import users, profiles, categories, products, orders, auth

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PyBackend",
    description="FastAPI college project",
    version="0.1.0",
)

# ── Prometheus: автоматичні HTTP-метрики ──────────────────────────────────────
Instrumentator().instrument(app).expose(app)

# Підключаємо всі роутери
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)


async def _refresh_metrics_bg() -> None:
    """Фонова задача: оновлює кастомні метрики з БД."""
    try:
        from app.database import AsyncSessionLocal
        from app.metrics import update_all_metrics
        async with AsyncSessionLocal() as db:
            await update_all_metrics(db)
    except Exception as e:
        logger.debug("Metrics update skipped: %s", e)


@app.get("/", tags=["root"])
async def root():
    return {"message": "Hello from PyBackend!"}


@app.get("/health", tags=["root"])
async def health():
    return {"status": "ok"}


@app.get("/metrics/refresh", tags=["monitoring"])
async def refresh_metrics_endpoint(background_tasks: BackgroundTasks):
    """Вручну тригерує оновлення кастомних метрик."""
    background_tasks.add_task(_refresh_metrics_bg)
    return {"status": "metrics refresh scheduled"}
