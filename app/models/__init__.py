# Імпортуємо всі моделі тут, щоб Alembic їх бачив при автогенерації міграцій
from app.models.user import User  # noqa: F401
from app.models.profile import Profile  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.order import Order, OrderItem  # noqa: F401
