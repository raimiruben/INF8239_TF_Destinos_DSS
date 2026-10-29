"""Paquetes 1-2 · Contrato de datos y partición sin fuga."""

import pytest

from tourism_dss.data import ATTRACTION_CITY_MAP, DataContractError, temporal_split, validate_raw


def test_contract_accepts_valid_data_and_maps_cities(tables):
    interactions, attractions = tables
    assert set(attractions["city"]) <= set(ATTRACTION_CITY_MAP.values())
    assert interactions[["mode", "city", "continent"]].notna().all().all()
    assert "Douala" not in set(attractions["city"])  # la tabla City no se usa como llave de Item


def test_contract_rejects_invalid_rating_and_unknown_attraction(raw_tables):
    raw_tables["Transaction"].loc[0, "Rating"] = 7
    raw_tables["Transaction"].loc[1, "AttractionId"] = 999
    with pytest.raises(DataContractError) as err:
        validate_raw(raw_tables)
    assert "Rating" in str(err.value) and "AttractionId" in str(err.value)


def test_temporal_split_has_no_future_leakage(tables):
    interactions, _ = tables
    train, val, test = temporal_split(interactions, 201712, 201812)
    assert train["ym"].max() < val["ym"].min() <= val["ym"].max() < test["ym"].min()
    assert len(train) + len(val) + len(test) == len(interactions)
    with pytest.raises(ValueError):
        temporal_split(interactions, 201812, 201712)
