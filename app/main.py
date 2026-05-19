import asyncio
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers import users, profiles, categories, products, orders, auth

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PyBackend",
    description="FastAPI college project",
    version="0.1.0",
)

# ── Prometheus: автоматичні HTTP-метрики ──────────────────────────────────────
Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
async def refresh_metrics_on_startup() -> None:
    """Оновлює кастомні метрики одразу після старту (щоб Grafana не показувала нулі)."""
    await _refresh_metrics_bg()


# Підключаємо всі роутери
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)


async def _refresh_metrics_bg() -> None:
    """Фонова задача: оновлює кастомні метрики з БД (fire-and-forget)."""
    try:
        from app.database import AsyncSessionLocal
        from app.metrics import update_all_metrics
        async with AsyncSessionLocal() as db:
            await update_all_metrics(db)
    except Exception as e:
        logger.debug("Metrics update skipped: %s", e)


# ── Middleware: тригерує оновлення метрик після кожного запиту ────────────────
@app.middleware("http")
async def trigger_metrics_refresh(request: Request, call_next):
    """
    Після кожного HTTP запиту (крім /metrics) — запускає фонове оновлення
    кастомних метрик через asyncio.ensure_future (не блокує відповідь).
    """
    response = await call_next(request)
    if not request.url.path.startswith("/metrics"):
        # Fire-and-forget: не чекаємо на завершення, не блокуємо відповідь
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.create_task(_refresh_metrics_bg())
        except RuntimeError:
            pass  # event loop вже закритий (напр. під час teardown тестів)
    return response


@app.get("/", tags=["root"])
async def root():
    return {"message": "Hello from PyBackend!"}


@app.get("/health", tags=["root"])
async def health():
    return {"status": "ok"}


@app.get("/metrics/refresh", tags=["monitoring"])
async def refresh_metrics_endpoint(background_tasks: BackgroundTasks):
    """Вручну тригерує оновлення кастомних метрик (для демонстрації)."""
    background_tasks.add_task(_refresh_metrics_bg)
    return {"status": "metrics refresh scheduled"}
