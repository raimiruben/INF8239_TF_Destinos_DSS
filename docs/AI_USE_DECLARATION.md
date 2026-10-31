# Declaración de uso de IA generativa

**Proyecto:** DSS de priorización de atracciones turísticas · INF-8239 Ciencia de Datos II · UASD · Tema 31
**Equipo:** Raimi De Jesús, Mario Feliz, Victoria Beltré y Alexis De La Cruz
**Herramienta:** Claude (Anthropic), asistente conversacional usado por Raimi De Jesús del 22 al 30 de octubre de 2026.

## 1\. Alcance del uso

La IA generativa tuvo un papel **importante** en este proyecto. El equipo lo declara de forma explícita:

|Componente|Quién lo produjo|Papel del equipo|
|-|-|-|
|Evaluación de datasets|Claude, a partir de los PDF del mandato y del tema y de los datasets propuestos por el equipo|El equipo propuso el dataset de Kaggle *Travel \& Tourism* y aportó el de Mendeley; decidió usar el de Mendeley tras revisar el análisis|
|Código (`src/tourism\_dss/`, `scripts/`, `app.py`)|Generado por Claude|Cada integrante copió su módulo, lo ejecutó con los datos reales y lo subió desde su cuenta|
|Pruebas automáticas (`tests/`, 17 pruebas)|Generadas por Claude|Cada integrante ejecutó las pruebas de su módulo antes de abrir su PR|
|Configuración (`configs/dss.yml`, `pyproject.toml`, CI)|Generada por Claude|Sin cambios del equipo|
|Reportes (`reports/`)|Generados por los scripts al ejecutarlos el equipo|Raimi generó `data\_audit.json`; Victoria generó los reportes de evaluación|
|Ayuda en la organización del trabajo en Git (repo, issues, ramas, PR, revisiones)|Se usó Claude como guía |Ejecutado por cada integrante en su computadora y en GitHub|

## 2\. Prompts relevantes (resumen)

1. "Analiza ese dataset y dime si cumple con los requisitos" (dataset de Kaggle propuesto por un integrante), y luego el análisis del dataset de Mendeley (9 tablas).



## 3\. Verificaciones humanas realizadas

|Integrante|Módulo|Qué ejecutó o revisó|Cambios propios|
|-|-|-|-|
|Raimi|Datos (#1) e informe (#7)|Ejecutó `prepare\_data.py` (`contract\_status: valid`, 52.930 interacciones, 30 atracciones), `pytest tests/test\_data.py` (3 passed) y comprobó que las huellas SHA-256 de los 9 archivos coincidían con las documentadas. Creó el repo, los issues y la protección de `main`. Revisó y aprobó el PR de modelos y el de CI ejecutando las pruebas de esas ramas. Ejecutó el pipeline completo y la app en `main`.|Ninguno al código; agregó el registro real de revisiones al RACI|
|Mario|Modelos (#2)|Siguió la guía: ejecutó `prepare\_data.py` y `pytest tests/test\_data.py tests/test\_models.py` antes de abrir su PR. Revisó los PR de evaluación y Model Card.|Ninguno|
|Victoria|Evaluación (#4) y Model Card (#6)|Revisó el PR de datos ejecutando `prepare\_data.py` y `test\_data.py`. Siguió la guía: ejecutó `train\_evaluate.py`, `diagnose\_subgroup.py` y `pytest` (17 passed), y generó los reportes de evaluación. Revisó el PR del DSS.|Ninguno|
|Alexis|DSS, app (#3) y CI (#5)|Siguió la guía: ejecutó `prepare\_data.py` y `pytest` (14 passed) antes de abrir sus PR. Revisó el PR del informe.|Ninguno|

Las verificaciones consistieron en **ejecutar** el código y comprobar que las salidas coincidían con las esperadas. El equipo no auditó línea por línea el código generado. Cada integrante se compromete a entender y poder explicar su módulo para la defensa individual.

## 4\. Errores detectados y correcciones

|Error|Cómo se detectó|Corrección|
|-|-|-|
|La tabla `City` no corresponde a `Item.AttractionCityId` (el Id 1 apunta a Douala, Camerún)|Auditoría de datos|Mapeo documentado 1 = Bali, 2 = Malang, 3 = Yogyakarta, protegido por una prueba de contrato|
|Primera explicación de la caída del subgrupo África ("el componente de continente perjudica al grupo")|Al probar la hipótesis quitando el continente, el resultado no cambió (0,658)|Se descartó y se reemplazó por el diagnóstico de deriva del contexto "parejas" en Bali (`scripts/diagnose\_subgroup.py`)|
|Prueba de integración que exigía que la primera recomendación coincidiera con los intereses|Falló con los datos reales (domina Bromo Tengger Semeru, de la misma familia temática)|Se cambió para exigir que al menos una de las tres coincida|
|Evaluación lenta (\~7 min)|Al ejecutar el pipeline|Caché de componentes de contexto; mismos resultados en \~1 min|
|Conteo esperado de archivos del zip (51) en la guía de Raimi|Al descomprimir salieron 38|El 51 incluía carpetas; los 38 archivos eran correctos|
|Ejecución de un script escribiendo solo su nombre (`scripts/prepare\_data.py`)|Error "is not recognized" en PowerShell durante la revisión del PR de datos|Se ejecuta con `uv run python scripts/prepare\_data.py`; se agregó la advertencia a las guías|
|El revisor del PR de datos no fue el del RACI|Alexis aún no tenía acceso al repo|Revisó Victoria; quedó registrado en el RACI|

## 5\. Límites y responsabilidad

* Los resultados numéricos provienen de ejecutar el código sobre los datos reales; no fueron escritos a mano.
* Las conclusiones del informe (recomendar el uso con revisión humana, abstención sin perfil y los límites del DSS) fueron propuestas por la IA y aceptadas por el equipo.
* El equipo asume la responsabilidad del contenido entregado y declara que se utilizó la IA en la elaboración de este trabajo.

