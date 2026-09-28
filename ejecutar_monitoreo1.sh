#!/bin/bash
# =========================================================================
#  Modulo de Monitoreo y Vigilancia - Salud Publica (IRA / Neumonia Peru)
#  Curso: Calidad de Software - Trabajo de Introduccion
#  Equipo: Viuda Negra 2.0
# =========================================================================

# Ir al directorio donde está guardado este script
cd "$(dirname "$0")"

echo -e "\n============================================================"
echo " Modulo de Monitoreo y Vigilancia de Salud Publica"
echo -e "============================================================\n"

# 1. Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] No se encontro Python 3."
    echo "Instalelo ejecutando: sudo apt update && sudo apt install python3 python3-venv python3-pip"
    read -p "Presione Enter para salir..."
    exit 1
fi

# 2. Verificar que el proyecto legado exista
if [ ! -d "ISPySA-Pneumonia-main/outputs/tables" ]; then
    echo "[ERROR] No se encontro el proyecto legado."
    echo "Coloque la carpeta 'ISPySA-Pneumonia-main' en esta misma ubicacion:"
    echo "   $(pwd)/ISPySA-Pneumonia-main"
    read -p "Presione Enter para salir..."
    exit 1
fi

# 3. Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "[1/3] Creando entorno virtual..."
    python3 -m venv venv
fi

echo "[2/3] Instalando dependencias del modulo de monitoreo..."
# Activar entorno virtual en Linux
source venv/bin/activate
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet -r monitoreo_salud_publica/requirements.txt

echo -e "[3/3] Iniciando el servidor...\n"
echo "  Abriendo http://127.0.0.1:5000 en el navegador..."
echo -e "  Para detener el servidor, presione CTRL+C en esta terminal.\n"

# Abrir el navegador en Pop!_OS (equivalente a start en Windows)
xdg-open "http://127.0.0.1:5000/" &

# Iniciar la aplicación
cd monitoreo_salud_publica
python3 app.py

read -p "Presione Enter para continuar..."
