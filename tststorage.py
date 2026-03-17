import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


def to_float(x: str) -> Optional[float]:
    x = x.strip()
    return None if x in ("-", "") else float(x.replace(",", ".").replace(" ", ""))


def to_int(x: str) -> Optional[int]:
    x = x.strip()
    return None if x in ("-", "") else int(float(x.replace(",", ".").replace(" ", "")))


@dataclass
class StoredObject:
    date: datetime
    instrument: str
    ticker: str
    ouverture: Optional[float]
    dernier_cours: Optional[float]
    haut_du_jour: Optional[float]
    bas_du_jour: Optional[float]
    nombre_de_titres_echanges: Optional[int]
    volume_des_echanges: Optional[float]
    nombre_de_transactions: Optional[int]
    capitalisation: Optional[float]

    @classmethod
    def from_row(cls, row: dict) -> "StoredObject":
        return cls(
            date=datetime.strptime(row["Séance"], "%d/%m/%Y"),
            instrument=row["Instrument"],
            ticker=row["Ticker"],
            ouverture=to_float(row["Ouverture"]),
            dernier_cours=to_float(row["Dernier_Cours"]),
            haut_du_jour=to_float(row["+haut_du_jour"]),
            bas_du_jour=to_float(row["+bas_du_jour"]),
            nombre_de_titres_echanges=to_int(row["Nombre_de_titres_échangés"]),
            volume_des_echanges=to_float(row["Volume_des_échanges"]),
            nombre_de_transactions=to_int(row["Nombre_de_transactions"]),
            capitalisation=to_float(row["Capitalisation"]),
        )

    @property
    def missing_data(self) -> bool:
        return self.ouverture is None

    @staticmethod
    def load_from_csv(data_dir: Path | str = Path("data/companies")) -> list["StoredObject"]:
        data_dir = Path(data_dir)
        objects: list[StoredObject] = []
        errors = 0

        for csv_file in sorted(data_dir.glob("*.csv")):
            with csv_file.open(encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    try:
                        objects.append(StoredObject.from_row(row))
                    except Exception as e:
                        errors += 1
                        print(f"[{csv_file.name}] Skipped row: {e}\n  Row: {row}")

        if errors:
            print(f"\n{errors} row(s) skipped across all files.")

        return sorted(objects, key=lambda o: (o.ticker, o.date))