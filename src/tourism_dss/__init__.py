"""DSS recomendador de atracciones turísticas (INF-8239 · Tema 31)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path | str | None = None) -> dict:
    """Lee configs/dss.yml (o la ruta indicada)."""
    path = Path(path) if path else ROOT / "configs" / "dss.yml"
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)
