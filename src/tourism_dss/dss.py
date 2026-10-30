"""Paquete 5 · Reglas, prioridades, explicaciones y abstención del DSS.

El DSS NO decide: entrega al planificador de viajes una lista priorizada y explicada, con un estado:
  GO       -> recomendación con evidencia suficiente
  REVIEW   -> recomendación entregada, pero con advertencias que requieren revisión humana
  ABSTAIN  -> el sistema no personaliza (falta perfil o contexto); muestra opciones generales marcadas
  STOP     -> no se puede recomendar (ciudad fuera de cobertura o restricciones imposibles)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .models import Context, HybridContentContext

MODE_ES = {"Business": "negocios", "Couples": "pareja", "Family": "familia", "Friends": "amigos", "Solo": "solo"}


@dataclass
class Recommendation:
    AttractionId: int
    name: str
    type: str
    score: float
    support: int
    reasons: list[str]
    flags: list[str] = field(default_factory=list)


@dataclass
class DSSResult:
    status: str
    items: list[Recommendation]
    warnings: list[str]
    rules_applied: list[str]
    profile_source: str

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([{
            "rank": i + 1, "atracción": r.name, "tipo": r.type, "puntaje": round(r.score, 3),
            "visitas de evidencia": r.support, "por qué": " · ".join(r.reasons),
            "advertencias": " · ".join(r.flags)} for i, r in enumerate(self.items)])


class TourismDSS:
    def __init__(self, model: HybridContentContext, cfg: dict):
        self.model = model
        self.cfg = cfg

    def recommend(self, ctx: Context, k: int | None = None, exclude_types: list[str] | None = None,
                  exclude_seen: bool = True) -> DSSResult:
        k = k or self.cfg["default_k"]
        warnings: list[str] = []
        rules = [f"top-{k}", f"máx. {self.cfg['max_per_type']} por tipo (diversidad)"]

        # Regla 1 · cobertura
        if ctx.city not in self.model.city_items:
            return DSSResult("STOP", [], [f"La ciudad «{ctx.city}» está fuera de la cobertura de los datos "
                                          f"({', '.join(sorted(self.model.city_items))}). Escalar a un asesor humano."],
                             ["cobertura"], "sin perfil")

        comps = self.model.components(ctx)
        scores = self.model.score(ctx)
        source = comps["profile_source"].iloc[0]
        att = self.model.attractions

        # Regla 2 · filtros duros (ya visitadas y tipos excluidos por el viajero)
        candidates = scores.index.tolist()
        if exclude_seen:
            seen = self.model.seen(ctx.user_id)
            candidates = [a for a in candidates if a not in seen]
            if seen:
                rules.append("excluye atracciones ya visitadas")
        if exclude_types:
            candidates = [a for a in candidates if att.loc[a, "type"] not in exclude_types]
            rules.append(f"excluye tipos: {', '.join(exclude_types)}")
        if not candidates:
            return DSSResult("STOP", [], ["Las restricciones eliminan todas las opciones. Relaje los filtros o "
                                          "consulte a un asesor humano."], rules, source)

        # Regla 3 · priorización con diversidad
        ranked = sorted(candidates, key=lambda a: (-scores[a], -self.model.pop[a], a))
        chosen, per_type = [], {}
        for a in ranked:
            t = att.loc[a, "type"]
            if per_type.get(t, 0) < self.cfg["max_per_type"]:
                chosen.append(a)
                per_type[t] = per_type.get(t, 0) + 1
            if len(chosen) == k:
                break
        if len(chosen) < k:
            for a in ranked:                      # se relaja la diversidad antes de entregar menos de k
                if a not in chosen:
                    chosen.append(a)
                if len(chosen) == k:
                    break
            if len(chosen) < k:
                warnings.append(f"Solo hay {len(chosen)} opciones que cumplen las restricciones (se pidieron {k}).")
            else:
                warnings.append("Se relajó la regla de diversidad para completar la lista.")

        # Regla 4 · abstención y revisión humana
        status = "GO"
        if source == "sin perfil":
            status = "ABSTAIN"
            warnings.append("Sin historial ni intereses declarados: el sistema se abstiene de personalizar. "
                            "La lista es general (contexto y calidad). Pida al viajero sus intereses.")
        support_ctx = int(self.model.mode_city_support.get((ctx.mode, ctx.city), 0)) if ctx.mode else 0
        if ctx.mode is None:
            warnings.append("No se indicó el modo de viaje: el contexto usa solo la popularidad general.")
            status = "REVIEW" if status == "GO" else status
        elif support_ctx < self.cfg["min_context_support"]:
            warnings.append(f"Poca evidencia para viajes de {MODE_ES.get(ctx.mode, ctx.mode)} en {ctx.city} "
                            f"({support_ctx} visitas < {self.cfg['min_context_support']}).")
            status = "REVIEW" if status == "GO" else status
        rest = [a for a in ranked if a not in chosen]
        if rest and chosen and scores[chosen[-1]] - scores[rest[0]] < self.cfg["tie_margin"]:
            warnings.append(f"Empate técnico entre «{att.loc[chosen[-1], 'name']}» y «{att.loc[rest[0], 'name']}»: "
                            "decide el planificador.")
            status = "REVIEW" if status == "GO" else status

        items = [self._explain(a, ctx, comps, scores, source) for a in chosen]
        if any(r.flags for r in items) and status == "GO":
            status = "REVIEW"
        return DSSResult(status, items, warnings, rules, source)

    def _explain(self, a: int, ctx: Context, comps: pd.DataFrame, scores: pd.Series, source: str) -> Recommendation:
        att = self.model.attractions.loc[a]
        support = int(self.model.pop[a])
        reasons = []
        if comps.loc[a, "content"] > 0:
            origin = "te interesa" if source == "intereses declarados" else "has visitado antes"
            reasons.append(f"tipo «{att['type']}» ({att['family']}), que {origin}")
        if ctx.mode:
            share = comps.loc[a, "share_mode"]
            reasons.append(f"{share:.0%} de las visitas de viajeros en {MODE_ES.get(ctx.mode, ctx.mode)} en {ctx.city} "
                           "(estimación suavizada)")
        reasons.append(f"calificación media {self.model.quality[a]:.2f}/5 con {support} visitas")
        flags = []
        if support < self.cfg["min_item_support"]:
            flags.append(f"evidencia limitada ({support} visitas)")
        return Recommendation(int(a), att["name"], att["type"], float(scores[a]), support, reasons, flags)
