"""Guarda las condiciones reales de la medición en GitHub Actions."""

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def version(package):
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


output = Path(sys.argv[1])
output.parent.mkdir(parents=True, exist_ok=True)
result = {
    "commit": os.environ.get("GITHUB_SHA") or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip(),
    "runner_os": os.environ.get("RUNNER_OS", platform.system()),
    "os": platform.platform(),
    "python": platform.python_version(),
    "architecture": platform.machine(),
    "logical_cpus": os.cpu_count(),
    "packages": {p: version(p) for p in ("Flask", "pandas", "pymetrica", "pytest", "coverage")},
    "scope": "monitoreo_salud_publica/app.py; se excluyen modelos y datos masivos del legado",
    "test_dataset": "CSV controlados y temporales, creados por pytest; no son datos epidemiológicos reales",
}
output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
