"""Mide peticiones completas con Flask Test Client, sin servidor ni red."""

import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

from monitoreo_salud_publica.app import app, legacy_ready


if not legacy_ready():
    raise SystemExit("No hay tablas y figuras reales del legado en la ruta esperada")

app.config.update(TESTING=True)
routes = ["/", "/regional", "/severidad", "/ranking", "/pronosticos"]
sample_size = 30
warmups = 3
results = []
with app.test_client() as client:
    for route in routes:
        for _ in range(warmups):
            if client.get(route).status_code != 200:
                raise SystemExit(f"Falló el calentamiento de {route}")
        samples = []
        for _ in range(sample_size):
            start = time.perf_counter_ns()
            response = client.get(route)
            elapsed = (time.perf_counter_ns() - start) / 1_000_000
            if response.status_code != 200:
                raise SystemExit(f"HTTP {response.status_code} en {route}")
            samples.append(elapsed)
        sorted_samples = sorted(samples)
        results.append({
            "route": route,
            "http_status": 200,
            "repetitions": sample_size,
            "warmups": warmups,
            "mean_ms": round(statistics.mean(samples), 3),
            "median_ms": round(statistics.median(samples), 3),
            "p95_nearest_rank_ms": round(sorted_samples[28], 3),
            "max_ms": round(max(samples), 3),
            "samples_ms": [round(value, 3) for value in samples],
        })

output = Path(sys.argv[1])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({
    "commit": os.environ.get("GITHUB_SHA"),
    "runner_os": os.environ.get("RUNNER_OS", platform.system()),
    "python": platform.python_version(),
    "method": "Flask Test Client; tiempo de respuesta en proceso, sin red ni navegador",
    "data": "CSV/PNG precalculados del proyecto legado versionados en el mismo commit",
    "routes": results,
}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
