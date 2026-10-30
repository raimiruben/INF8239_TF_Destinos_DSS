"""Paquetes 5-6 · Reglas, abstención, explicación e integración."""

import pytest

from tourism_dss.data import temporal_split
from tourism_dss.dss import TourismDSS
from tourism_dss.models import Context, HybridContentContext


@pytest.fixture
def dss(tables, dss_cfg):
    interactions, attractions = tables
    train, _, _ = temporal_split(interactions, 201712, 201812)
    return TourismDSS(HybridContentContext().fit(train, attractions), dss_cfg)


def test_stop_when_city_is_outside_coverage(dss):
    result = dss.recommend(Context(city="Punta Cana", mode="Couples"))
    assert result.status == "STOP" and not result.items
    assert "fuera de la cobertura" in result.warnings[0]


def test_abstains_without_profile_and_explains_with_interests(dss):
    general = dss.recommend(Context(city="Bali", mode="Couples", continent="Asia"))
    assert general.status == "ABSTAIN" and general.items  # muestra opciones generales, marcadas
    personal = dss.recommend(Context(city="Bali", mode="Couples", continent="Asia", interests=["Beaches"]))
    assert personal.status in {"GO", "REVIEW"}
    assert all(item.reasons for item in personal.items)
    assert any("te interesa" in r for item in personal.items for r in item.reasons)


def test_diversity_rule_and_impossible_constraints(dss):
    result = dss.recommend(Context(city="Bali", mode="Couples", continent="Asia", interests=["Beaches"]), k=2)
    assert len({item.type for item in result.items}) == 2  # máx. 1 por tipo: no dos playas
    blocked = dss.recommend(Context(city="Bali", mode="Couples"), exclude_types=["Beaches", "Religious Sites"])
    assert blocked.status == "STOP"


def test_low_evidence_context_requires_human_review(dss):
    result = dss.recommend(Context(city="Malang", mode="Solo", continent="Asia", interests=["Volcanos"]))
    assert result.status == "REVIEW"
    assert any("Poca evidencia" in w for w in result.warnings)
    frame = result.to_frame()
    assert {"atracción", "por qué", "advertencias"} <= set(frame.columns)
