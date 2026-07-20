import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "trafico.duckdb"

con = duckdb.connect(str(DB_PATH), read_only=True)
con.sql("""
    SELECT
        approx_quantile(ocupacion_media, 0.33) AS umbral_bajo_medio,
        approx_quantile(ocupacion_media, 0.66) AS umbral_medio_alto
    FROM fact_trafico_hora
""").show()
con.close()