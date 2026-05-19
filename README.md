# PyBackend — FastAPI College Project

Шаблонний FastAPI проект для коледжу.

## Вимоги

- Python 3.11+
- [Poetry](https://python-poetry.org/)

## Встановлення

```bash
poetry install
```

## Запуск

```bash
poetry run uvicorn app.main:app --reload
```

## Документація API

Після запуску доступна за адресою:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Git branches

| Branch | Зміст |
|--------|--------|
| `main` | Код застосунку, без `docs/` (лабораторні скріншоти) |
| `dev` | Код + `docs/` (скріншоти, звіти тестів) |

## Моніторинг (Grafana + Prometheus)

```bash
docker compose up -d
python scripts/warmup_metrics.py
```

- Grafana: http://localhost:3000 (admin / admin)
- Prometheus: http://localhost:9090
- Метрики API: http://localhost:8000/metrics
