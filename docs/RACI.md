# Distribución formal de responsabilidades (RACI)

R = responsable (hace) · A = rinde cuentas (aprueba, exactamente uno) · C = consultado · I = informado.
Regla de la ficha TF.31: **cada persona posee al menos un entregable y revisa otro**.

|Paquete / actividad|Raimi|Mario|Victoria|Alexis|
|-|-|-|-|-|
|1 · Gobernanza, adquisición y contrato de datos (`data.py`, `prepare\_data.py`, `data/README.md`)|**A/R**|I|C|I|
|2 · Auditoría, preparación y prevención de fuga (partición temporal, `DATASET\_CARD.md`)|**A/R**|C|C|I|
|3 · Baseline y modelos candidatos (`models.py`)|C (revisa PR)|**A/R**|C|I|
|4 · Evaluación, errores, subgrupos y Green AI (`evaluate.py`, `train\_evaluate.py`)|I|C (revisa PR)|**A/R**|C|
|5 · Reglas, prioridades, explicaciones y abstención (`dss.py`, `configs/dss.yml` sección dss)|C|I|C (revisa PR)|**A/R**|
|6 · Aplicación Streamlit e integración (`app.py`)|I|C|C|**A/R**|
|7a · Pruebas de cada módulo (`tests/test\_<módulo>.py`)|R (data)|R (models)|R (evaluate)|**A**/R (dss, integración)|
|7b · CI (`.github/workflows/ci.yml`)|C|I|I|**A/R**|
|7c · Model Card|C|R|**A/R**|C|
|7d · Informe técnico, README y registro de riesgos|**A/R**|R (sección 3)|R (secciones 4-5)|R (secciones 6-7)|
|Declaración de IA (cada uno completa su parte)|**A**/R|R|R|R|
|Revisión de PR (par asignado)|revisa Mario|revisa Victoria|revisa Alexis|revisa Raimi|
|Demostración integrada|R (datos)|R (modelos)|R (evidencia)|**A**/R (app)|

## Pruebas por responsable (18 en total; mínimo exigido 8)

|Archivo|Pruebas|Responsable|
|-|-|-|
|`tests/test\_data.py`|3 (contrato válido y mapeo de ciudades, contrato rechaza datos inválidos, partición sin fuga)|Raimi|
|`tests/test\_models.py`|5 (3 parametrizadas de rango/cobertura, contexto cambia ranking, intereses y exclusión de vistos)|Mario|
|`tests/test\_evaluate.py`|3 (métricas calculadas a mano, objetivos sin historial, subgrupos pequeños no interpretables)|Victoria|
|`tests/test\_dss.py`, `tests/test\_integration.py`|7 (STOP por cobertura, explicación tipo vs. familia temática, abstención y explicación, diversidad y restricciones imposibles, revisión por poca evidencia, flujo real de punta a punta, app compila)|Alexis|

## Defensa individual

Cada integrante debe poder **ejecutar su módulo y sus pruebas** en vivo y explicar sus decisiones:
Raimi (contrato, mapeo de ciudades, corte temporal), Mario (suavizado y pesos de los modelos), Victoria
(unidad de evaluación, bootstrap, subgrupos, Green AI), Alexis (estados GO/REVIEW/ABSTAIN/STOP y umbrales).



\## Revisiones realizadas (registro real)



| PR | Autor | Revisor | Nota |

|---|---|---|---|

| #8 Datos | Raimi | Victoria | Revisó Victoria en lugar de Alexis, que aún no tenía acceso al repo |

| Modelos | Mario | Raimi | Según RACI |

| DSS y app | Alexis | Victoria | Según RACI |

| CI | Alexis | Raimi | Según RACI |

| Evaluación | Victoria | Mario | Según RACI |

| Model Card | Victoria | Raimi | Revisó Raimi en lugar de Mario |

| Informe y declaración de IA | Raimi | Victoria | Revisó Victoria en lugar de A lexis |

