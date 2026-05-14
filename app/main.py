from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers import users, profiles, categories, products, orders, auth
from app.database import get_db
from app.metrics import update_orders_cost, update_products_count

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


# ── Middleware: оновлення кастомних метрик після кожного запиту ───────────────
@app.middleware("http")
async def update_custom_metrics(request: Request, call_next):
    response = await call_next(request)
    # Пропускаємо запити до /metrics щоб уникнути рекурсії
    if not request.url.path.startswith("/metrics"):
        try:
            async for db in get_db():
                await update_orders_cost(db)
                await update_products_count(db)
        except Exception:
            pass  # не блокуємо відповідь якщо БД недоступна
    return response


@app.get("/", tags=["root"])
async def root():
    return {"message": "Hello from PyBackend!"}


@app.get("/health", tags=["root"])
async def health():
    return {"status": "ok"}
