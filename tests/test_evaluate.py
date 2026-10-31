"""Paquete 4 · Métricas, unidades de evaluación y subgrupos."""

import math

import pandas as pd
import pytest

from tourism_dss.data import temporal_split
from tourism_dss.evaluate import (MIN_SUBGROUP_TRIPS, build_trips, catalog_coverage, hit_at_k, ndcg_at_k,
                                  precision_at_k, recall_at_k, subgroup_table)


def test_ranking_metrics_match_hand_computed_values():
    recs, targets = [10, 20, 30], {20, 40}
    assert precision_at_k(recs, targets, 3) == pytest.approx(1 / 3)
    assert recall_at_k(recs, targets, 3) == pytest.approx(1 / 2)
    assert hit_at_k(recs, targets, 3) == 1.0
    expected_ndcg = (1 / math.log2(3)) / (1 / math.log2(2) + 1 / math.log2(3))
    assert ndcg_at_k(recs, targets, 3) == pytest.approx(expected_ndcg)
    assert catalog_coverage([[1, 2], [2, 3]], 6) == pytest.approx(0.5)


def test_trips_exclude_attractions_already_in_history(tables):
    interactions, _ = tables
    train, val, test = temporal_split(interactions, 201712, 201812)
    trips = build_trips(test, pd.concat([train, val]))
    by_user = dict(zip(trips["UserId"], trips["targets"]))
    assert by_user[2] == {3} and by_user[10] == {3}
    assert by_user[20] == {5} and not trips.loc[trips["UserId"] == 20, "warm"].iloc[0]  # usuario nuevo (frío)


def test_small_subgroups_are_flagged_as_not_interpretable():
    detail = pd.DataFrame({"mode": ["Family"] * MIN_SUBGROUP_TRIPS + ["Solo"] * 3,
                           "precision@3": 0.5, "hit@3": 1.0, "ndcg@3": 0.7})
    table = subgroup_table(detail, "mode", 3, "m").set_index("group")
    assert table.loc["Family", "interpretable"] and not table.loc["Solo", "interpretable"]
