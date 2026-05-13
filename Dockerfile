# Базовий образ Python
FROM python:3.11-slim

# Встановлюємо Poetry
RUN pip install poetry==2.4.1

# Робоча директорія всередині контейнера
WORKDIR /app

# Копіюємо файли залежностей
COPY pyproject.toml poetry.lock ./

# Встановлюємо залежності без створення venv
RUN poetry config virtualenvs.create false \
    && poetry install --no-root

# Копіюємо код (буде перекрито через volume mount)
COPY . .

# Запуск: міграції → seed → сервер
CMD ["sh", "-c", "alembic upgrade head && python seed.py && python main.py"]
