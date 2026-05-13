"""
metrics.py — Кастомні Prometheus-метрики для PyBackend.

Метрики:
  - pybackend_total_orders_cost   : Gauge — загальна сума всіх замовлень
                                    (price * quantity для кожного order_item)
  - pybackend_products_total      : Gauge — кількість товарів у каталозі

Оновлення відбувається при кожному запиті через middleware,
зареєстрований у main.py.
"""
from prometheus_client import Gauge
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# ── Визначення метрик ─────────────────────────────────────────────────────────
ORDERS_COST_GAUGE = Gauge(
    "pybackend_total_orders_cost",
    "Total monetary value of all order items (price × quantity)",
)

PRODUCTS_COUNT_GAUGE = Gauge(
    "pybackend_products_total",
    "Total number of products in the catalogue",
)


# ── Функції оновлення ─────────────────────────────────────────────────────────
async def update_orders_cost(db: AsyncSession) -> None:
    """Рахує SUM(price * quantity) по всіх order_items і оновлює gauge."""
    from app.models.order import OrderItem
    from app.models.product import Product

    stmt = select(
        func.coalesce(
            func.sum(Product.price * OrderItem.quantity), 0
        )
    ).join(Product, OrderItem.product_id == Product.id)

    result = await db.execute(stmt)
    total = result.scalar() or 0
    ORDERS_COST_GAUGE.set(float(total))


async def update_products_count(db: AsyncSession) -> None:
    """Рахує кількість записів у таблиці products і оновлює gauge."""
    from app.models.product import Product

    stmt = select(func.count()).select_from(Product)
    result = await db.execute(stmt)
    count = result.scalar() or 0
    PRODUCTS_COUNT_GAUGE.set(float(count))
