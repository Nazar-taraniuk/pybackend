#!/usr/bin/env python3
"""Generate 4 Grafana dashboards for PyBackend monitoring."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "monitoring" / "grafana" / "provisioning" / "dashboards"
DS = {"type": "prometheus", "uid": "prometheus"}
PY = 'datname="pybackend"'
# Avoid "No Data": fallback to zero only when series is absent
Z = " or on() vector(0)"


def _defaults(unit: str = "short", dec: int | None = None) -> dict:
    d: dict = {"color": {"mode": "palette-classic"}, "noValue": "0"}
    if unit:
        d["unit"] = unit
    if dec is not None:
        d["decimals"] = dec
    return d


def _target(expr: str, legend: str = "", ref: str = "A", instant: bool = False) -> dict:
    t: dict = {
        "datasource": DS,
        "expr": expr,
        "refId": ref,
        "legendFormat": legend,
    }
    if instant:
        t["instant"] = True
        t["range"] = False
    return t


def _grid(x: int, y: int, w: int, h: int) -> dict:
    return {"x": x, "y": y, "w": w, "h": h}


def row(pid: int, title: str, y: int) -> dict:
    return {
        "id": pid,
        "type": "row",
        "title": title,
        "gridPos": _grid(0, y, 24, 1),
        "collapsed": False,
    }


def stat(pid: int, title: str, x: int, y: int, w: int, h: int, expr: str, unit: str = "short") -> dict:
    return {
        "id": pid,
        "type": "stat",
        "title": title,
        "gridPos": _grid(x, y, w, h),
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"]},
            "colorMode": "background",
            "graphMode": "area",
        },
        "fieldConfig": {"defaults": _defaults(unit), "overrides": []},
        "targets": [_target(f"({expr}){Z}", title, instant=True)],
    }


def timeseries(
    pid: int,
    title: str,
    x: int,
    y: int,
    w: int,
    h: int,
    targets: list[tuple[str, str]],
    unit: str = "short",
    desc: str = "",
) -> dict:
    return {
        "id": pid,
        "type": "timeseries",
        "title": title,
        "description": desc,
        "gridPos": _grid(x, y, w, h),
        "options": {
            "tooltip": {"mode": "multi"},
            "legend": {"displayMode": "table", "placement": "bottom", "calcs": ["mean", "max", "last"]},
        },
        "fieldConfig": {"defaults": _defaults(unit), "overrides": []},
        "targets": [_target(e, l, chr(65 + i)) for i, (e, l) in enumerate(targets)],
    }


def gauge(pid: int, title: str, x: int, y: int, w: int, h: int, expr: str, unit: str = "percentunit") -> dict:
    return {
        "id": pid,
        "type": "gauge",
        "title": title,
        "gridPos": _grid(x, y, w, h),
        "fieldConfig": {
            "defaults": {**_defaults(unit), "min": 0, "max": 1 if unit == "percentunit" else None},
            "overrides": [],
        },
        "options": {"reduceOptions": {"calcs": ["lastNotNull"]}},
        "targets": [_target(f"({expr}){Z}", title, instant=True)],
    }


def dashboard(uid: str, title: str, tags: list[str], panels: list[dict]) -> dict:
    return {
        "uid": uid,
        "title": title,
        "tags": tags,
        "timezone": "browser",
        "schemaVersion": 38,
        "version": 1,
        "refresh": "10s",
        "time": {"from": "now-30m", "to": "now"},
        "timepicker": {},
        "templating": {"list": []},
        "panels": panels,
    }


def build_api_dashboard() -> dict:
    p: list[dict] = []
    y = 0
    p.append(row(1, "📡 API Server — огляд (як Kubernetes apiserver)", y))
    y += 1
    stats = [
        (2, "RPS (усі)", f'sum(rate(http_requests_total{{job="fastapi"}}[5m]))', "reqps"),
        (3, "Всього запитів", f'sum(http_requests_total{{job="fastapi"}})', "short"),
        (4, "Помилки RPS", f'sum(rate(http_requests_total{{job="fastapi",status=~"4..|5.."}}[5m]))', "reqps"),
        (5, "p95 latency", 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="fastapi"}[5m])) by (le))', "s"),
        (6, "p99 latency", 'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="fastapi"}[5m])) by (le))', "s"),
        (7, "Оновлень метрик", "pybackend_metrics_db_updates_total", "short"),
    ]
    for i, (pid, t, e, u) in enumerate(stats):
        p.append(stat(pid, t, (i % 6) * 4, y, 4, 4, e, u))
    y += 4

    p.append(row(10, "🐳 Обидва контейнери — API (FastAPI) та DB (PostgreSQL exporter)", y))
    y += 1
    p.append(stat(11, "API container UP", 0, y, 4, 4, 'up{job="fastapi"}', "short"))
    p.append(stat(12, "DB stack UP (pg_up)", 4, y, 4, 4, "pg_up", "short"))
    p.append(stat(13, "API RAM", 8, y, 4, 4, 'process_resident_memory_bytes{job="fastapi"}', "bytes"))
    p.append(stat(14, "DB exporter RAM", 12, y, 4, 4, 'process_resident_memory_bytes{job="postgres"}', "bytes"))
    p.append(stat(15, "API CPU rate", 16, y, 4, 4, 'rate(process_cpu_seconds_total{job="fastapi"}[5m])', "short"))
    p.append(stat(16, "DB CPU rate", 20, y, 4, 4, 'rate(process_cpu_seconds_total{job="postgres"}[5m])', "short"))
    y += 4

    p.append(
        timeseries(
            17,
            "API vs DB — використання RAM",
            0,
            y,
            12,
            8,
            [
                ('process_resident_memory_bytes{job="fastapi"}', "FastAPI (api)"),
                ('process_resident_memory_bytes{job="postgres"}', "Postgres exporter (db)"),
            ],
            "bytes",
        )
    )
    p.append(
        timeseries(
            18,
            "API vs DB — CPU time rate",
            12,
            y,
            12,
            8,
            [
                ('rate(process_cpu_seconds_total{job="fastapi"}[5m])', "FastAPI CPU"),
                ('rate(process_cpu_seconds_total{job="postgres"}[5m])', "Postgres exp. CPU"),
            ],
            "short",
        )
    )
    y += 8

    p.append(row(20, "📈 HTTP — швидкість та статуси", y))
    y += 1
    p.append(
        timeseries(
            21,
            "HTTP Request Rate by handler",
            0,
            y,
            24,
            8,
            [('topk(12, sum(rate(http_requests_total{job="fastapi"}[5m])) by (handler, method, status))', "{{handler}} {{method}} {{status}}")],
            "reqps",
        )
    )
    y += 8
    p.append(
        timeseries(
            22,
            "HTTP Rate by status code",
            0,
            y,
            12,
            8,
            [('sum(rate(http_requests_total{job="fastapi"}[5m])) by (status)', "{{status}}")],
            "reqps",
        )
    )
    p.append(
        timeseries(
            23,
            "HTTP Errors (4xx/5xx) rate",
            12,
            y,
            12,
            8,
            [('sum(rate(http_requests_total{job="fastapi",status=~"4..|5.."}[5m])) by (status)', "{{status}}")],
            "reqps",
        )
    )
    y += 8

    p.append(row(30, "⏱️ HTTP — затримки та розмір", y))
    y += 1
    p.append(
        timeseries(
            31,
            "Latency percentiles (p50 / p95 / p99)",
            0,
            y,
            12,
            8,
            [
                ('histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{job="fastapi"}[5m])) by (le))', "p50"),
                ('histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="fastapi"}[5m])) by (le))', "p95"),
                ('histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="fastapi"}[5m])) by (le))', "p99"),
            ],
            "s",
        )
    )
    p.append(
        timeseries(
            32,
            "p95 latency by handler",
            12,
            y,
            12,
            8,
            [
                (
                    'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="fastapi"}[5m])) by (le, handler))',
                    "{{handler}}",
                )
            ],
            "s",
        )
    )
    y += 8
    p.append(
        timeseries(
            33,
            "Request / Response size rate",
            0,
            y,
            24,
            8,
            [
                ("sum(rate(http_request_size_bytes_sum{job=\"fastapi\"}[5m]))", "request bytes/s"),
                ("sum(rate(http_response_size_bytes_sum{job=\"fastapi\"}[5m]))", "response bytes/s"),
            ],
            "Bps",
        )
    )
    y += 8

    p.append(row(40, "🔌 Python / Go runtime (процес API)", y))
    y += 1
    p.append(
        timeseries(
            41,
            "Python GC collections",
            0,
            y,
            12,
            6,
            [('rate(python_gc_collections_total{job="fastapi"}[5m])', "{{generation}}")],
        )
    )
    p.append(
        timeseries(
            42,
            "Open FDs (API process)",
            12,
            y,
            12,
            6,
            [
                ('process_open_fds{job="fastapi"}', "open fds"),
                ('process_max_fds{job="fastapi"}', "max fds"),
            ],
        )
    )
    return dashboard("pybackend-api", "PyBackend — API Server", ["pybackend", "api", "fastapi"], p)


def build_postgresql_dashboard() -> dict:
    p: list[dict] = []
    y = 0
    p.append(row(1, "🗄️ PostgreSQL — стан кластера (pybackend)", y))
    y += 1
    for i, (pid, t, e, u) in enumerate(
        [
            (2, "pg_up", "pg_up", "short"),
            (3, "З'єднання", f"pg_stat_database_numbackends{{{PY}}}", "short"),
            (4, "Розмір БД", f"pg_database_size_bytes{{{PY}}}", "bytes"),
            (5, "Commits/s", f"rate(pg_stat_database_xact_commit{{{PY}}}[5m])", "ops"),
            (6, "Rollbacks/s", f"rate(pg_stat_database_xact_rollback{{{PY}}}[5m])", "ops"),
            (7, "Deadlocks", f"pg_stat_database_deadlocks{{{PY}}}", "short"),
        ]
    ):
        p.append(stat(pid, t, i * 4, y, 4, 4, e, u))
    y += 4

    p.append(row(10, "📊 Активність БД", y))
    y += 1
    p.append(
        timeseries(
            11,
            "Tuples: returned / fetched / inserted",
            0,
            y,
            12,
            8,
            [
                (f"rate(pg_stat_database_tup_returned{{{PY}}}[5m])", "returned"),
                (f"rate(pg_stat_database_tup_fetched{{{PY}}}[5m])", "fetched"),
                (f"rate(pg_stat_database_tup_inserted{{{PY}}}[5m])", "inserted"),
            ],
            "ops",
        )
    )
    p.append(
        timeseries(
            12,
            "Tuples: updated / deleted",
            12,
            y,
            12,
            8,
            [
                (f"rate(pg_stat_database_tup_updated{{{PY}}}[5m])", "updated"),
                (f"rate(pg_stat_database_tup_deleted{{{PY}}}[5m])", "deleted"),
            ],
            "ops",
        )
    )
    y += 8
    p.append(
        gauge(
            13,
            "Cache hit ratio",
            0,
            y,
            6,
            6,
            f"pg_stat_database_blks_hit{{{PY}}} / (pg_stat_database_blks_hit{{{PY}}} + pg_stat_database_blks_read{{{PY}}} + 0.0001)",
        )
    )
    p.append(
        timeseries(
            14,
            "Block I/O — hit vs read rate",
            6,
            y,
            18,
            6,
            [
                (f"rate(pg_stat_database_blks_hit{{{PY}}}[5m])", "hit"),
                (f"rate(pg_stat_database_blks_read{{{PY}}}[5m])", "read"),
            ],
            "ops",
        )
    )
    y += 6

    p.append(row(20, "🔒 Locks & WAL", y))
    y += 1
    p.append(
        timeseries(
            21,
            "Locks by mode",
            0,
            y,
            12,
            8,
            [("pg_locks_count", "{{mode}}")],
        )
    )
    p.append(
        timeseries(
            22,
            "WAL size & segments",
            12,
            y,
            12,
            8,
            [
                ("pg_wal_size_bytes", "wal size"),
                ("pg_wal_segments", "segments"),
            ],
            "bytes",
        )
    )
    y += 8

    p.append(row(30, "📋 Таблиці (user tables)", y))
    y += 1
    p.append(
        timeseries(
            31,
            "Live vs dead tuples (top tables)",
            0,
            y,
            12,
            8,
            [
                ("topk(8, pg_stat_user_tables_n_live_tup)", "live {{relname}}"),
                ("topk(8, pg_stat_user_tables_n_dead_tup)", "dead {{relname}}"),
            ],
        )
    )
    p.append(
        timeseries(
            32,
            "Seq scans vs idx scans",
            12,
            y,
            12,
            8,
            [
                ("topk(6, rate(pg_stat_user_tables_seq_scan[5m]))", "seq {{relname}}"),
                ("topk(6, rate(pg_stat_user_tables_idx_scan[5m]))", "idx {{relname}}"),
            ],
            "ops",
        )
    )
    y += 8
    p.append(
        timeseries(
            33,
            "Table sizes (bytes)",
            0,
            y,
            24,
            8,
            [("pg_stat_user_tables_size_bytes", "{{relname}}")],
            "bytes",
        )
    )
    y += 8

    p.append(row(40, "⚙️ Exporter & налаштування", y))
    y += 1
    p.append(stat(41, "Scrape OK", 0, y, 4, 4, "pg_exporter_last_scrape_error", "short"))
    p.append(stat(42, "Max connections", 4, y, 4, 4, "pg_settings_max_connections", "short"))
    p.append(stat(43, "Shared buffers", 8, y, 4, 4, "pg_settings_shared_buffers_bytes", "bytes"))
    p.append(
        timeseries(
            44,
            "Scrape duration",
            12,
            y,
            12,
            6,
            [("pg_exporter_last_scrape_duration_seconds", "duration")],
            "s",
        )
    )
    return dashboard("pybackend-postgresql", "PyBackend — PostgreSQL", ["pybackend", "postgres"], p)


def build_docker_dashboard() -> dict:
    p: list[dict] = []
    y = 0
    docker_id = 'id="/docker"'
    p.append(row(1, "🐳 Docker / cAdvisor — хост та cgroup", y))
    y += 1
    for i, (pid, t, e, u) in enumerate(
        [
            (2, "Machine RAM", "machine_memory_bytes", "bytes"),
            (3, "CPU cores", "machine_cpu_cores", "short"),
            (4, "cAdvisor UP", 'up{job="cadvisor"}', "short"),
            (5, "Prometheus UP", 'up{job="prometheus"}', "short"),
            (6, "FastAPI scrape UP", 'up{job="fastapi"}', "short"),
            (7, "Postgres scrape UP", 'up{job="postgres"}', "short"),
        ]
    ):
        p.append(stat(pid, t, i * 4, y, 4, 4, e, u))
    y += 4

    p.append(row(10, "📦 Cgroup /docker (усі контейнери разом на Windows)", y))
    y += 1
    p.append(
        timeseries(
            11,
            "CPU usage (/docker)",
            0,
            y,
            12,
            8,
            [(f"rate(container_cpu_usage_seconds_total{{{docker_id}}}[5m])", "CPU")],
            "percentunit",
        )
    )
    p.append(
        timeseries(
            12,
            "Memory usage (/docker)",
            12,
            y,
            12,
            8,
            [
                (f"container_memory_usage_bytes{{{docker_id}}}", "usage"),
                (f"container_memory_working_set_bytes{{{docker_id}}}", "working set"),
                (f"container_memory_rss{{{docker_id}}}", "rss"),
            ],
            "bytes",
        )
    )
    y += 8
    p.append(
        timeseries(
            13,
            "Network RX/TX (/docker)",
            0,
            y,
            12,
            8,
            [
                (f"rate(container_network_receive_bytes_total{{{docker_id}}}[5m])", "RX"),
                (f"rate(container_network_transmit_bytes_total{{{docker_id}}}[5m])", "TX"),
            ],
            "Bps",
        )
    )
    p.append(
        timeseries(
            14,
            "Disk I/O (/docker)",
            12,
            y,
            12,
            8,
            [
                (f"rate(container_fs_reads_bytes_total{{{docker_id}}}[5m])", "read"),
                (f"rate(container_fs_writes_bytes_total{{{docker_id}}}[5m])", "write"),
            ],
            "Bps",
        )
    )
    y += 8

    p.append(row(20, "🎯 Scrape targets (усі jobs)", y))
    y += 1
    p.append(
        timeseries(
            21,
            "Scrape duration by job",
            0,
            y,
            12,
            8,
            [("scrape_duration_seconds", "{{job}}")],
            "s",
        )
    )
    p.append(
        timeseries(
            22,
            "Samples scraped",
            12,
            y,
            12,
            8,
            [("scrape_samples_scraped", "{{job}}")],
        )
    )
    y += 8

    p.append(row(30, "🧩 Процеси сервісів (через exporters)", y))
    y += 1
    p.append(
        timeseries(
            31,
            "RAM: FastAPI / Postgres exp. / cAdvisor / Prometheus",
            0,
            y,
            24,
            8,
            [
                ('process_resident_memory_bytes{job="fastapi"}', "fastapi"),
                ('process_resident_memory_bytes{job="postgres"}', "postgres"),
                ('process_resident_memory_bytes{job="cadvisor"}', "cadvisor"),
                ('process_resident_memory_bytes{job="prometheus"}', "prometheus"),
            ],
            "bytes",
        )
    )
    y += 8
    p.append(
        timeseries(
            32,
            "CPU rate by job (process)",
            0,
            y,
            24,
            8,
            [
                ('rate(process_cpu_seconds_total{job="fastapi"}[5m])', "fastapi"),
                ('rate(process_cpu_seconds_total{job="postgres"}[5m])', "postgres"),
                ('rate(process_cpu_seconds_total{job="cadvisor"}[5m])', "cadvisor"),
                ('rate(process_cpu_seconds_total{job="prometheus"}[5m])', "prometheus"),
            ],
        )
    )
    y += 8

    p.append(row(40, "💾 Filesystem & OOM", y))
    y += 1
    p.append(
        timeseries(
            41,
            "FS usage vs limit (/docker)",
            0,
            y,
            12,
            8,
            [
                (f"container_fs_usage_bytes{{{docker_id}}}", "used"),
                (f"container_fs_limit_bytes{{{docker_id}}}", "limit"),
            ],
            "bytes",
        )
    )
    p.append(
        timeseries(
            42,
            "OOM events",
            12,
            y,
            12,
            6,
            [(f"container_oom_events_total{{{docker_id}}}", "oom")],
        )
    )
    return dashboard("pybackend-docker", "PyBackend — Docker / cAdvisor", ["pybackend", "docker", "cadvisor"], p)


def build_custom_dashboard() -> dict:
    p: list[dict] = []
    y = 0
    p.append(row(1, "🎯 Кастомні бізнес-метрики PyBackend", y))
    y += 1
    customs = [
        (2, "💰 Total Orders Cost", "pybackend_total_orders_cost", "currencyUAH"),
        (3, "📦 Products", "pybackend_products_total", "short"),
        (4, "👤 Users", "pybackend_users_total", "short"),
        (5, "🛒 Orders", "pybackend_orders_total", "short"),
        (6, "📂 Categories", "pybackend_categories_total", "short"),
        (7, "💵 Avg Order Value", "pybackend_avg_order_value", "currencyUAH"),
        (8, "🔄 DB Refreshes", "pybackend_metrics_db_updates_total", "short"),
    ]
    for i, (pid, t, m, u) in enumerate(customs):
        p.append(stat(pid, t, (i % 6) * 4, y + (i // 6) * 4, 4, 4, f"last_over_time({m}[5m])", u))
    y += 8

    p.append(row(20, "📈 Динаміка в часі", y))
    y += 1
    p.append(
        timeseries(
            21,
            "Каталог і користувачі",
            0,
            y,
            12,
            8,
            [
                ("pybackend_users_total", "users"),
                ("pybackend_products_total", "products"),
                ("pybackend_categories_total", "categories"),
            ],
        )
    )
    p.append(
        timeseries(
            22,
            "Замовлення та виручка",
            12,
            y,
            12,
            8,
            [
                ("pybackend_orders_total", "orders"),
                ("pybackend_total_orders_cost", "total cost UAH"),
            ],
        )
    )
    y += 8
    p.append(
        timeseries(
            23,
            "Avg order value & refresh counter",
            0,
            y,
            24,
            8,
            [
                ("pybackend_avg_order_value", "avg order"),
                ("rate(pybackend_metrics_db_updates_total[5m])", "refresh rate"),
            ],
        )
    )
    return dashboard("pybackend-custom", "PyBackend — Custom Metrics", ["pybackend", "custom"], p)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    boards = [
        ("01_api.json", build_api_dashboard()),
        ("02_postgresql.json", build_postgresql_dashboard()),
        ("03_docker.json", build_docker_dashboard()),
        ("04_custom.json", build_custom_dashboard()),
    ]
    old = OUT / "pybackend_custom.json"
    if old.exists():
        old.unlink()
    for name, body in boards:
        path = OUT / name
        path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {path}")
    print("Done — 4 dashboards generated.")


if __name__ == "__main__":
    main()
