#!/usr/bin/env python3
"""
Прогріває API та кастомні Prometheus-метрики.
Запуск: python scripts/warmup_metrics.py [--base-url http://localhost:8000]
"""
import argparse
import sys
import urllib.error
import urllib.request


def hit(url: str, method: str = "GET", data: bytes | None = None) -> int:
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def main() -> int:
    parser = argparse.ArgumentParser(description="Warm up PyBackend metrics")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    endpoints = [
        "/",
        "/health",
        "/users/",
        "/users/1",
        "/profiles/",
        "/profiles/1",
        "/profiles/user/1",
        "/categories/",
        "/categories/1",
        "/products/",
        "/products/1",
        "/products/category/1",
        "/orders/",
        "/orders/1",
        "/metrics/refresh",
        "/metrics",
    ]

    print(f"Warming up {base} ...")
    for path in endpoints:
        status = hit(f"{base}{path}")
        print(f"  {path:30} -> {status}")

    print("Done. Check Grafana custom metrics (pybackend_*).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
