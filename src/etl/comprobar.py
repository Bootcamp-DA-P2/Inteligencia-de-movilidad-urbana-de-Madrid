import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "trafico.duckdb"

con = duckdb.connect(str(DB_PATH), read_only=True)
con.sql("""
    SELECT id_sensor, fecha, COUNT(*) AS veces
    FROM raw_live
    GROUP BY id_sensor, fecha
    HAVING COUNT(*) > 1
""").show()
con.close()
print("Duplicados eliminados de raw_live")