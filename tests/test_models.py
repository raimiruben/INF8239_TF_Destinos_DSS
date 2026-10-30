"""Paquete 3 · Baseline y modelos candidatos."""

import pytest

from tourism_dss.data import temporal_split
from tourism_dss.models import (Context, ContextPopularity, HybridContentContext, PopularityBaseline,
                                recommend_top_k)


@pytest.fixture
def train_att(tables):
    interactions, attractions = tables
    train, _, _ = temporal_split(interactions, 201712, 201812)
    return train, attractions


@pytest.mark.parametrize("cls", [PopularityBaseline, ContextPopularity, HybridContentContext])
def test_scores_cover_city_and_are_bounded(train_att, cls):
    model = cls().fit(*train_att)
    s = model.score(Context(city="Bali", mode="Couples", continent="Asia"))
    assert sorted(s.index) == [1, 2, 3]
    assert s.between(0, 1 + 1e-9).all()


def test_context_model_changes_ranking_with_travel_mode(train_att):
    base = PopularityBaseline().fit(*train_att)
    ctx_model = ContextPopularity(smoothing_m=1, w_mode=1.0).fit(*train_att)
    family = Context(city="Bali", mode="Family", continent="Asia")
    assert recommend_top_k(base, family, 1) == [1]        # el baseline ignora el contexto
    assert recommend_top_k(ctx_model, family, 1) == [2]   # en familia domina el templo


def test_hybrid_uses_declared_interests_and_excludes_seen(train_att):
    model = HybridContentContext(weights=(0.2, 0.8, 0.0)).fit(*train_att)
    ctx = Context(city="Bali", mode="Couples", continent="Asia", interests=["Religious Sites"])
    assert recommend_top_k(model, ctx, 1) == [2]
    visited = Context(city="Bali", mode="Couples", continent="Asia", user_id=1)  # usuario 1 ya visitó la 1
    assert 1 not in recommend_top_k(model, visited, 3)
