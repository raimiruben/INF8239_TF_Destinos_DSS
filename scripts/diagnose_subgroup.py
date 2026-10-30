"""Paquete 4 · Diagnóstico de la caída del híbrido en viajeros de África (n = 120 viajes de prueba).

Hipótesis evaluadas:
  H1 · el componente de continente perjudica al grupo  -> se prueba w_mode = 1 (sin continente)
  H2 · deriva temporal del contexto "parejas" en Bali   -> cuota por año de las atracciones intercambiadas
  H3 · una ventana reciente de entrenamiento lo corrige -> entrenar solo con 2016-2018

Uso: uv run python scripts/diagnose_subgroup.py   (salida: reports/subgroup_diagnostic.json)
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tourism_dss import load_config  # noqa: E402
from tourism_dss.data import temporal_split  # noqa: E402
from tourism_dss.evaluate import build_trips, evaluate_model  # noqa: E402
from tourism_dss.models import HybridContentContext, PopularityBaseline  # noqa: E402


def run(model, trips, k=3):
    s, d = evaluate_model(model, trips, k, 30)
    africa = d["continent"] == "Africa"
    couples = d["mode"] == "Couples"
    return {"hit@3": s["hit@3"], "ndcg@3": s["ndcg@3"], "coverage@3": s["coverage@3"],
            "africa_hit@3": round(float(d.loc[africa, "hit@3"].mean()), 3),
            "africa_couples_hit@3": round(float(d.loc[africa & couples, "hit@3"].mean()), 3),
            "couples_hit@3": round(float(d.loc[couples, "hit@3"].mean()), 3)}


def main():
    cfg = load_config()
    inter = pd.read_csv(ROOT / "data" / "processed" / "interactions.csv")
    att = pd.read_csv(ROOT / "data" / "processed" / "attractions.csv")
    train, val, test = temporal_split(inter, cfg["split"]["train_end"], cfg["split"]["val_end"])
    hist = pd.concat([train, val])
    trips = build_trips(test, hist)
    w = tuple(json.loads((ROOT / "reports" / "metrics.json").read_text(encoding="utf-8"))["meta"]["best_weights"])

    out = {
        "baseline": run(PopularityBaseline().fit(hist, att), trips),
        "m2_actual": run(HybridContentContext(weights=w).fit(hist, att), trips),
        "H1_m2_sin_continente": run(HybridContentContext(w_mode=1.0, weights=w).fit(hist, att), trips),
    }
    # H3 · ventana reciente (el historial de visitas y perfiles se conservan completos)
    full = HybridContentContext(weights=w).fit(hist, att)
    recent = HybridContentContext(weights=w).fit(hist[hist["VisitYear"] >= 2016], att)
    recent.history, recent.user_profiles = full.history, full.user_profiles
    out["H3_m2_ventana_2016_2018"] = run(recent, trips)

    # H2 · cuota anual entre parejas en Bali de las atracciones que el contexto intercambia
    bali_couples = inter[(inter["city"] == "Bali") & (inter["mode"] == "Couples")]
    share = (bali_couples.groupby("VisitYear")["AttractionId"].value_counts(normalize=True)
             .unstack(fill_value=0)[[841, 737]].round(3))
    out["H2_cuota_parejas_bali"] = {"Waterbom Bali (841)": share[841].to_dict(),
                                    "Tanah Lot Temple (737)": share[737].to_dict()}
    (ROOT / "reports" / "subgroup_diagnostic.json").write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                                               encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
