import duckdb

con = duckdb.connect()

con.execute("""
COPY (
    SELECT *
    FROM read_parquet('data/gold/fact_trafico_hora.parquet')
    WHERE CAST(id_fecha AS DATE) >= DATE '2026-06-06'
      AND CAST(id_fecha AS DATE) < DATE '2026-06-13'
)
TO 'data/gold/fact_trafico_hora_demo.parquet'
(FORMAT PARQUET);
""")

con.close()

print("Dataset demo creado.")