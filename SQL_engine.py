import sqlite3
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

data_dir = Path("data/companies")


def to_float(x) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if s in ("-", ""):
        return None
    try:
        return float(s.replace(",", ".").replace(" ", ""))
    except ValueError:
        return None


def to_int(x) -> Optional[int]:
    v = to_float(x)
    return int(v) if v is not None else None


def csv_to_sql_db(folder_path: Path | str = data_dir) -> int:
    rows = []
    for csv_file in sorted(Path(folder_path).glob("*.csv")):
        with csv_file.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows.append((
                    row["Séance"],
                    row["Instrument"],
                    row["Ticker"],
                    to_float(row.get("Ouverture")),
                    to_float(row.get("Dernier_Cours")),
                    to_float(row.get("haut_du_jour")),   # fixed: was +haut_du_jour
                    to_float(row.get("bas_du_jour")),    # fixed: was +bas_du_jour
                    to_int(row.get("Nombre_de_titres_échangés")),
                    to_float(row.get("Volume_des_échanges")),
                    to_int(row.get("Nombre_de_transactions")),
                    to_float(row.get("Capitalisation")),
                ))

    seen = set()
    deduped = []
    for row in rows:
        key = (row[1], row[0])  # (instrument, date)
        if key not in seen:
            seen.add(key)
            deduped.append(row)

    deduped.sort(key=lambda r: (r[1], -datetime.strptime(r[0], "%d/%m/%Y").timestamp()))

    conn = sqlite3.connect("companies_SQL.db")
    conn.execute("DROP TABLE IF EXISTS companies")
    conn.execute("""
        CREATE TABLE companies (
            date                        TEXT    NOT NULL,
            instrument                  TEXT    NOT NULL,
            ticker                      TEXT    NOT NULL,
            ouverture                   REAL,
            dernier_cours               REAL,
            haut_du_jour                REAL,
            bas_du_jour                 REAL,
            nombre_de_titres_echanges   INTEGER,
            volume_des_echanges         REAL,
            nombre_de_transactions      INTEGER,
            capitalisation              REAL,
            PRIMARY KEY (ticker, date)
        )
    """)
    conn.executemany("INSERT INTO companies VALUES (?,?,?,?,?,?,?,?,?,?,?)", deduped)
    conn.commit()
    conn.close()
    return len(deduped)


if __name__ == "__main__":
    n = csv_to_sql_db()
    print(f"Done — {n} rows inserted")
