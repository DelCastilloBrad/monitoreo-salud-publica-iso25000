# Módulo de Monitoreo y Vigilancia — Salud Pública

Aplicación web en Flask para consultar resultados de vigilancia de infecciones respiratorias agudas y neumonía en el Perú. Presenta indicadores, vistas regionales, severidad, rankings y pronósticos para menores de cinco años y adultos mayores de 60 años.

El módulo utiliza las tablas CSV y figuras PNG generadas por el proyecto `ISPySA-Pneumonia-main`. La interfaz no vuelve a entrenar los modelos ni recalcula sus predicciones.

## Componentes

- `monitoreo_salud_publica/`: aplicación Flask, plantillas y archivos estáticos.
- `ISPySA-Pneumonia-main/`: proyecto de análisis y salidas precalculadas que consume la interfaz.
- `ejecutar_monitoreo.bat` y `ejecutar_monitoreo1.sh`: scripts de instalación y arranque para Windows y Linux.
- En la rama [`evaluacion-iso25000-etapas-1-2`](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/tree/evaluacion-iso25000-etapas-1-2) se conservan las evaluaciones anteriores. En `main` están el auditor del TP5 (`t5/full.py`), el lanzador para Windows y un workflow centralizado de GitHub Actions.

## Ejecutar el módulo

Para reproducir la evaluación, utiliza la rama `evaluacion-iso25000-etapas-1-2`, donde el módulo y el proyecto heredado están organizados en las rutas esperadas por los scripts. Se requiere Python 3.11 y las salidas del proyecto heredado en `ISPySA-Pneumonia-main/outputs/`.

```bash
git clone https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000.git
cd monitoreo-salud-publica-iso25000
git switch evaluacion-iso25000-etapas-1-2
```

En Linux:

```bash
bash ejecutar_monitoreo1.sh
```

En Windows, ejecuta `ejecutar_monitoreo.bat`. Una vez iniciado el servidor, abre `http://127.0.0.1:5000/`.

> Los scripts originales esperan `monitoreo_salud_publica/` e `ISPySA-Pneumonia-main/` directamente en la raíz. En `main` hay una capa adicional de directorios procedente de la carga inicial; por eso las instrucciones de ejecución apuntan a la rama de evaluación.

## Evaluación de calidad

La rama de evaluación contiene pruebas funcionales, comparación de valores de la interfaz con CSV, medición de cobertura y tiempos de respuesta, análisis estático con PyMetrica y verificación de arranque en Ubuntu y Windows. Los resultados y archivos de evidencia se conservan en las [ejecuciones de GitHub Actions](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions).

Las comprobaciones de la interfaz se realizan sobre salidas precalculadas. Los resultados de prueba describen los escenarios y entornos ensayados; no constituyen una validación clínica de los pronósticos.

## Trabajo Parcial 5: auditoría centralizada (Windows y GitHub Actions)

Esta sección describe la evaluación del código según los indicadores adoptados por el equipo en el TP5 (ISO/IEC 20246:2017 e ISO/IEC 5055:2021). **No modifica `app.py` ni aplica automáticamente correcciones.** El auditor reúne Radon, Pylint, Bandit, PyMetrica, candidatos de eficiencia y pruebas mediante Flask Test Client.

### Opción A — Windows 10/11 (un solo archivo)

**Requisitos:** Git, Python 3.11 o 3.12 de 64 bits (marcar **Add Python to PATH** durante la instalación) y conexión a Internet para instalar dependencias. En PowerShell o CMD:

```bat
git clone https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000.git
cd monitoreo-salud-publica-iso25000
git switch main
git pull --ff-only
ejecutar_auditoria_t5_windows.bat
```

También se puede hacer doble clic en **`ejecutar_auditoria_t5_windows.bat`** desde el Explorador. El archivo crea `.venv-t5`, instala `t5/requirements.txt`, ejecuta el auditor y abre el reporte HTML. Los resultados quedan en **`t5/results/windows/`**:

- `reporte.html`: resumen legible en el navegador.
- `summary.json`: métricas, versiones, commit y alcance.
- `radon_cc.json`, `radon_mi.json`, `radon_raw.json`: complejidad, mantenibilidad y tamaño.
- `pylint.json`, `bandit.json`, `pymetrica.json`: análisis estático.
- `dynamic.json`, `routes.csv`: resultados de rutas, tiempos y lecturas CSV.
- `eficiencia_candidatos.json` y `.csv`: **candidatos**, no defectos confirmados.

**Datos heredados:** para medir el comportamiento real de las rutas, el proyecto `ISPySA-Pneumonia-main` y sus salidas CSV/PNG deben estar disponibles en la ruta esperada por `app.py`: **`monitoreo_salud_publica/ISPySA-Pneumonia-main/outputs/tables/`** y **`.../outputs/figures/`**. Estas salidas no se regeneran mediante el auditor. Si faltan, la ejecución puede producir resultados estáticos y respuestas de respaldo, pero **no debe interpretarse como evaluación dinámica completa**. Compruebe el campo `status` de `t5/results/windows/dynamic.json`: `measured` significa medición con datos heredados; `incomplete_missing_legacy_data` indica ausencia de datos; `failed` indica error. La ruta de la carpeta heredada es relativa al módulo actual, no a la raíz del repositorio.

Para repetir el análisis sin el lanzador, con el entorno ya instalado:

```bat
.venv-t5\Scripts\python.exe t5\full.py --source monitoreo_salud_publica\monitoreo_salud_publica\app.py --out t5\results\windows --repeats 10
```

Si falla la instalación de PyMetrica en un equipo, revise el error de `pip` y la versión de Python antes de atribuirlo a `app.py`.

### Opción B — GitHub Actions (sin instalar herramientas localmente)

1. Abra [Actions](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions).
2. Seleccione **TP5 - Auditoria centralizada** en la barra lateral.
3. Pulse **Run workflow**, seleccione la rama **main** y confirme **Run workflow**.
4. Espere a los trabajos **Ubuntu** y **Windows**. En la ejecución, descargue los archivos **`tp5-evidencias-ubuntu-latest`** y **`tp5-evidencias-windows-latest`** desde **Artifacts**.

El workflow ejecuta el mismo `t5/full.py` en ambos sistemas y conserva reportes separados. **Advertencia:** los runners de GitHub no necesariamente incluyen las salidas precalculadas del proyecto heredado; consulte `dynamic.json` antes de afirmar que las pruebas dinámicas fueron completas. Un trabajo en verde confirma que el proceso de auditoría y la generación de reportes finalizaron, **no** que todos los indicadores cumplan sus umbrales ni que no existan vulnerabilidades.

### Interpretación y trazabilidad

Los tiempos obtenidos con Flask Test Client corresponden a solicitudes **dentro del proceso**, no a latencia de red ni pruebas de carga. Las lecturas CSV contabilizadas no son automáticamente lecturas redundantes. Los candidatos IND-EF-02/03 requieren revisión manual y **IND-EF-04 no debe fijarse en cero** sin validar debilidades distintas. `summary.json` incluye el commit, las versiones de las herramientas y el entorno para facilitar la comparación reproducible.
