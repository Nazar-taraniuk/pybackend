# Лаба 7 — Моніторинг: Grafana + Prometheus

## Стек моніторингу

| Сервіс | Образ | Порт | Призначення |
|---|---|---|---|
| **Prometheus** | `prom/prometheus:v2.52.0` | 9090 | Збір та зберігання метрик |
| **Grafana** | `grafana/grafana:11.1.0` | 3000 | Візуалізація дашбордів |
| **postgres_exporter** | `prometheuscommunity/postgres-exporter:v0.15.0` | 9187 | Метрики PostgreSQL |
| **cAdvisor** | `gcr.io/cadvisor/cadvisor:v0.49.1` | 8080 | Метрики Docker-контейнерів |

## Кастомні метрики

| Метрика | Тип | Опис |
|---|---|---|
| `pybackend_total_orders_cost` | Gauge | Загальна сума всіх замовлень (price × quantity) |
| `pybackend_products_total` | Gauge | Кількість товарів у каталозі |

## Команди

```bash
# Запустити весь стек
docker compose up -d

# Зупинити
docker compose down

# Переглянути логи
docker compose logs -f
```

## URLs

- **FastAPI** → http://localhost:8000
- **Prometheus metrics** → http://localhost:8000/metrics
- **Prometheus UI** → http://localhost:9090
- **Grafana** → http://localhost:3000 (admin/admin)
- **cAdvisor** → http://localhost:8080
- **PostgreSQL Exporter** → http://localhost:9187/metrics

## Дашборди

### PyBackend — Custom Metrics
- 💰 Загальна сума замовлень
- 📦 Кількість товарів у каталозі
- 📈 HTTP Request Rate (req/s)
- ⏱️ HTTP Request Duration (p95)
- 🔴 Кількість HTTP помилок (4xx + 5xx)

### Популярні дашборди (імпортуються через Grafana ID)
- **PostgreSQL** → ID: `9628` (PostgreSQL Database)
- **cAdvisor** → ID: `14282` (Docker Container & Host Metrics)
- **FastAPI** → ID: `19840` (FastAPI Observability)

## Скріни

Скріни метрик та графіків знаходяться в папці `docs/screenshots/`.
