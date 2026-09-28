@echo off
REM =========================================================================
REM  Modulo de Monitoreo y Vigilancia - Salud Publica (IRA / Neumonia Peru)
REM  Curso: Calidad de Software - Trabajo de Introduccion
REM  Equipo: Viuda Negra 2.0
REM
REM  Este script:
REM   1) Verifica que Python este instalado
REM   2) Crea un entorno virtual (venv) si no existe
REM   3) Instala las dependencias del modulo nuevo (Flask, pandas)
REM   4) Verifica que el proyecto legado ISPySA-Pneumonia-main este presente
REM   5) Levanta el servidor y abre el navegador en http://127.0.0.1:5000
REM =========================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo  Modulo de Monitoreo y Vigilancia de Salud Publica
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro Python en el PATH.
    echo Instale Python 3.10+ desde https://www.python.org/downloads/
    echo y marque la opcion "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

if not exist "ISPySA-Pneumonia-main\outputs\tables" (
    echo [ERROR] No se encontro el proyecto legado.
    echo Coloque la carpeta "ISPySA-Pneumonia-main" en esta misma ubicacion:
    echo   %cd%\ISPySA-Pneumonia-main
    pause
    exit /b 1
)

if not exist "venv" (
    echo [1/3] Creando entorno virtual...
    python -m venv venv
)

echo [2/3] Instalando dependencias del modulo de monitoreo...
call venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r monitoreo_salud_publica\requirements.txt

echo [3/3] Iniciando el servidor...
echo.
echo   Abriendo http://127.0.0.1:5000 en el navegador...
echo   Para detener el servidor, cierre esta ventana o presione CTRL+C.
echo.

start "" http://127.0.0.1:5000/
cd monitoreo_salud_publica
python app.py

pause
