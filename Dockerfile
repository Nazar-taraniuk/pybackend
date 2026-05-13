# Базовий образ Python
FROM python:3.11-slim

# Встановлюємо Poetry
RUN pip install poetry==2.4.1

# Робоча директорія всередині контейнера
WORKDIR /app

# Копіюємо файли залежностей
COPY pyproject.toml poetry.lock ./

# Встановлюємо залежності без створення venv (в контейнері не потрібно)
RUN poetry config virtualenvs.create false \
    && poetry install --no-root

# Копіюємо код (буде перекрито через volume mount, але потрібно для build)
COPY . .

# Запускаємо uvicorn з автоперезавантаженням
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
