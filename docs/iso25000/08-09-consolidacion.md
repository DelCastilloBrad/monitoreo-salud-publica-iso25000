# 8.9. Consolidación de los resultados de la evaluación

## Alcance y trazabilidad

Se evalúa el módulo web `monitoreo_salud_publica/app.py` y sus scripts de arranque, con las salidas CSV y PNG precalculadas del proyecto legado. No se reentrenan modelos ni se evalúa su precisión predictiva. Las pruebas finales de funcionalidad, cobertura y tiempo se ejecutan en el commit `070ff1a2a1ccf00564e6164c76f9bfacf9b3c729` de la rama de evaluación. Pymetrica corresponde al mismo contenido de `app.py` medido en la etapa 2; la comprobación de arranque corresponde al commit `5bb188b99d3f5d68f2dcafb01dc927b70fa8997e`.

Evidencia descargable en GitHub Actions: [métricas estructurales de la etapa 2](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36368796296), [pruebas finales de funcionalidad, cobertura y tiempos](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36371920353) y [arranque en dos sistemas de la etapa 4](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36370927427). Cada ejecución conserva artefactos separados para Ubuntu y Windows con JSON, XML y registros de prueba.

| Indicador | Valor obtenido | Unidad | Evidencia y alcance |
|---|---:|---|---|
| IND-01, funciones observadas | 5/5 vistas previstas responden; 3/3 escenarios de filtro regional aprobados | vistas y escenarios | [Pruebas finales](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36371920353), `functional.xml` y `tests/test_real_outputs.py`. Es comprobación de las funciones seleccionadas, no inventario exhaustivo de todos los requisitos. |
| IND-02, correspondencia CSV–interfaz | 18/18 valores seleccionados coinciden | valores comprobados | [Pruebas finales](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36371920353), `tests/test_real_outputs.py`: 4 valores de KPI, 10 de severidad/ranking y 4 de pronósticos. Se inspeccionan filas seleccionadas de ambos grupos; no todos los registros del CSV. |
| IND-03, tiempo medio de respuesta | Véase tabla por ruta y sistema | ms/petición | [Pruebas finales](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36371920353), `response_times.json`. Flask Test Client dentro del proceso, 30 mediciones por ruta después de 3 calentamientos. |
| IND-04, ejecución satisfactoria de solicitudes | Ubuntu 150/150; Windows 150/150, todas HTTP 200 | peticiones medidas | [Pruebas finales](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36371920353), `response_times.json`. Son solicitudes secuenciales controladas, no disponibilidad en producción. |
| IND-05, cobertura de sentencias de `app.py` | Ubuntu y Windows: 87/91 = 95,60 % | sentencias | [Pruebas finales](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36371920353), `coverage.json` y `coverage.txt`. Las 19 pruebas pasan en cada sistema. |
| Complejidad ciclomática agregada | 22; 139 LLOC analizadas | valor y líneas lógicas | [Pymetrica](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36368796296), `pymetrica.json`. La razón 139/22 = 6,32 LLOC por punto de complejidad activa una alerta de umbral de Pymetrica. |
| Volumen de Halstead | 3888,31 | valor de la herramienta | [Pymetrica](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36368796296), `pymetrica.json`. |
| Maintainability cost | 22,28 | valor de la herramienta | [Pymetrica](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36368796296), `pymetrica.json`; no equivale a un porcentaje de mantenibilidad. |
| Instability de Pymetrica | 0,00 para la raíz | índice reportado | [Pymetrica](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36368796296), `pymetrica.json`. El análisis de un único archivo Python no permite concluir que el sistema completo tenga bajo acoplamiento. |
| IND-06, instalación y arranque por sistema | 2/2: Ubuntu 24.04 y Windows Server 2022 | entornos previstos | [Etapa 4](https://github.com/DelCastilloBrad/monitoreo-salud-publica-iso25000/actions/runs/36370927427), `portability.json` y `portability.log`: scripts originales, instalación, servidor local y GET `/` y `/ranking` con HTTP 200. La apertura gráfica del navegador no se comprobó. |
| Usabilidad | Sin valor experimental | — | Falta ejecutar y documentar la revisión heurística propuesta; no se le asigna una puntuación. |

El desglose de IND-02 cuenta **campos visibles**, no afirmaciones individuales de Pytest: dos fechas y dos cantidades de casos; por grupo, año, HR, CFR, región y frecuencia top-3; por grupo, nombre de modelo y MAE. Las cadenas completas de las celdas se comprueban contra el CSV correspondiente. Un resultado de 18/18 describe únicamente esa muestra.

### IND-03. Detalle de tiempo por vista

| Ruta | Ubuntu: media | Ubuntu: p95 | Windows: media | Windows: p95 |
|---|---:|---:|---:|---:|
| `/` | 5,248 | 5,559 | 10,188 | 10,887 |
| `/regional` | 0,955 | 1,012 | 1,220 | 1,305 |
| `/severidad` | 1,436 | 1,545 | 1,768 | 1,875 |
| `/ranking` | 1,561 | 1,635 | 2,023 | 2,287 |
| `/pronosticos` | 1,541 | 1,641 | 1,933 | 2,037 |

Todas las cifras están en milisegundos; p95 se calcula por rango más cercano sobre las 30 mediciones de cada ruta. Los tiempos excluyen red, navegador y concurrencia; tampoco son tiempos de carga del modelo. Los runners tienen cuatro CPU lógicas, Python 3.11.16 en Ubuntu y 3.11.9 en Windows. El entorno final registra Flask 3.1.3, pandas 3.0.6, Pytest 9.1.1 y Coverage.py 7.16.2.

### Interpretación y trabajo pendiente

La cobertura aumenta desde 47/91 (51,65 %) con las siete pruebas iniciales hasta 87/91 (95,60 %) con 19 pruebas y las salidas reales. Las cuatro sentencias restantes ejecutan el bloque `if __name__ == "__main__"` y quedan fuera de la instrumentación de Pytest; los scripts de la etapa 4 sí arrancan el servidor y verifican las dos rutas por HTTP. Esta evidencia de arranque no suma sentencias a Coverage.py.

La evaluación respalda la funcionalidad seleccionada, la cobertura, la medición en proceso y la instalación/arranque en los dos entornos especificados. Para cerrar los indicadores más amplios del informe se requiere una matriz completa de requisitos para IND-01, comparación de la totalidad de datos si se pretende extrapolar IND-02, una revisión heurística para usabilidad y ensayos adicionales si se desea medir navegación gráfica, red o concurrencia. No se calcula el índice global ponderado del informe: faltan la medida de usabilidad y reglas explícitas de normalización de las métricas para aplicar sus pesos sin inventar puntuaciones.
