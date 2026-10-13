"""Ejecuta el script original de cada SO y comprueba el servidor real por HTTP."""

import datetime
import json
import os
import platform
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(sys.argv[1])
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
LOG = OUTPUT.with_suffix(".log")
IS_WINDOWS = sys.platform == "win32"
SCRIPT = "ejecutar_monitoreo.bat" if IS_WINDOWS else "ejecutar_monitoreo1.sh"
COMMAND = (["cmd.exe", "/d", "/c", str(ROOT / SCRIPT)] if IS_WINDOWS
           else ["bash", str(ROOT / SCRIPT)])
BASE_URL = "http://127.0.0.1:5000"


def stop_process_tree(process):
    if IS_WINDOWS:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)],
                       capture_output=True, check=False)
    elif process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if not IS_WINDOWS:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)


result = {
    "commit": os.environ.get("GITHUB_SHA"),
    "runner_os": os.environ.get("RUNNER_OS", platform.system()),
    "os": platform.platform(),
    "python": platform.python_version(),
    "script": SCRIPT,
    "checks": {},
    "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "status": "failed",
    "scope": "Instalación, arranque y HTTP local; no se comprueba la apertura gráfica del navegador",
}
process = None
started = time.monotonic()
try:
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", 5000)) == 0:
            raise RuntimeError("El puerto 5000 ya estaba ocupado antes de iniciar el script")

    with LOG.open("w", encoding="utf-8", errors="replace") as log:
        process = subprocess.Popen(COMMAND, cwd=ROOT, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if IS_WINDOWS else 0),
                                   start_new_session=not IS_WINDOWS)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"El script terminó antes del arranque (código {process.returncode})")
            try:
                with urllib.request.urlopen(BASE_URL + "/", timeout=3) as response:
                    body = response.read().decode("utf-8", errors="replace")
                    if response.status == 200 and "Última semana reportada" in body:
                        result["checks"]["home"] = 200
                        break
            except (urllib.error.URLError, TimeoutError, UnicodeError):
                pass
            time.sleep(1)
        else:
            raise TimeoutError("El servidor no respondió con la vista y los CSV reales en 180 s")

        with urllib.request.urlopen(BASE_URL + "/ranking", timeout=10) as response:
            body = response.read().decode("utf-8", errors="replace")
            if response.status != 200 or "Regiones de Mayor Carga" not in body:
                raise RuntimeError("La ruta /ranking no mostró la vista esperada")
            result["checks"]["ranking"] = response.status

        venv_python = (ROOT / "venv" / "Scripts" / "python.exe" if IS_WINDOWS
                       else ROOT / "venv" / "bin" / "python")
        versions = subprocess.check_output(
            [str(venv_python), "-c",
             "import importlib.metadata as m; print(m.version('Flask'), m.version('pandas'))"],
            text=True, timeout=10).strip().split()
        result["installed_packages"] = dict(zip(("Flask", "pandas"), versions))
        result["status"] = "passed"
except Exception as error:
    result["error"] = str(error)
finally:
    result["startup_seconds"] = round(time.monotonic() - started, 2)
    if process is not None:
        stop_process_tree(process)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if result["status"] != "passed":
    print(f"Portabilidad fallida: {result['error']}; revisar {LOG}", file=sys.stderr)
    raise SystemExit(1)
print(f"Portabilidad aprobada: {SCRIPT}, {result['checks']}")
