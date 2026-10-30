"""Paquete 3 · Baseline y modelos candidatos.

Interfaz común: fit(train, attractions) y score(context) -> pd.Series (índice AttractionId, valores en [0, 1])
con las atracciones de la ciudad pedida. Más puntaje = más recomendable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class Context:
    """Lo que sabe el planificador al momento de decidir (nada del futuro)."""
    city: str
    mode: str | None = None              # Business, Couples, Family, Friends, Solo
    continent: str | None = None         # continente de origen del viajero
    user_id: int | None = None           # para leer su historial (si existe)
    interests: list[str] = field(default_factory=list)  # tipos de atracción declarados por el viajero


def _minmax(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if hi - lo < 1e-12:
        return pd.Series(0.0, index=s.index)
    return (s - lo) / (hi - lo)


class BaseRecommender:
    name = "base"

    def fit(self, train: pd.DataFrame, attractions: pd.DataFrame) -> "BaseRecommender":
        self.attractions = attractions.set_index("AttractionId")
        self.city_items = {c: g.index.tolist() for c, g in self.attractions.groupby("city")}
        self.pop = train.groupby("AttractionId").size().reindex(self.attractions.index, fill_value=0)
        self.history = train.groupby("UserId")["AttractionId"].agg(set).to_dict()
        self._cache = {}  # componentes de contexto por (ciudad, modo, continento): muchos viajeros comparten contexto
        return self

    def items(self, city: str) -> list[int]:
        if city not in self.city_items:
            raise KeyError(f"Ciudad fuera de cobertura: {city}")
        return self.city_items[city]

    def seen(self, user_id: int | None) -> set[int]:
        return self.history.get(user_id, set()) if user_id is not None else set()

    def score(self, ctx: Context) -> pd.Series:  # pragma: no cover - interfaz
        raise NotImplementedError


class PopularityBaseline(BaseRecommender):
    """Baseline: atracciones más visitadas de la ciudad en el periodo de entrenamiento."""
    name = "baseline_popularidad"

    def score(self, ctx: Context) -> pd.Series:
        return _minmax(self.pop.loc[self.items(ctx.city)].astype(float))


class ContextPopularity(BaseRecommender):
    """Modelo 1 · Contexto: popularidad condicionada al modo de viaje y al continente de origen,
    suavizada hacia la popularidad global de la ciudad (evita sobreajustar contextos con pocos datos)."""
    name = "m1_contexto"

    def __init__(self, smoothing_m: float = 50, w_mode: float = 0.6):
        self.m, self.w_mode = smoothing_m, w_mode

    def fit(self, train, attractions):
        super().fit(train, attractions)
        self.by_mode = train.groupby(["mode", "AttractionId"]).size()
        self.by_cont = train.groupby(["continent", "AttractionId"]).size()
        self.mode_city_support = train.groupby(["mode", "city"]).size()
        return self

    def _smoothed_share(self, counts: pd.Series, key, items) -> pd.Series:
        prior = self.pop.loc[items] / max(self.pop.loc[items].sum(), 1)
        if key is None:
            return prior
        n = counts.loc[key].reindex(items, fill_value=0) if key in counts.index.get_level_values(0) else pd.Series(0, index=items)
        return (n + self.m * prior) / (n.sum() + self.m)

    def components(self, ctx: Context) -> pd.DataFrame:
        key = (ctx.city, ctx.mode, ctx.continent)
        if key not in self._cache:
            self._cache[key] = self._context_components(ctx)
        return self._cache[key].copy()

    def _context_components(self, ctx: Context) -> pd.DataFrame:
        items = self.items(ctx.city)
        share_mode = self._smoothed_share(self.by_mode, ctx.mode, items)
        share_cont = self._smoothed_share(self.by_cont, ctx.continent, items)
        c = pd.DataFrame({"share_mode": share_mode, "share_continent": share_cont})
        c["context"] = _minmax(self.w_mode * c["share_mode"] + (1 - self.w_mode) * c["share_continent"])
        return c

    def score(self, ctx: Context) -> pd.Series:
        return self.components(ctx)["context"]


class HybridContentContext(ContextPopularity):
    """Modelo 2 · Híbrido contenido + contexto + calidad.

    - contexto: puntaje del Modelo 1
    - contenido: afinidad del perfil del viajero (tipos visitados antes o intereses declarados) con el tipo
      y la familia temática de cada atracción
    - calidad: calificación media bayesiana (suavizada hacia la media global)
    """
    name = "m2_hibrido"

    def __init__(self, smoothing_m=50, w_mode=0.6, rating_m=20, weights=(0.5, 0.3, 0.2)):
        super().__init__(smoothing_m, w_mode)
        self.rating_m = rating_m
        self.weights = tuple(weights)

    def fit(self, train, attractions):
        super().fit(train, attractions)
        g = train.groupby("AttractionId")["Rating"].agg(["sum", "count"]).reindex(self.attractions.index, fill_value=0)
        mu = train["Rating"].mean()
        self.quality = (g["sum"] + self.rating_m * mu) / (g["count"] + self.rating_m)
        first = train.drop_duplicates(["UserId", "AttractionId"]).merge(
            attractions[["AttractionId", "type", "family"]], on="AttractionId")
        self.type_family = dict(zip(attractions["type"], attractions["family"]))
        self.user_profiles = {}
        for (u, t), share in first.groupby("UserId")["type"].value_counts(normalize=True).items():
            self.user_profiles.setdefault(u, {})[t] = share
        return self

    def profile(self, ctx: Context) -> tuple[dict, dict, str]:
        """Perfil de contenido: intereses declarados tienen prioridad sobre el historial."""
        if ctx.interests:
            types = {t: 1 / len(ctx.interests) for t in ctx.interests}
            return types, self._families(types), "intereses declarados"
        if ctx.user_id is not None and ctx.user_id in self.user_profiles:
            types = self.user_profiles[ctx.user_id]
            return types, self._families(types), "historial de visitas"
        return {}, {}, "sin perfil"

    def _families(self, types: dict) -> dict:
        fam: dict = {}
        for t, share in types.items():
            f = self.type_family.get(t)
            if f:
                fam[f] = fam.get(f, 0) + share
        return fam

    def _context_components(self, ctx: Context) -> pd.DataFrame:
        c = super()._context_components(ctx)
        att = self.attractions.loc[c.index]
        c["type"], c["family"] = att["type"], att["family"]
        c["quality"] = _minmax(self.quality.loc[c.index])
        return c

    def components(self, ctx: Context) -> pd.DataFrame:
        c = super().components(ctx)  # contexto, tipo y calidad (cacheados por contexto)
        types, fams, source = self.profile(ctx)
        c["content"] = [0.7 * types.get(t, 0.0) + 0.3 * fams.get(f, 0.0) for t, f in zip(c["type"], c["family"])]
        c["profile_source"] = source
        return c

    def score(self, ctx: Context) -> pd.Series:
        c = self.components(ctx)
        wc, wt, wq = self.weights
        if c["content"].sum() == 0:            # sin perfil: el peso de contenido pasa al contexto
            wc, wt = wc + wt, 0.0
        return wc * c["context"] + wt * c["content"] + wq * c["quality"]


def recommend_top_k(model: BaseRecommender, ctx: Context, k: int, exclude_seen: bool = True) -> list[int]:
    s = model.score(ctx)
    if exclude_seen:
        seen = model.seen(ctx.user_id)
        if seen:
            s = s[~s.index.isin(list(seen))]
    # desempate determinista: puntaje, luego popularidad, luego id
    pop = model.pop
    return sorted(s.index, key=lambda a: (-s[a], -pop[a], a))[:k]


MODEL_REGISTRY = {
    "baseline_popularidad": PopularityBaseline,
    "m1_contexto": ContextPopularity,
    "m2_hibrido": HybridContentContext,
}
