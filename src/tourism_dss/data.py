"""Paquetes 1 y 2 · Gobernanza, adquisición, contrato de datos, auditoría y partición sin fuga.

Fuente: Huda, C. (2023). Tourism Dataset. Mendeley Data, V1. DOI 10.17632/h58s544674.1
Uso: investigación, no comercial.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW_TABLES = ["Transaction", "Item", "Type", "Mode", "User", "Continent", "Region", "Country", "City"]

# Hallazgo del contrato: Item.AttractionCityId (1, 2, 3) NO es llave de la tabla City
# (CityId 1 = Douala, Camerún). Se mapea por los nombres y direcciones de las atracciones.
ATTRACTION_CITY_MAP = {1: "Bali", 2: "Malang", 3: "Yogyakarta"}

# Agrupación temática de los 17 tipos (para la afinidad de contenido)
TYPE_FAMILY = {
    "Beaches": "Naturaleza", "Waterfalls": "Naturaleza", "Volcanos": "Naturaleza",
    "National Parks": "Naturaleza", "Nature & Wildlife Areas": "Naturaleza", "Caverns & Caves": "Naturaleza",
    "Ancient Ruins": "Cultura", "Religious Sites": "Cultura", "Historic Sites": "Cultura",
    "History Museums": "Cultura", "Speciality Museums": "Cultura", "Ballets": "Cultura",
    "Flea & Street Markets": "Urbano y ocio", "Neighborhoods": "Urbano y ocio",
    "Points of Interest & Landmarks": "Urbano y ocio", "Spas": "Urbano y ocio", "Water Parks": "Urbano y ocio",
}

INTERACTION_COLUMNS = ["TransactionId", "UserId", "AttractionId", "ym", "VisitYear", "VisitMonth",
                       "mode", "Rating", "continent", "city"]
ATTRACTION_COLUMNS = ["AttractionId", "name", "city", "type", "family", "address"]


class DataContractError(ValueError):
    """Los datos no cumplen el contrato."""


def load_raw(raw_dir: Path | str) -> dict[str, pd.DataFrame]:
    raw_dir = Path(raw_dir)
    missing = [t for t in RAW_TABLES if not (raw_dir / f"{t}.xlsx").exists()]
    if missing:
        raise FileNotFoundError(
            f"Faltan tablas en {raw_dir}: {missing}. Descárguelas de https://data.mendeley.com/datasets/h58s544674/1 "
            "(ver data/README.md)."
        )
    return {t: pd.read_excel(raw_dir / f"{t}.xlsx") for t in RAW_TABLES}


def validate_raw(t: dict[str, pd.DataFrame]) -> None:
    """Contrato de las tablas crudas. Lanza DataContractError con todos los problemas encontrados."""
    problems: list[str] = []
    required = {
        "Transaction": {"TransactionId", "UserId", "VisitYear", "VisitMonth", "VisitMode", "AttractionId", "Rating"},
        "Item": {"AttractionId", "AttractionCityId", "AttractionTypeId", "Attraction", "AttractionAddress"},
        "Type": {"AttractionTypeId", "AttractionType"},
        "Mode": {"VisitModeId", "VisitMode"},
        "User": {"UserId", "ContenentId"},
        "Continent": {"ContenentId", "Contenent"},
    }
    for name, cols in required.items():
        lost = cols - set(t[name].columns)
        if lost:
            problems.append(f"{name}: faltan columnas {sorted(lost)}")
    if problems:
        raise DataContractError("; ".join(problems))

    tx, item = t["Transaction"], t["Item"]
    if tx["TransactionId"].duplicated().any():
        problems.append("Transaction: TransactionId duplicado")
    if not tx["Rating"].between(1, 5).all():
        problems.append("Transaction: Rating fuera de 1-5")
    if not tx["VisitMonth"].between(1, 12).all():
        problems.append("Transaction: VisitMonth fuera de 1-12")
    if not tx["VisitMode"].isin(t["Mode"]["VisitModeId"]).all():
        problems.append("Transaction: VisitMode sin correspondencia en Mode")
    if not tx["AttractionId"].isin(item["AttractionId"]).all():
        problems.append("Transaction: AttractionId sin correspondencia en Item")
    if not tx["UserId"].isin(t["User"]["UserId"]).all():
        problems.append("Transaction: UserId sin correspondencia en User")
    if not item["AttractionCityId"].isin(ATTRACTION_CITY_MAP).all():
        problems.append("Item: AttractionCityId fuera del mapeo documentado")
    if not item["AttractionTypeId"].isin(t["Type"]["AttractionTypeId"]).all():
        problems.append("Item: AttractionTypeId sin correspondencia en Type")
    unknown_types = set(t["Type"]["AttractionType"]) - set(TYPE_FAMILY)
    if unknown_types:
        problems.append(f"Type: tipos sin familia temática {sorted(unknown_types)}")
    if problems:
        raise DataContractError("; ".join(problems))


def build_tables(t: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (interactions, attractions) limpias y con nombres legibles."""
    validate_raw(t)
    item = t["Item"].merge(t["Type"], on="AttractionTypeId", how="left")
    attractions = pd.DataFrame({
        "AttractionId": item["AttractionId"],
        "name": item["Attraction"].str.strip(),
        "city": item["AttractionCityId"].map(ATTRACTION_CITY_MAP),
        "type": item["AttractionType"],
        "family": item["AttractionType"].map(TYPE_FAMILY),
        "address": item["AttractionAddress"].astype(str).str.strip(),
    }).sort_values("AttractionId").reset_index(drop=True)

    users = t["User"].merge(t["Continent"], on="ContenentId", how="left")[["UserId", "Contenent"]]
    tx = (t["Transaction"]
          .merge(t["Mode"].rename(columns={"VisitModeId": "VisitMode", "VisitMode": "mode"}), on="VisitMode", how="left")
          .merge(users, on="UserId", how="left")
          .merge(attractions[["AttractionId", "city"]], on="AttractionId", how="left"))
    tx["continent"] = tx["Contenent"].replace({"-": "Desconocido"}).fillna("Desconocido")
    tx["ym"] = tx["VisitYear"] * 100 + tx["VisitMonth"]
    interactions = tx[INTERACTION_COLUMNS].sort_values(["ym", "TransactionId"]).reset_index(drop=True)
    validate_processed(interactions, attractions)
    return interactions, attractions


def validate_processed(interactions: pd.DataFrame, attractions: pd.DataFrame) -> None:
    problems = []
    if list(interactions.columns) != INTERACTION_COLUMNS:
        problems.append("interactions: columnas distintas al contrato")
    if list(attractions.columns) != ATTRACTION_COLUMNS:
        problems.append("attractions: columnas distintas al contrato")
    if interactions[["mode", "city", "continent"]].isna().any().any():
        problems.append("interactions: nulos en mode/city/continent tras las uniones")
    if attractions[["city", "type", "family"]].isna().any().any():
        problems.append("attractions: nulos en city/type/family")
    direct_ids = {"name", "email", "phone", "UserName"} & set(interactions.columns)
    if direct_ids:
        problems.append(f"interactions: identificadores directos {sorted(direct_ids)}")
    if problems:
        raise DataContractError("; ".join(problems))


def temporal_split(interactions: pd.DataFrame, train_end: int, val_end: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Partición temporal global (sin fuga del futuro): train <= train_end < val <= val_end < test."""
    if not train_end < val_end:
        raise ValueError("train_end debe ser anterior a val_end")
    train = interactions[interactions["ym"] <= train_end]
    val = interactions[(interactions["ym"] > train_end) & (interactions["ym"] <= val_end)]
    test = interactions[interactions["ym"] > val_end]
    return train.copy(), val.copy(), test.copy()


def audit(interactions: pd.DataFrame, attractions: pd.DataFrame) -> dict:
    """Resumen de auditoría de datos (se guarda en reports/data_audit.json)."""
    per_user = interactions.groupby("UserId").size()
    per_item = interactions.groupby("AttractionId").size()
    return {
        "interactions": int(len(interactions)),
        "users": int(interactions["UserId"].nunique()),
        "attractions": int(len(attractions)),
        "cities": attractions["city"].value_counts().to_dict(),
        "types": int(attractions["type"].nunique()),
        "period": [int(interactions["ym"].min()), int(interactions["ym"].max())],
        "visits_per_year": interactions.groupby("VisitYear").size().astype(int).to_dict(),
        "users_with_2plus_visits": int((per_user >= 2).sum()),
        "repeat_user_attraction_pairs": int(interactions.duplicated(["UserId", "AttractionId"]).sum()),
        "visits_per_attraction_min_median_max": [int(per_item.min()), int(per_item.median()), int(per_item.max())],
        "rating_distribution": interactions["Rating"].value_counts().sort_index().astype(int).to_dict(),
        "mode_distribution": interactions["mode"].value_counts().astype(int).to_dict(),
        "continent_distribution": interactions["continent"].value_counts().astype(int).to_dict(),
        "known_issues": [
            "Item.AttractionCityId no es llave de City: se mapea a Bali/Malang/Yogyakarta",
            "Muy pocas visitas desde 2020 (COVID): la prueba se concentra en 2019",
            "Popularidad muy concentrada entre atracciones",
        ],
    }
