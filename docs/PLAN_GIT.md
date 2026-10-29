# Plan de trabajo en Git (28–31 oct 2026)

La rúbrica asigna 3 puntos individuales a **issues, commits sustantivos, ramas, pull requests y revisiones de pares**.
Cada integrante sube **su módulo desde su propia cuenta**, en su propia rama, con su PR revisado por el par asignado.

## 1 · Raimi crea el repositorio (hoy)

1. GitHub → New repository `INF8239_TF_Destinos_DSS` (público o privado con acceso del profesor).
2. Settings → Collaborators: invitar a Mario, Victoria y Alexis.
3. Settings → Branches → regla para `main`: *Require a pull request before merging* + *Require 1 approval*.
4. Primer commit en `main` con el esqueleto común (todo **excepto** los módulos de los demás):

```powershell
git init; git branch -M main
git add pyproject.toml uv.lock .gitignore README.md configs/ data/README.md docs/RACI.md docs/PLAN_GIT.md docs/RISK_REGISTER.md docs/AI_USE_DECLARATION.md src/tourism_dss/__init__.py
git commit -m "chore: estructura inicial, alcance, RACI y registro de riesgos"
git remote add origin https://github.com/<usuario>/INF8239_TF_Destinos_DSS.git
git push -u origin main
```

## 2 · Issues iniciales (uno por paquete; asignar a su responsable)

| # | Título | Responsable | Rama |
|---|---|---|---|
| 1 | Contrato de datos, mapeo de ciudades y partición temporal | Raimi | `feat/datos-contrato` |
| 2 | Baseline de popularidad y modelos M1 (contexto) y M2 (híbrido) | Mario | `feat/modelos` |
| 3 | Reglas DSS, explicación, abstención y app Streamlit | Alexis | `feat/dss-app` |
| 4 | Evaluación P@k, cobertura, subgrupos, errores y Green AI | Victoria | `feat/evaluacion` |
| 5 | CI con GitHub Actions | Alexis | `ci/github-actions` |
| 6 | Model Card | Victoria | `docs/model-card` |
| 7 | Informe técnico y declaración de IA | Raimi (+ todos) | `docs/informe` |

## 3 · Flujo por integrante

```powershell
git checkout main; git pull
git checkout -b feat/<rama>
# copiar SOLO los archivos de su paquete (ver tabla de README.md), ejecutar y entender
uv run pytest -q tests/test_<modulo>.py
git add <archivos del paquete>
git commit -m "feat(<modulo>): <qué hace>  (closes #<issue>)"
git push -u origin feat/<rama>
# GitHub: abrir Pull Request, asignar como revisor al par del RACI
```

Orden de integración (por dependencias del código): **datos → modelos → DSS/app → evaluación → CI y docs**
(`train_evaluate.py` importa el DSS, por eso la evaluación entra después).

| PR | Archivos que sube cada uno |
|---|---|
| #1 Raimi | `src/tourism_dss/data.py`, `scripts/prepare_data.py`, `tests/conftest.py`, `tests/test_data.py`, `docs/DATASET_CARD.md`, `reports/data_audit.json` |
| #2 Mario | `src/tourism_dss/models.py`, `tests/test_models.py` |
| #3 Alexis | `src/tourism_dss/dss.py`, `app.py`, `tests/test_dss.py`, `tests/test_integration.py` |
| #4 Victoria | `src/tourism_dss/evaluate.py`, `scripts/train_evaluate.py`, `scripts/diagnose_subgroup.py`, `tests/test_evaluate.py`, `reports/*` restantes |
| #5 Alexis | `.github/workflows/ci.yml` |
| #6 Victoria | `docs/MODEL_CARD.md` |
| #7 Raimi (+ todos) | `docs/INFORME_TECNICO.md`, completar `docs/AI_USE_DECLARATION.md` |

El revisor ejecuta las pruebas, deja al menos un comentario técnico y aprueba; luego el autor hace *merge*.
Preferible 2–3 commits pequeños por persona (código, pruebas, documentación) a uno gigante.

## 4 · Calendario

| Día | Entregable |
|---|---|
| Mié 28 | Repo, colaboradores, issues, PR #1 (datos) |
| Jue 29 | PR #2 (modelos) y PR #3 (DSS + app) revisados y fusionados |
| Vie 30 | PR #4 (evaluación), CI, Model Card, informe; `train_evaluate.py` y la app corren en `main`; ensayo de demostración con un escenario nuevo |
| Sáb 31 | Revisión final, `git tag -a v1.0-final -m "Entrega final"`, `git push --tags`, entrega en la plataforma |
