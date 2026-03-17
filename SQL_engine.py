import sqlite3
import csv
import os

data_dir = r"data\companies"

def csv_to_sql_db(folder_path):

    conn = sqlite3.connect("companies_SQL.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            date TEXT NOT NULL,
            instrument TEXT NOT NULL,
            ticker TEXT NOT NULL,
            ouverture REAL,
            dernier_cours REAL,
            haut_du_jour REAL,
            bas_du_jour REAL,
            nombre_de_titres_echanges INTEGER,
            volume_des_echanges REAL,
            nombre_de_transactions INTEGER,
            capitalisation REAL,
            PRIMARY KEY (ticker, date)
        )
    """)

    for file in os.listdir(folder_path):

        if file.endswith(".csv"):

            file_path = os.path.join(folder_path, file)

            with open(file_path, "r", encoding="utf-8") as f:

                reader = csv.DictReader(f)

                for row in reader:
                    cursor.execute("""
                        INSERT OR IGNORE INTO companies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row["Séance"],
                        row["Instrument"],
                        row["Ticker"],
                        row["Ouverture"],
                        row["Dernier_Cours"],
                        row["+haut_du_jour"],
                        row["+bas_du_jour"],
                        row["Nombre_de_titres_échangés"],
                        row["Volume_des_échanges"],
                        row.get("Nombre_de_transactions", 0), 
                        row.get("Capitalisation", 0)          
                    ))

    conn.commit()
    conn.close()

