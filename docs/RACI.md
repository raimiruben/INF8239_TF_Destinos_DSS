# Distribución formal de responsabilidades (RACI)

R = responsable (hace) · A = rinde cuentas (aprueba, exactamente uno) · C = consultado · I = informado.
Regla de la ficha TF.31: **cada persona posee al menos un entregable y revisa otro**.

| Paquete / actividad | Raimi | Mario | Victoria | Alexis |
|---|---|---|---|---|
| 1 · Gobernanza, adquisición y contrato de datos (`data.py`, `prepare_data.py`, `data/README.md`) | **A/R** | I | C | I |
| 2 · Auditoría, preparación y prevención de fuga (partición temporal, `DATASET_CARD.md`) | **A/R** | C | C | I |
| 3 · Baseline y modelos candidatos (`models.py`) | C (revisa PR) | **A/R** | C | I |
| 4 · Evaluación, errores, subgrupos y Green AI (`evaluate.py`, `train_evaluate.py`) | I | C (revisa PR) | **A/R** | C |
| 5 · Reglas, prioridades, explicaciones y abstención (`dss.py`, `configs/dss.yml` sección dss) | C | I | C (revisa PR) | **A/R** |
| 6 · Aplicación Streamlit e integración (`app.py`) | I | C | C | **A/R** |
| 7a · Pruebas de cada módulo (`tests/test_<módulo>.py`) | R (data) | R (models) | R (evaluate) | **A**/R (dss, integración) |
| 7b · CI (`.github/workflows/ci.yml`) | C | I | I | **A/R** |
| 7c · Model Card | C | R | **A/R** | C |
| 7d · Informe técnico, README y registro de riesgos | **A/R** | R (sección 3) | R (secciones 4-5) | R (secciones 6-7) |
| Declaración de IA (cada uno completa su parte) | **A**/R | R | R | R |
| Revisión de PR (par asignado) | revisa Mario | revisa Victoria | revisa Alexis | revisa Raimi |
| Demostración integrada | R (datos) | R (modelos) | R (evidencia) | **A**/R (app) |

## Pruebas por responsable (17 en total; mínimo exigido 8)

| Archivo | Pruebas | Responsable |
|---|---|---|
| `tests/test_data.py` | 3 (contrato válido y mapeo de ciudades, contrato rechaza datos inválidos, partición sin fuga) | Raimi |
| `tests/test_models.py` | 5 (3 parametrizadas de rango/cobertura, contexto cambia ranking, intereses y exclusión de vistos) | Mario |
| `tests/test_evaluate.py` | 3 (métricas calculadas a mano, objetivos sin historial, subgrupos pequeños no interpretables) | Victoria |
| `tests/test_dss.py`, `tests/test_integration.py` | 6 (STOP por cobertura, abstención y explicación, diversidad y restricciones imposibles, revisión por poca evidencia, flujo real de punta a punta, app compila) | Alexis |

## Defensa individual

Cada integrante debe poder **ejecutar su módulo y sus pruebas** en vivo y explicar sus decisiones:
Raimi (contrato, mapeo de ciudades, corte temporal), Mario (suavizado y pesos de los modelos), Victoria
(unidad de evaluación, bootstrap, subgrupos, Green AI), Alexis (estados GO/REVIEW/ABSTAIN/STOP y umbrales).
