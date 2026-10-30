"""Paquetes 3-5 · Ajuste en validación, comparación en prueba, subgrupos, errores, Green AI y estados del DSS.

Uso: uv run python scripts/train_evaluate.py
Salidas: reports/*.json|csv y models/m2_hibrido.pkl
"""

import json
import pickle
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tourism_dss import load_config  # noqa: E402
from tourism_dss.data import temporal_split  # noqa: E402
from tourism_dss.dss import TourismDSS  # noqa: E402
from tourism_dss.evaluate import (bootstrap_diff, build_trips, ctx_from_trip, evaluate_model,  # noqa: E402
                                  green_metrics, subgroup_table)
from tourism_dss.models import ContextPopularity, HybridContentContext, PopularityBaseline  # noqa: E402


def load_processed():
    p = ROOT / "data" / "processed"
    if not (p / "interactions.csv").exists():
        sys.exit("Faltan datos procesados. Ejecute primero: uv run python scripts/prepare_data.py")
    return pd.read_csv(p / "interactions.csv"), pd.read_csv(p / "attractions.csv")


def main() -> None:
    cfg = load_config()
    reports, models_dir = ROOT / "reports", ROOT / "models"
    reports.mkdir(exist_ok=True)
    models_dir.mkdir(exist_ok=True)
    inter, att = load_processed()
    train, val, test = temporal_split(inter, cfg["split"]["train_end"], cfg["split"]["val_end"])
    k, n_items = cfg["evaluation"]["primary_k"], len(att)
    ctx_kw = dict(smoothing_m=cfg["models"]["context"]["smoothing_m"], w_mode=cfg["models"]["context"]["w_mode"])
    print(f"train {len(train)} | val {len(val)} | test {len(test)}")

    # 1 · Ajuste de pesos del híbrido en VALIDACIÓN (modelos entrenados solo con train)
    val_trips = build_trips(val, train)
    tuning = []
    for w in cfg["models"]["hybrid"]["weight_grid"]:
        m = HybridContentContext(**ctx_kw, rating_m=cfg["models"]["hybrid"]["rating_smoothing_m"], weights=w).fit(train, att)
        s, _ = evaluate_model(m, val_trips, k, n_items)
        tuning.append({"weights": w, **{c: s[c] for c in (f"ndcg@{k}", f"precision@{k}", f"hit@{k}", f"coverage@{k}")}})
        print("val", w, s[f"ndcg@{k}"])
    best_w = max(tuning, key=lambda r: (r[f"ndcg@{k}"], r[f"coverage@{k}"]))["weights"]
    pd.DataFrame(tuning).to_csv(reports / "tuning_validation.csv", index=False)
    print("pesos elegidos (contexto, contenido, calidad):", best_w)

    # 2 · Reentrenamiento con train+val y evaluación en PRUEBA (nunca vista durante el ajuste)
    hist = pd.concat([train, val])
    test_trips = build_trips(test, hist)
    specs = [
        ("baseline_popularidad", PopularityBaseline, {}),
        ("m1_contexto", ContextPopularity, ctx_kw),
        ("m2_hibrido", HybridContentContext, {**ctx_kw, "rating_m": cfg["models"]["hybrid"]["rating_smoothing_m"],
                                              "weights": best_w}),
    ]
    rows, details, green, fitted = [], {}, {}, {}
    for name, cls, kw in specs:
        g, model = green_metrics(cls, kw, hist, att)
        green[name], fitted[name] = g, model
        for kk in cfg["evaluation"]["k_values"]:
            s, d = evaluate_model(model, test_trips, kk, n_items)
            green[name][f"ms_per_request@{kk}"] = s.pop("ms_per_request")
            rows.append({key.replace(f"@{kk}", ""): v for key, v in s.items()})
            if kk == k:
                details[name] = d
    comparison = pd.DataFrame(rows)[["model", "k", "trips", "precision", "recall", "hit", "ndcg", "coverage",
                                     "popularity_bias"]]
    comparison.to_csv(reports / "comparison_test.csv", index=False)
    print(comparison.to_string(index=False))

    # 3 · ¿La diferencia frente al baseline es robusta? (bootstrap pareado por viaje)
    base = details["baseline_popularidad"]
    significance = {name: {m: bootstrap_diff(base[m], details[name][m]) for m in (f"precision@{k}", f"hit@{k}", f"ndcg@{k}")}
                    for name in ("m1_contexto", "m2_hibrido")}

    # 4 · Subgrupos (equidad y robustez) y análisis de errores
    sub = pd.concat([subgroup_table(details[n], by, k, n) for n in details for by in ("mode", "continent", "warm", "city")])
    sub.to_csv(reports / "subgroups_test.csv", index=False)
    d2 = details["m2_hibrido"].assign(targets=test_trips["targets"].values)
    missed = pd.Series([a for t, r in zip(d2["targets"], d2["recs"]) for a in t if a not in r]).value_counts()
    errors = (missed.rename("veces_no_recomendada").to_frame()
              .join(att.set_index("AttractionId")[["name", "city", "type"]])
              .join(fitted["m2_hibrido"].pop.rename("visitas_historial")))
    errors.to_csv(reports / "errors_missed_attractions.csv")

    # 5 · El DSS sobre los viajes de prueba: estados, explicaciones y abstención
    dss = TourismDSS(fitted["m2_hibrido"], cfg["dss"])
    results = [dss.recommend(ctx_from_trip(r)) for r in test_trips.itertuples(index=False)]
    dss_summary = {
        "trips": len(results),
        "status": pd.Series([r.status for r in results]).value_counts().to_dict(),
        "explanation_coverage": round(sum(all(it.reasons for it in r.items) and bool(r.items) for r in results) / len(results), 4),
        "hit@3_dss": round(float(pd.Series([any(it.AttractionId in t for it in r.items)
                                            for r, t in zip(results, test_trips["targets"])]).mean()), 4),
        "hit@3_by_status": pd.DataFrame({"s": [r.status for r in results],
                                          "h": [any(it.AttractionId in t for it in r.items)
                                                for r, t in zip(results, test_trips["targets"])]})
                            .groupby("s")["h"].mean().round(4).to_dict(),
    }

    meta = {"date": str(date.today()), "split": cfg["split"], "train_rows": len(train), "val_rows": len(val),
            "test_rows": len(test), "val_trips": len(val_trips), "test_trips": len(test_trips),
            "warm_test_trips": int(test_trips["warm"].sum()), "best_weights": best_w}
    out = {"meta": meta, "test": rows, "significance_vs_baseline": significance, "green": green, "dss": dss_summary}
    (reports / "metrics.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    fitted["m2_hibrido"]._cache = {}
    with open(models_dir / "m2_hibrido.pkl", "wb") as fh:
        pickle.dump(fitted["m2_hibrido"], fh)
    print(json.dumps({"significance": significance, "green": green, "dss": dss_summary}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
