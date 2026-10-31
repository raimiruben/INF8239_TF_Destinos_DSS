"""Paquete 4 · Evaluación, errores, subgrupos y Green AI.

Unidad de evaluación ("viaje"): las visitas de un usuario a una ciudad con un modo de viaje dentro del
periodo evaluado. Objetivo: atracciones de ese viaje que el usuario NO había visitado en el historial
(las ya visitadas se excluyen de candidatos y de objetivos, porque el DSS no las vuelve a recomendar).
"""

from __future__ import annotations

import math
import pickle
import time
import tracemalloc

import numpy as np
import pandas as pd

from .models import BaseRecommender, Context, recommend_top_k

MIN_SUBGROUP_TRIPS = 30  # por debajo no se interpreta el subgrupo


def build_trips(period: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    seen = history.groupby("UserId")["AttractionId"].agg(set).to_dict()
    trips = (period.groupby(["UserId", "city", "mode", "continent"])["AttractionId"]
             .agg(lambda s: set(s)).rename("targets").reset_index())
    trips["targets"] = [t - seen.get(u, set()) for u, t in zip(trips["UserId"], trips["targets"])]
    trips["warm"] = trips["UserId"].isin(seen)
    return trips[trips["targets"].map(len) > 0].reset_index(drop=True)


def precision_at_k(recs: list, targets: set, k: int) -> float:
    return sum(r in targets for r in recs[:k]) / k


def recall_at_k(recs: list, targets: set, k: int) -> float:
    return sum(r in targets for r in recs[:k]) / len(targets) if targets else 0.0


def hit_at_k(recs: list, targets: set, k: int) -> float:
    return float(any(r in targets for r in recs[:k]))


def ndcg_at_k(recs: list, targets: set, k: int) -> float:
    dcg = sum(1 / math.log2(i + 2) for i, r in enumerate(recs[:k]) if r in targets)
    idcg = sum(1 / math.log2(i + 2) for i in range(min(len(targets), k)))
    return dcg / idcg if idcg else 0.0


def catalog_coverage(all_recs: list[list], catalog_size: int) -> float:
    return len({r for recs in all_recs for r in recs}) / catalog_size


def ctx_from_trip(row) -> Context:
    return Context(city=row.city, mode=row.mode, continent=row.continent, user_id=row.UserId)


def recommend_trips(model: BaseRecommender, trips: pd.DataFrame, k: int) -> list[list]:
    return [recommend_top_k(model, ctx_from_trip(r), k) for r in trips.itertuples(index=False)]


def per_trip_metrics(recs: list[list], trips: pd.DataFrame, k: int) -> pd.DataFrame:
    rows = [{
        f"precision@{k}": precision_at_k(r, t, k), f"recall@{k}": recall_at_k(r, t, k),
        f"hit@{k}": hit_at_k(r, t, k), f"ndcg@{k}": ndcg_at_k(r, t, k),
    } for r, t in zip(recs, trips["targets"])]
    return pd.concat([trips.drop(columns="targets").reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def popularity_bias(model: BaseRecommender, recs: list[list]) -> float:
    """Percentil medio de popularidad (0 = menos visitada, 1 = más visitada) de lo recomendado."""
    pct = model.pop.rank(pct=True)
    flat = [a for r in recs for a in r]
    return float(pct.loc[flat].mean()) if flat else float("nan")


def evaluate_model(model: BaseRecommender, trips: pd.DataFrame, k: int, catalog_size: int) -> tuple[dict, pd.DataFrame]:
    t0 = time.perf_counter()
    recs = recommend_trips(model, trips, k)
    elapsed = time.perf_counter() - t0
    detail = per_trip_metrics(recs, trips, k)
    summary = {c: round(float(detail[c].mean()), 4) for c in detail.columns if "@" in c}
    summary.update({
        "model": model.name, "k": k, "trips": int(len(trips)),
        f"coverage@{k}": round(catalog_coverage(recs, catalog_size), 4),
        "popularity_bias": round(popularity_bias(model, recs), 4),
        "ms_per_request": round(1000 * elapsed / max(len(trips), 1), 3),
    })
    detail["recs"] = recs
    return summary, detail


def subgroup_table(detail: pd.DataFrame, by: str, k: int, model_name: str) -> pd.DataFrame:
    g = detail.groupby(by).agg(trips=(f"hit@{k}", "size"), **{
        f"precision@{k}": (f"precision@{k}", "mean"), f"hit@{k}": (f"hit@{k}", "mean"),
        f"ndcg@{k}": (f"ndcg@{k}", "mean")}).reset_index().rename(columns={by: "group"})
    g.insert(0, "dimension", by)
    g.insert(0, "model", model_name)
    g["interpretable"] = g["trips"] >= MIN_SUBGROUP_TRIPS
    return g


def bootstrap_diff(a: pd.Series, b: pd.Series, n: int = 1000, seed: int = 42) -> dict:
    """IC 95 % de la diferencia de medias pareada (b - a) por bootstrap sobre viajes."""
    rng = np.random.default_rng(seed)
    d = (b.to_numpy() - a.to_numpy())
    means = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(n)]
    return {"diff": round(float(d.mean()), 4), "ci95": [round(float(np.percentile(means, 2.5)), 4),
                                                        round(float(np.percentile(means, 97.5)), 4)]}


def green_metrics(model_cls, kwargs: dict, train: pd.DataFrame, attractions: pd.DataFrame) -> tuple[dict, BaseRecommender]:
    """Entrena midiendo tiempo, memoria pico y tamaño serializado (evidencia Green AI)."""
    tracemalloc.start()
    t0 = time.perf_counter()
    model = model_cls(**kwargs).fit(train, attractions)
    fit_s = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"fit_seconds": round(fit_s, 3), "peak_memory_mb": round(peak / 1e6, 2),
            "model_kb": round(len(pickle.dumps(model)) / 1024, 1)}, model
