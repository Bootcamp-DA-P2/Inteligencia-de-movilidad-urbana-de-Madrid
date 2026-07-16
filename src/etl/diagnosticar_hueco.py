import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "trafico.duckdb"

con = duckdb.connect(str(DB_PATH), read_only=True)

print("=== Rango de fechas por tabla ===")
con.sql("""
    SELECT 'historico' AS tabla, MIN(id_fecha) AS min_fecha, MAX(id_fecha) AS max_fecha
    FROM fact_trafico_hora
    UNION ALL
    SELECT 'live', MIN(id_fecha), MAX(id_fecha)
    FROM fact_trafico_hora_live
""").show()

print("=== Últimas 20 horas del sensor 9841 en la vista completa ===")
con.sql("""
    SELECT id_sensor, id_fecha, hora
    FROM fact_trafico_completa
    WHERE id_sensor = 9841
    ORDER BY id_fecha DESC, hora DESC
    LIMIT 20
""").show()

con.close()