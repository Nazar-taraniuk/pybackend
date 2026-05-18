"""
metrics.py — Кастомні Prometheus-метрики для PyBackend.

Метрики:
  - pybackend_total_orders_cost   : Gauge — загальна сума всіх замовлень
  - pybackend_products_total      : Gauge — кількість товарів у каталозі
  - pybackend_users_total         : Gauge — кількість зареєстрованих користувачів
  - pybackend_orders_total        : Gauge — кількість замовлень у БД
  - pybackend_categories_total    : Gauge — кількість категорій
  - pybackend_avg_order_value     : Gauge — середня вартість замовлення

Оновлення відбувається при кожному запиті через middleware у main.py.
"""
from prometheus_client import Gauge, Counter
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# ── Gauge метрики (поточний стан БД) ─────────────────────────────────────────
ORDERS_COST_GAUGE = Gauge(
    "pybackend_total_orders_cost",
    "Total monetary value of all order items (price × quantity)",
)

PRODUCTS_COUNT_GAUGE = Gauge(
    "pybackend_products_total",
    "Total number of products in the catalogue",
)

USERS_COUNT_GAUGE = Gauge(
    "pybackend_users_total",
    "Total number of registered users",
)

ORDERS_COUNT_GAUGE = Gauge(
    "pybackend_orders_total",
    "Total number of orders in the database",
)

CATEGORIES_COUNT_GAUGE = Gauge(
    "pybackend_categories_total",
    "Total number of product categories",
)

AVG_ORDER_VALUE_GAUGE = Gauge(
    "pybackend_avg_order_value",
    "Average order value in UAH (total_cost / orders_count)",
)

# ── Counter метрики (накопичувальні) ──────────────────────────────────────────
DB_UPDATES_COUNTER = Counter(
    "pybackend_metrics_db_updates_total",
    "Total number of times custom metrics were refreshed from DB",
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
    return float(total)


async def update_products_count(db: AsyncSession) -> None:
    """Рахує кількість записів у таблиці products і оновлює gauge."""
    from app.models.product import Product

    stmt = select(func.count()).select_from(Product)
    result = await db.execute(stmt)
    count = result.scalar() or 0
    PRODUCTS_COUNT_GAUGE.set(float(count))


async def update_users_count(db: AsyncSession) -> None:
    """Рахує кількість користувачів і оновлює gauge."""
    from app.models.user import User

    stmt = select(func.count()).select_from(User)
    result = await db.execute(stmt)
    count = result.scalar() or 0
    USERS_COUNT_GAUGE.set(float(count))


async def update_orders_count(db: AsyncSession) -> None:
    """Рахує кількість замовлень і оновлює gauge."""
    from app.models.order import Order

    stmt = select(func.count()).select_from(Order)
    result = await db.execute(stmt)
    count = result.scalar() or 0
    ORDERS_COUNT_GAUGE.set(float(count))


async def update_categories_count(db: AsyncSession) -> None:
    """Рахує кількість категорій і оновлює gauge."""
    from app.models.category import Category

    stmt = select(func.count()).select_from(Category)
    result = await db.execute(stmt)
    count = result.scalar() or 0
    CATEGORIES_COUNT_GAUGE.set(float(count))


async def update_avg_order_value(db: AsyncSession) -> None:
    """Рахує середнє значення замовлення і оновлює gauge."""
    from app.models.order import Order, OrderItem
    from app.models.product import Product

    # Загальна сума
    cost_stmt = select(
        func.coalesce(func.sum(Product.price * OrderItem.quantity), 0)
    ).join(Product, OrderItem.product_id == Product.id)
    cost_result = await db.execute(cost_stmt)
    total_cost = float(cost_result.scalar() or 0)

    # Кількість замовлень
    count_stmt = select(func.count()).select_from(Order)
    count_result = await db.execute(count_stmt)
    order_count = int(count_result.scalar() or 0)

    avg = total_cost / order_count if order_count > 0 else 0
    AVG_ORDER_VALUE_GAUGE.set(avg)


async def update_all_metrics(db: AsyncSession) -> None:
    """Оновлює всі кастомні метрики за один виклик."""
    await update_orders_cost(db)
    await update_products_count(db)
    await update_users_count(db)
    await update_orders_count(db)
    await update_categories_count(db)
    await update_avg_order_value(db)
    DB_UPDATES_COUNTER.inc()
