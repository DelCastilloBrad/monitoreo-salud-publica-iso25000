@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  TP5 - Auditoria centralizada ISO/IEC 20246 y 5055
echo ============================================================
echo.

set "PYTHON_CMD=py -3"
py -3 --version >nul 2>&1
if errorlevel 1 (
    set "PYTHON_CMD=python"
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python 3 no esta disponible. Instale Python 3.11 o 3.12.
        pause
        exit /b 1
    )
)

if not exist ".venv-t5\Scripts\python.exe" (
    echo [1/4] Creando entorno virtual...
    %PYTHON_CMD% -m venv ".venv-t5"
    if errorlevel 1 goto :fail
)

set "PY=.venv-t5\Scripts\python.exe"
echo [2/4] Instalando dependencias del auditor...
"%PY%" -m pip install --disable-pip-version-check -r "t5\requirements.txt"
if errorlevel 1 goto :fail

echo [3/4] Ejecutando analisis estatico y pruebas dinamicas...
"%PY%" "t5\full.py" --source "monitoreo_salud_publica\monitoreo_salud_publica\app.py" --out "t5\results\windows" --repeats 10
if errorlevel 1 goto :fail

echo [4/4] Comprobando el estado de la prueba dinamica...
"%PY%" -c "import json; p='t5/results/windows/dynamic.json'; d=json.load(open(p,encoding='utf-8')); print('Estado:',d.get('status')); print('Detalle:',d.get('reason') or 'Sin incidencias'); print('Rutas:',len(d.get('routes',[])))"
if errorlevel 1 goto :fail

echo.
echo [OK] Archivos generados en t5\results\windows
echo [INFO] Revise dynamic.json: measured = prueba dinamica completa.
echo [INFO] incomplete_missing_legacy_data = faltan datos heredados.
if exist "t5\results\windows\reporte.html" start "" "t5\results\windows\reporte.html"
pause
exit /b 0

:fail
echo.
echo [ERROR] La auditoria no termino correctamente. Revise el mensaje anterior.
pause
exit /b 1
