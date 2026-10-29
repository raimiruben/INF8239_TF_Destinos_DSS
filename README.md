# DSS · Priorización de atracciones turísticas (INF-8239 · Tema 31)

Sistema de soporte a decisiones (**Modalidad B**) que ayuda a un **planificador de viajes** a priorizar
atracciones en Bali, Malang y Yogyakarta (Indonesia) según el **contexto** del viaje (modo de viaje, origen),
el **contenido** (tipos de atracción de interés) y la calidad observada, con reglas explícitas, explicación,
abstención y revisión humana.

- Asignatura: INF-8239 Ciencia de Datos II · UASD · Trabajo final
- Equipo (4): Raimi De Jesús, Mario, Victoria, Alexis · reparto formal en [docs/RACI.md](docs/RACI.md)
- Alcance comprometido (4–5 integrantes): baseline + 2 modelos, ≥ 8 pruebas (hay 17), documentación, demostración
  y distribución formal de responsabilidades.

## Ejecución (Windows PowerShell o Linux)

```powershell
uv sync                                    # crea .venv con las versiones de uv.lock
# 1) Descargar las 9 tablas .xlsx a data\raw\ (ver data\README.md)
uv run python scripts/prepare_data.py      # contrato de datos + data/processed + reports/data_audit.json
uv run python scripts/train_evaluate.py    # ajuste (2018), prueba (2019-2022), subgrupos, Green AI (~1-2 min)
uv run python scripts/diagnose_subgroup.py # diagnóstico del subgrupo África
uv run pytest -q                           # 17 pruebas (las de integración se omiten si no hay datos reales)
uv run streamlit run app.py                # interfaz del DSS
```

## Estructura

| Ruta | Paquete de trabajo | Responsable |
|---|---|---|
| `src/tourism_dss/data.py`, `scripts/prepare_data.py`, `data/README.md`, `docs/DATASET_CARD.md` | 1-2 · Gobernanza, contrato, auditoría, partición sin fuga | Raimi |
| `src/tourism_dss/models.py` | 3 · Baseline y modelos candidatos | Mario |
| `src/tourism_dss/evaluate.py`, `scripts/train_evaluate.py`, `scripts/diagnose_subgroup.py`, `docs/MODEL_CARD.md` | 4 · Evaluación, errores, subgrupos, Green AI | Victoria |
| `src/tourism_dss/dss.py`, `app.py`, `.github/workflows/ci.yml` | 5-6 · Reglas, explicación, abstención, app e integración | Alexis |
| `tests/` | 7 · Cada responsable mantiene las pruebas de su módulo | Todos |
| `configs/dss.yml` | Umbrales y pesos versionados (cambios solo por PR) | Todos |

## Resultados en prueba temporal (2019–2022, 4.731 viajes)

| Modelo | P@3 | Hit@3 | NDCG@3 | Cobertura@3 | P@5 | Hit@5 | NDCG@5 | Cobertura@5 |
|---|---|---|---|---|---|---|---|---|
| Baseline · popularidad | **0,270** | **0,732** | 0,553 | 0,57 | 0,178 | 0,791 | 0,580 | 0,70 |
| M1 · contexto (modo + origen) | 0,266 | 0,720 | 0,590 | 0,67 | 0,182 | 0,806 | 0,629 | 0,83 |
| M2 · híbrido contenido + contexto | 0,266 | 0,721 | **0,590** | **0,80** | **0,182** | **0,809** | **0,630** | **0,97** |

El baseline gana en Hit@3 por ~1 punto; el híbrido ordena mejor (NDCG@3 +0,037, IC 95 % [0,032; 0,043]),
cubre más catálogo y gana con k = 5. Análisis completo en [docs/INFORME_TECNICO.md](docs/INFORME_TECNICO.md).

## Documentación

[Informe técnico](docs/INFORME_TECNICO.md) · [Model Card](docs/MODEL_CARD.md) · [Dataset Card](docs/DATASET_CARD.md) ·
[Registro de riesgos](docs/RISK_REGISTER.md) · [RACI](docs/RACI.md) · [Plan Git](docs/PLAN_GIT.md) ·
[Declaración de IA](docs/AI_USE_DECLARATION.md)

## Datos y licencia

Huda, C. (2023). *Tourism Dataset*. Mendeley Data, V1. https://doi.org/10.17632/h58s544674.1 — uso de investigación,
no comercial. Los archivos crudos no se versionan; ver [data/README.md](data/README.md).
