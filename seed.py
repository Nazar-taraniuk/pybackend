"""
Seed script — заповнює БД початковими даними.
Запускається один раз при старті (якщо таблиці порожні).
"""
import asyncio
from decimal import Decimal
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.models.profile import Profile
from app.models.order import Order, OrderItem


async def seed():
    async with AsyncSessionLocal() as db:
        # Перевіряємо чи вже є дані
        result = await db.execute(select(Category))
        if result.scalars().first():
            print("Seed: дані вже існують, пропускаємо.")
            return

        print("Seed: заповнюємо БД початковими даними...")

        # Категорії
        electronics = Category(name="Електроніка", description="Гаджети та пристрої")
        clothing = Category(name="Одяг", description="Чоловічий та жіночий одяг")
        food = Category(name="Їжа", description="Продукти харчування")
        db.add_all([electronics, clothing, food])
        await db.flush()

        # Товари
        products = [
            Product(name="Ноутбук Lenovo", description="15.6 дюймів, 16GB RAM", price=Decimal("25999.99"), stock=10, category_id=electronics.id),
            Product(name="Смартфон Samsung", description="128GB, AMOLED екран", price=Decimal("14999.99"), stock=25, category_id=electronics.id),
            Product(name="Навушники Sony", description="Бездротові, шумопоглинання", price=Decimal("4499.99"), stock=15, category_id=electronics.id),
            Product(name="Футболка Nike", description="Бавовна 100%, розмір M", price=Decimal("799.99"), stock=50, category_id=clothing.id),
            Product(name="Джинси Levi's", description="Класичний крій, синій", price=Decimal("2199.99"), stock=30, category_id=clothing.id),
            Product(name="Кава Lavazza", description="Мелена, 250г, Арабіка", price=Decimal("349.99"), stock=100, category_id=food.id),
            Product(name="Чай Ahmad", description="Чорний, 100 пакетиків", price=Decimal("189.99"), stock=80, category_id=food.id),
        ]
        db.add_all(products)
        await db.flush()

        # Юзери
        ivan = User(name="Ivan Petrenko", email="ivan@example.com")
        olena = User(name="Olena Kovalenko", email="olena@example.com")
        maksym = User(name="Maksym Bondarenko", email="maksym@example.com")
        db.add_all([ivan, olena, maksym])
        await db.flush()

        # Профілі (one-to-one)
        db.add_all([
            Profile(user_id=ivan.id, bio="Розробник Python", phone="+380671234567"),
            Profile(user_id=olena.id, bio="Дизайнер UI/UX", phone="+380507654321"),
            Profile(user_id=maksym.id, bio="DevOps інженер", phone="+380631112233"),
        ])
        await db.flush()

        # Замовлення
        order1 = Order(user_id=ivan.id, status="completed")
        order2 = Order(user_id=ivan.id, status="pending")
        order3 = Order(user_id=olena.id, status="processing")
        db.add_all([order1, order2, order3])
        await db.flush()

        # Позиції замовлень
        db.add_all([
            OrderItem(order_id=order1.id, product_id=products[0].id, quantity=1),
            OrderItem(order_id=order1.id, product_id=products[5].id, quantity=2),
            OrderItem(order_id=order2.id, product_id=products[1].id, quantity=1),
            OrderItem(order_id=order3.id, product_id=products[3].id, quantity=3),
            OrderItem(order_id=order3.id, product_id=products[4].id, quantity=1),
        ])

        await db.commit()
        print("Seed: готово!")


if __name__ == "__main__":
    asyncio.run(seed())
