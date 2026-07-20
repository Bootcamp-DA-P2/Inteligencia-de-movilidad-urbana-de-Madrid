import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "trafico.duckdb"

con = duckdb.connect(str(DB_PATH))

con.execute("""
    CREATE OR REPLACE VIEW fact_trafico_completa AS
    SELECT * FROM fact_trafico_hora
    UNION ALL
    SELECT * FROM fact_trafico_hora_live
    WHERE (id_sensor, id_fecha, hora) NOT IN (
        SELECT id_sensor, id_fecha, hora FROM fact_trafico_hora
    )
""")

print("Vista fact_trafico_completa creada correctamente")

con.sql("SELECT COUNT(*) FROM fact_trafico_completa").show()

con.close()