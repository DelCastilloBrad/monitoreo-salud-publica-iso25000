# Módulo de Monitoreo y Vigilancia — Salud Pública

Aplicación web en Flask para consultar resultados de vigilancia de infecciones respiratorias agudas y neumonía en el Perú. Presenta indicadores, vistas regionales, severidad, rankings y pronósticos para menores de cinco años y adultos mayores de 60 años.

El módulo utiliza las tablas CSV y figuras PNG generadas por el proyecto `ISPySA-Pneumonia-main`. La interfaz no vuelve a entrenar los modelos ni recalcula sus predicciones.

## Componentes

- `monitoreo_salud_publica/`: aplicación Flask, plantillas y archivos estáticos.
- `ISPySA-Pneumonia-main/`: proyecto de análisis y salidas precalculadas que consume la interfaz.
- `ejecutar_monitoreo.bat` y `ejecutar_monitoreo1.sh`: scripts de instalación y arranque para Windows y Linux.
- En la rama [`evaluacion-iso25000-etapas-1-2`](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/tree/evaluacion-iso25000-etapas-1-2) se encuentran además las pruebas, los scripts de medición y los flujos de GitHub Actions.

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
