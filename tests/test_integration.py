"""Integración con los datos reales (se omite si data/raw no tiene las tablas, p. ej. en CI)."""

from pathlib import Path

import pytest

from tourism_dss import ROOT, load_config
from tourism_dss.data import build_tables, load_raw, temporal_split
from tourism_dss.dss import TourismDSS
from tourism_dss.models import Context, HybridContentContext

RAW = ROOT / "data" / "raw"
pytestmark = [pytest.mark.integration,
              pytest.mark.skipif(not (RAW / "Transaction.xlsx").exists(), reason="sin datos reales en data/raw")]


def test_real_data_contract_and_end_to_end_flow():
    interactions, attractions = build_tables(load_raw(RAW))
    assert interactions.shape == (52930, 10) and len(attractions) == 30
    cfg = load_config()
    train, val, _ = temporal_split(interactions, cfg["split"]["train_end"], cfg["split"]["val_end"])
    dss = TourismDSS(HybridContentContext().fit(train, attractions), cfg["dss"])
    # escenario no memorizado: viajero nuevo, en familia, interesado en cascadas y volcanes
    result = dss.recommend(Context(city="Malang", mode="Family", continent="Europe",
                                   interests=["Waterfalls", "Volcanos"]))
    assert result.status in {"GO", "REVIEW"} and len(result.items) == 3
    assert any(item.type in {"Waterfalls", "Volcanos"} for item in result.items)
    assert all(item.reasons for item in result.items)


def test_app_module_compiles():
    source = Path(ROOT / "app.py").read_text(encoding="utf-8")
    compile(source, "app.py", "exec")
