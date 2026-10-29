"""Paquetes 1-2 · Lee las 9 tablas crudas, valida el contrato y genera los datos procesados + auditoría.

Uso: uv run python scripts/prepare_data.py
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tourism_dss.data import RAW_TABLES, audit, build_tables, load_raw  # noqa: E402


def main() -> None:
    raw_dir, out_dir = ROOT / "data" / "raw", ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)

    tables = load_raw(raw_dir)
    interactions, attractions = build_tables(tables)
    interactions.to_csv(out_dir / "interactions.csv", index=False)
    attractions.to_csv(out_dir / "attractions.csv", index=False)

    report = audit(interactions, attractions)
    report["raw_sha256"] = {t: hashlib.sha256((raw_dir / f"{t}.xlsx").read_bytes()).hexdigest()[:16] for t in RAW_TABLES}
    (ROOT / "reports" / "data_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"interactions: {interactions.shape} | attractions: {attractions.shape}")
    print(f"usuarios: {report['users']} | periodo: {report['period']} | ciudades: {report['cities']}")
    print("contract_status: valid")


if __name__ == "__main__":
    main()
