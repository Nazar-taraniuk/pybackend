# PyBackend — Документація проекту

> FastAPI backend-проект, розроблений в рамках лабораторних робіт. Python 3.11, PostgreSQL, Docker, Prometheus, Grafana, GitHub Actions.

---

## Зміст

1. [Загальна архітектура](#1-загальна-архітектура)
2. [Структура проекту](#2-структура-проекту)
3. [Лаба 1-2 — Ініціалізація проекту](#3-лаба-1-2--ініціалізація)
4. [Лаба 3 — Моделі та база даних](#4-лаба-3--моделі-та-база-даних)
5. [Лаба 4 — REST API](#5-лаба-4--rest-api)
6. [Лаба 5 — Авторизація JWT](#6-лаба-5--авторизація-jwt)
7. [Лаба 6 — Тести](#7-лаба-6--тести)
8. [Лаба 7 — Моніторинг](#8-лаба-7--моніторинг)
9. [Лаба 8 — CI/CD та AWS](#9-лаба-8--cicd-та-aws)
10. [Як запустити](#10-як-запустити)

---

## 1. Загальна архітектура

```
Клієнт (браузер / Postman)
        │
        ▼
  FastAPI (port 8000)
        │
        ├─── PostgreSQL (port 5433 → 5432)
        │         └── БД: pybackend (прод), pybackend_test (тести)
        │
        ├─── Prometheus (port 9090)  ←── scrape /metrics кожні 15 сек
        │
        ├─── Grafana (port 3000)     ←── читає з Prometheus
        │
        ├─── postgres_exporter (9187) ←── метрики PostgreSQL
        │
        └─── cAdvisor (port 8080)   ←── метрики Docker-контейнерів
```

Весь стек підіймається однією командою: `docker compose up -d`

---

## 2. Структура проекту

```
pybackend/
├── app/
│   ├── main.py           # FastAPI app, підключення роутерів, middleware
│   ├── config.py         # Налаштування (pydantic-settings, читає .env)
│   ├── database.py       # SQLAlchemy engine, get_db() dependency
│   ├── auth.py           # bcrypt хешування, JWT створення/декодування
│   ├── dependencies.py   # get_current_user() — читає JWT з куки
│   ├── metrics.py        # Кастомні Prometheus метрики (Gauge)
│   ├── models/           # SQLAlchemy ORM моделі
│   ├── schemas/          # Pydantic схеми (валідація)
│   ├── crud/             # Функції роботи з БД
│   └── routers/          # HTTP ендпоінти
├── tests/
│   ├── conftest.py       # Фікстури: тестова БД, HTTP клієнт
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_profiles.py
│   ├── test_categories.py
│   ├── test_products.py
│   ├── test_orders.py
│   ├── test_crud.py      # Unit-тести CRUD функцій
│   └── test_root.py
├── alembic/              # Міграції бази даних
├── monitoring/
│   ├── prometheus/prometheus.yml
│   └── grafana/provisioning/
│       ├── datasources/prometheus.yml
│       └── dashboards/pybackend_custom.json
├── .github/workflows/deploy.yml   # CI/CD пайплайн
├── main.py               # Точка входу (запускає uvicorn)
├── seed.py               # Заповнення БД початковими даними
├── Dockerfile
├── docker-compose.yml        # Локальна розробка
├── docker-compose.prod.yml   # Продакшн (EC2)
└── pyproject.toml        # Залежності (Poetry)
```

---

## 3. Лаба 1-2 — Ініціалізація

**Що зроблено:**
- Ініціалізовано проект через Poetry (`pyproject.toml`)
- Налаштовано Git із гілками `main` та `dev`
- Написано `Dockerfile` на базі `python:3.11-slim`
- Написано `docker-compose.yml` з сервісами `api` та `db`
- Налаштовано Alembic для міграцій

**Dockerfile — послідовність:**
```
python:3.11-slim
  → pip install poetry
  → poetry install (всі залежності)
  → COPY . .
  → CMD: alembic upgrade head && python seed.py && python main.py
```

**Команди:**
```bash
docker compose up -d          # Запустити
docker compose down           # Зупинити
docker compose logs api -f    # Логи API
docker compose exec api bash  # Shell в контейнері
```

---

## 4. Лаба 3 — Моделі та база даних

### Схема БД

```
users ──────────────────────────────────────────────
  id PK | name | email UNIQUE | password_hash | created_at

profiles (one-to-one з users) ──────────────────────
  id PK | user_id FK→users | bio | phone

categories ─────────────────────────────────────────
  id PK | name UNIQUE | description

products (many-to-one з categories) ────────────────
  id PK | name | description | price NUMERIC | stock | category_id FK→categories

orders (many-to-one з users) ───────────────────────
  id PK | user_id FK→users | status | created_at

order_items (many-to-one з orders і products) ───────
  id PK | order_id FK→orders | product_id FK→products | quantity
```

### Зв'язки SQLAlchemy

| Від | До | Тип |
|-----|----|-----|
| User | Profile | one-to-one, cascade delete |
| User | Order[] | one-to-many, cascade delete |
| Category | Product[] | one-to-many |
| Order | OrderItem[] | one-to-many, cascade delete |
| Product | OrderItem[] | one-to-many |

### Підключення до БД (`app/database.py`)

```python
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session  # FastAPI Dependency Injection
```

### Seed-дані (`seed.py`)

При першому старті автоматично:
- 3 категорії: Електроніка, Одяг, Їжа
- 7 товарів (Lenovo, Samsung, Sony, Nike, Levi's, Lavazza, Ahmad)
- 3 користувачі + профілі (Ivan, Olena, Maksym)
- 3 замовлення з 5 позиціями

---

## 5. Лаба 4 — REST API

### Всі ендпоінти

#### `/auth` — Авторизація

| Метод | URL | Опис | Auth |
|-------|-----|------|------|
| POST | `/auth/register` | Реєстрація (bcrypt хеш) | ❌ |
| POST | `/auth/login` | Вхід, JWT у HTTP-only куці | ❌ |
| POST | `/auth/logout` | Вихід, очищення куки | ❌ |
| GET | `/auth/me` | Дані поточного юзера | ✅ |
| GET | `/auth/my-orders` | Мої замовлення | ✅ |
| PUT | `/auth/me` | Оновити своє ім'я | ✅ |

#### `/users`, `/profiles`, `/categories`, `/products`, `/orders`

Кожен ресурс: повний CRUD

| Метод | URL | Статус |
|-------|-----|--------|
| GET | `/{resource}/` | 200 |
| GET | `/{resource}/{id}` | 200 / 404 |
| POST | `/{resource}/` | 201 |
| PUT | `/{resource}/{id}` | 200 / 404 |
| DELETE | `/{resource}/{id}` | 204 / 404 |

**Swagger UI:** http://localhost:8000/docs

### CRUD патерн (`app/crud/*.py`)

```python
async def get_all(db, skip=0, limit=100):
    result = await db.execute(select(Model).offset(skip).limit(limit))
    return result.scalars().all()

async def create(db, data: SchemaCreate):
    obj = Model(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
```

---

## 6. Лаба 5 — Авторизація JWT

### Схема роботи

```
POST /auth/register
  → validate (Pydantic)
  → hash_password(password)  ← bcrypt + сіль
  → INSERT INTO users
  → повернути UserResponse (без хешу!)

POST /auth/login
  → get_by_email(email)
  → verify_password(plain, hash)  ← bcrypt.checkpw
  → create_access_token(user_id)  ← JWT HS256, exp=24год
  → Set-Cookie: access_token=<jwt>; HttpOnly; SameSite=Lax

GET /auth/me  (захищений)
  → Cookie: access_token → decode_token() → user_id
  → get_by_id(db, user_id) → User
  → повернути UserResponse
```

### Ключові функції (`app/auth.py`)

| Функція | Опис |
|---------|------|
| `hash_password(pwd)` | bcrypt.hashpw з автосіллю |
| `verify_password(plain, hash)` | bcrypt.checkpw → bool |
| `create_access_token(user_id)` | JWT {sub: user_id, exp: +24h} |
| `decode_token(token)` | JWT decode → user_id |

### Захист ендпоінтів

```python
# app/dependencies.py
async def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = decode_token(access_token)
    return await user_crud.get_by_id(db, user_id)

# Використання в роутері:
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

---

## 7. Лаба 6 — Тести

### Принцип ізоляції

```
Продова БД (pybackend)         ← не чіпається
Тестова БД (pybackend_test)    ← окрема БД

dependency_overrides:
  get_db → override_get_db     ← підміна на тестову сесію

Після кожного тесту:
  TRUNCATE order_items, orders, profiles, products, categories, users
  RESTART IDENTITY CASCADE
```

### Фікстури (`tests/conftest.py`)

| Фікстура | Scope | Опис |
|----------|-------|------|
| `setup_test_db` | session | CREATE TABLE → тести → DROP TABLE |
| `clean_tables` | function (autouse) | TRUNCATE після кожного тесту |
| `db_session` | function | Пряма сесія для unit-тестів CRUD |
| `client` | function | AsyncClient + підміна get_db |
| `auth_client` | function | client + реєстрація + login |

### Підтримка двох середовищ

- **Локально (Docker):** `TEST_DATABASE_URL = postgresql+asyncpg://admin:secret@db:5432/pybackend_test`, БД створюється через asyncpg якщо не існує
- **CI (GitHub Actions):** `DATABASE_URL` береться з env var, БД вже існує як service container — пропускаємо створення

### Що тестується

| Файл | Кількість тестів | Що перевіряє |
|------|-----------------|--------------|
| `test_auth.py` | 10 | register, login, logout, /me, /my-orders |
| `test_users.py` | ~8 | CRUD /users/, 404 при відсутності |
| `test_profiles.py` | ~6 | CRUD /profiles/ |
| `test_categories.py` | ~6 | CRUD /categories/ |
| `test_products.py` | ~6 | CRUD /products/ |
| `test_orders.py` | ~6 | CRUD /orders/ |
| `test_crud.py` | ~15 | Unit-тести CRUD функцій через db |
| `test_root.py` | 2 | GET /, GET /health |

**Запуск:**
```bash
docker compose exec api pytest tests/ -v
```

---

## 8. Лаба 7 — Моніторинг

### Сервіси

| Сервіс | Образ | Порт | Призначення |
|--------|-------|------|-------------|
| Prometheus | `prom/prometheus:v2.52.0` | 9090 | Збір метрик |
| Grafana | `grafana/grafana:11.1.0` | 3000 | Дашборди |
| postgres_exporter | `prometheuscommunity/postgres-exporter:v0.15.0` | 9187 | Метрики PostgreSQL |
| cAdvisor | `gcr.io/cadvisor/cadvisor:v0.49.1` | 8080 | Метрики Docker |

### Scrape targets (`monitoring/prometheus/prometheus.yml`)

```yaml
scrape_configs:
  - job_name: "fastapi"
    static_configs:
      - targets: ["api:8000"]     # GET /metrics кожні 15 сек
  - job_name: "postgres"
    static_configs:
      - targets: ["postgres_exporter:9187"]
  - job_name: "cadvisor"
    static_configs:
      - targets: ["cadvisor:8080"]
```

### Кастомні метрики (`app/metrics.py`)

| Метрика | Тип | Формула |
|---------|-----|---------|
| `pybackend_total_orders_cost` | Gauge | `SUM(products.price × order_items.quantity)` |
| `pybackend_products_total` | Gauge | `COUNT(*) FROM products` |

Оновлюються через `@app.middleware("http")` після кожного запиту.

### Grafana

- **URL:** http://localhost:3000 (admin/admin)
- **Datasource:** Prometheus (auto-provisioned)
- **Дашборд:** PyBackend → "PyBackend — Custom Metrics" (auto-provisioned)
- **Панелі:** Total Orders Cost, Products Count, HTTP Rate, Latency p95, Errors

**Популярні дашборди для імпорту:**
- PostgreSQL: `9628`
- Docker/cAdvisor: `14282`
- FastAPI: `19840`

---

## 9. Лаба 8 — CI/CD та AWS

### GitHub Actions Pipeline (`.github/workflows/deploy.yml`)

```
git push origin main / dev
        │
        ▼
Job 1: 🧪 TEST
  ├── GitHub запускає postgres:16-alpine як service container
  ├── pip install + poetry install
  └── pytest tests/ -v  (DATABASE_URL вказує на service container)
        │
        ▼ (тільки якщо push, не PR)
Job 2: 🐳 BUILD & PUSH
  ├── docker buildx build .
  ├── Tag: sha-<7chars>, branch-name, latest (тільки main)
  └── docker push → Docker Hub
        │
        ▼ (тільки main branch)
Job 3: 🚀 DEPLOY TO EC2
  ├── SCP: docker-compose.prod.yml + monitoring/ → /home/ubuntu/pybackend/
  ├── SSH: docker pull <image>:<sha-tag>
  ├── SSH: docker compose -f docker-compose.prod.yml up -d
  ├── SSH: curl http://localhost:8000/health  (health check)
  └── SSH: docker image prune -f
```

### Тригери pipeline

| Event | test | build | deploy |
|-------|------|-------|--------|
| `push → dev` | ✅ | ✅ | ❌ |
| `push → main` | ✅ | ✅ | ✅ |
| `pull_request → main` | ✅ | ❌ | ❌ |

### GitHub Secrets

| Secret | Значення |
|--------|---------|
| `EC2_HOST` | Публічний IP EC2 (наприклад `54.123.45.67`) |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Вміст `.pem` файлу (SSH private key) |
| `DOCKER_HUB_USERNAME` | Docker Hub логін |
| `DOCKER_HUB_TOKEN` | Docker Hub Access Token |

### AWS EC2 Free Tier

- **Інстанс:** t2.micro (750 год/міс — безкоштовно 12 місяців)
- **OS:** Ubuntu 24.04 LTS
- **Порти:** 22 (SSH), 80 (HTTP), 8000 (FastAPI), 443 (HTTPS)
- **На сервері:** Docker + Docker Compose + `.env` файл

### `docker-compose.prod.yml` (відмінність від dev)

- Використовує готовий образ з Docker Hub: `${DOCKER_HUB_USERNAME}/pybackend:${IMAGE_TAG}`
- Немає volume mount вихідного коду
- `restart: always` (замість `unless-stopped`)
- ENV змінні беруться з `.env` файлу на сервері

---

## 10. Як запустити

### Локально

```bash
# Клонувати і запустити
git clone https://github.com/<user>/pybackend.git
cd pybackend
docker compose up -d

# Перевірка
curl http://localhost:8000/health   # {"status": "ok"}

# Swagger UI
# http://localhost:8000/docs

# Grafana: http://localhost:3000  (admin/admin)
# Prometheus: http://localhost:9090
# cAdvisor: http://localhost:8080
# Metrics: http://localhost:8000/metrics
```

### Тести

```bash
docker compose exec api pytest tests/ -v
```

### Перша реєстрація

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Назар", "email": "nazar@example.com", "password": "password123"}'
```

---

## Технологічний стек

| Категорія | Технологія | Версія |
|-----------|-----------|--------|
| Мова | Python | 3.11 |
| Web-фреймворк | FastAPI | 0.136 |
| ASGI сервер | Uvicorn | 0.46 |
| ORM | SQLAlchemy (async) | 2.0 |
| БД | PostgreSQL | 16 |
| Драйвер БД | asyncpg | 0.31 |
| Міграції | Alembic | 1.18 |
| Валідація | Pydantic v2 | 2.13 |
| Аутентифікація | python-jose + bcrypt | JWT HS256 |
| Менеджер залежностей | Poetry | 2.4 |
| Контейнеризація | Docker + Docker Compose | — |
| Моніторинг | Prometheus + Grafana | 2.52 / 11.1 |
| Метрики | prometheus-fastapi-instrumentator | 7.1 |
| Тести | pytest + pytest-asyncio + httpx | — |
| CI/CD | GitHub Actions | — |
| Хостинг | AWS EC2 t2.micro | Free Tier |
