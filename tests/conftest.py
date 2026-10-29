"""Datos sintéticos mínimos con el mismo esquema que el dataset real (las pruebas no dependen de data/raw)."""

import pandas as pd
import pytest

from tourism_dss.data import TYPE_FAMILY, build_tables

DSS_CFG = {"default_k": 2, "max_per_type": 1, "min_context_support": 3, "min_item_support": 2, "tie_margin": 0.0}


@pytest.fixture
def raw_tables():
    types = sorted(TYPE_FAMILY)
    tid = {t: i + 1 for i, t in enumerate(types)}
    item = pd.DataFrame({
        "AttractionId": [1, 2, 3, 4, 5, 6],
        "AttractionCityId": [1, 1, 1, 2, 2, 2],
        "AttractionTypeId": [tid["Beaches"], tid["Religious Sites"], tid["Beaches"],
                             tid["Volcanos"], tid["History Museums"], tid["Spas"]],
        "Attraction": ["Playa A", "Templo B", "Playa C", "Volcán D", "Museo E", "Spa F"],
        "AttractionAddress": ["a", "b", "c", "d", "e", "f"],
    })
    rows = []
    tx_id = 1

    def add(user, year, month, mode, att, rating):
        nonlocal tx_id
        rows.append([tx_id, user, year, month, mode, att, rating])
        tx_id += 1

    # Ciudad 1 (Bali): Playa A es la más popular en general (parejas); Templo B domina en familias (modo 3)
    for u in range(1, 9):
        add(u, 2016, 3, 2, 1, 5)
    for u in range(9, 13):
        add(u, 2016, 5, 3, 2, 4)
    add(13, 2017, 1, 3, 2, 5)
    add(14, 2017, 2, 2, 3, 3)
    # Ciudad 2 (Malang)
    for u in range(1, 4):
        add(u, 2017, 6, 2, 4, 4)
    add(4, 2017, 7, 5, 5, 3)
    # Validación (2018) y prueba (2019)
    add(1, 2018, 4, 2, 2, 4)
    add(9, 2018, 8, 3, 1, 5)
    add(2, 2019, 1, 2, 3, 4)
    add(10, 2019, 2, 3, 3, 5)
    add(20, 2019, 3, 4, 5, 4)
    tx = pd.DataFrame(rows, columns=["TransactionId", "UserId", "VisitYear", "VisitMonth", "VisitMode",
                                     "AttractionId", "Rating"])
    users = pd.DataFrame({"UserId": list(range(1, 15)) + [20],
                          "ContenentId": [3] * 7 + [4] * 7 + [5], "RegionId": 0, "CountryId": 0, "CityId": 0})
    return {
        "Transaction": tx, "Item": item,
        "Type": pd.DataFrame({"AttractionTypeId": list(tid.values()), "AttractionType": list(tid)}),
        "Mode": pd.DataFrame({"VisitModeId": [0, 1, 2, 3, 4, 5],
                              "VisitMode": ["-", "Business", "Couples", "Family", "Friends", "Solo"]}),
        "User": users,
        "Continent": pd.DataFrame({"ContenentId": [0, 1, 2, 3, 4, 5],
                                   "Contenent": ["-", "Africa", "America", "Asia", "Australia & Oceania", "Europe"]}),
        "Region": pd.DataFrame({"Region": ["-"], "RegionId": [0], "ContentId": [0]}),
        "Country": pd.DataFrame({"CountryId": [0], "Country": ["-"], "RegionId": [0]}),
        "City": pd.DataFrame({"CityId": [0, 1], "CityName": ["-", "Douala"], "CountryId": [0, 0]}),
    }


@pytest.fixture
def tables(raw_tables):
    return build_tables(raw_tables)


@pytest.fixture
def dss_cfg():
    return dict(DSS_CFG)
