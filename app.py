"""Paquete 6 · Interfaz Streamlit del DSS de destinos turísticos.

Uso: uv run streamlit run app.py
Requiere: scripts/prepare_data.py y scripts/train_evaluate.py ejecutados (genera models/ y reports/).
"""

import json
import pickle
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from tourism_dss import load_config  # noqa: E402
from tourism_dss.dss import MODE_ES, TourismDSS  # noqa: E402
from tourism_dss.models import Context  # noqa: E402

STATUS = {
    "GO": ("🟢 GO", "Evidencia suficiente. El planificador valida y decide."),
    "REVIEW": ("🟡 REVISIÓN", "Se entrega la lista, pero hay advertencias que el planificador debe revisar."),
    "ABSTAIN": ("⚪ ABSTENCIÓN", "El sistema no personaliza: falta perfil del viajero. La lista es general."),
    "STOP": ("🔴 DETENIDO", "No se puede recomendar con estos datos o restricciones. Escalar a un asesor."),
}

st.set_page_config(page_title="DSS Destinos turísticos", page_icon="🧭", layout="wide")


@st.cache_resource
def load_model():
    path = ROOT / "models" / "m2_hibrido.pkl"
    if not path.exists():
        st.error("Falta models/m2_hibrido.pkl. Ejecute: uv run python scripts/prepare_data.py y "
                 "uv run python scripts/train_evaluate.py")
        st.stop()
    with open(path, "rb") as fh:
        return pickle.load(fh)


def load_metrics():
    p = ROOT / "reports" / "metrics.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


cfg = load_config()
model = load_model()
dss = TourismDSS(model, cfg["dss"])
att = model.attractions
metrics = load_metrics()

st.title("🧭 DSS · Priorización de atracciones turísticas")
st.caption("Apoyo al planificador de viajes · Bali, Malang y Yogyakarta (Indonesia) · Datos TripAdvisor 2013–2022 "
           "(Huda, 2023, Mendeley Data, DOI 10.17632/h58s544674.1) · INF-8239 Tema 31")

with st.sidebar:
    st.header("Escenario del viaje")
    city = st.selectbox("Ciudad", sorted(model.city_items) + ["Otra ciudad (fuera de cobertura)"])
    mode = st.selectbox("Modo de viaje", ["(no indicado)"] + list(MODE_ES),
                        format_func=lambda m: m if m.startswith("(") else f"{m} ({MODE_ES[m]})")
    continent = st.selectbox("Continente de origen del viajero",
                             ["(no indicado)", "Africa", "America", "Asia", "Australia & Oceania", "Europe"])
    types = sorted(att["type"].unique())
    interests = st.multiselect("Intereses declarados (tipos de atracción)", types)
    excluded = st.multiselect("Excluir tipos", [t for t in types if t not in interests])
    k = st.slider("Número de atracciones a priorizar", 1, 6, cfg["dss"]["default_k"])
    user_id = st.number_input("Id de viajero con historial (opcional, 0 = nuevo)", min_value=0, step=1, value=0)

ctx = Context(city=city, mode=None if mode.startswith("(") else mode,
              continent=None if continent.startswith("(") else continent,
              user_id=int(user_id) or None, interests=interests)
result = dss.recommend(ctx, k=k, exclude_types=excluded or None)

label, meaning = STATUS[result.status]
c1, c2 = st.columns([1, 3])
c1.markdown(f"**Estado de la recomendación**\n\n### {label}")
c2.info(f"**{meaning}**  \nPerfil usado: {result.profile_source}. Reglas aplicadas: {', '.join(result.rules_applied)}.")
for w in result.warnings:
    st.warning(w)

if result.items:
    st.subheader("Prioridades sugeridas")
    for i, item in enumerate(result.items, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {item.name}** · {item.type} · puntaje {item.score:.2f}")
            st.markdown("Por qué: " + "; ".join(item.reasons) + ".")
            for f in item.flags:
                st.caption(f"⚠️ {f}")
    with st.expander("Ver como tabla"):
        st.dataframe(result.to_frame(), hide_index=True, use_container_width=True)

    if ctx.city in model.city_items:
        with st.expander("Alternativas no priorizadas (para revisión humana)"):
            comps = model.components(ctx)
            scores = model.score(ctx)
            alt = pd.DataFrame({"atracción": att.loc[scores.index, "name"], "tipo": att.loc[scores.index, "type"],
                                "puntaje": scores.round(3), "contexto": comps["context"].round(3),
                                "contenido": comps["content"].round(3), "calidad": comps["quality"].round(3),
                                "visitas": model.pop.loc[scores.index]}).sort_values("puntaje", ascending=False)
            st.dataframe(alt, hide_index=True, use_container_width=True)

st.divider()
st.subheader("Qué representa este resultado y qué no permite concluir")
st.markdown(
    "- **Representa** una priorización de atracciones de la ciudad elegida según: popularidad en viajes con el mismo "
    "modo y origen (contexto), afinidad con los tipos de interés (contenido) y calificación media (calidad).\n"
    "- **No permite concluir** que el viajero disfrutará la atracción, ni nada sobre precios, horarios, accesibilidad, "
    "seguridad o clima: esos datos no existen en la fuente.\n"
    "- Los datos vienen de reseñas de TripAdvisor (2013–2022); la mayoría son de Bali y de antes de 2020. "
    "Malang y Yogyakarta tienen mucha menos evidencia.\n"
    "- El puntaje es relativo dentro de la ciudad (0–1); no es una probabilidad.\n"
    "- **La decisión final es del planificador**; ante estado REVISIÓN, ABSTENCIÓN o DETENIDO debe intervenir.")

if metrics:
    with st.expander("Evidencia del modelo (prueba temporal 2019–2022)"):
        test = pd.DataFrame(metrics["test"])
        st.dataframe(test[test["k"] == cfg["evaluation"]["primary_k"]], hide_index=True, use_container_width=True)
        st.caption(f"Pesos (contexto, contenido, calidad) elegidos en validación 2018: {metrics['meta']['best_weights']} · "
                   f"Viajes de prueba: {metrics['meta']['test_trips']} · Generado: {metrics['meta']['date']}. "
                   "El baseline de popularidad sigue siendo competitivo; ver docs/INFORME_TECNICO.md.")
