import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "trafico.duckdb"

con = duckdb.connect(str(DB_PATH))

print("=== 1. Creando tabla fact_trafico_hora_live si no existe ===")
con.execute("""
    CREATE TABLE IF NOT EXISTS fact_trafico_hora_live AS
    SELECT * FROM fact_trafico_hora WHERE 1=0
""")

print("=== 2. Ejecutando agregación de la última hora ===")
con.execute("""
    INSERT INTO fact_trafico_hora_live
    WITH trafico AS (
        SELECT r.*, s.tipo_elem
        FROM raw_live r
        JOIN dim_sensor s ON r.id_sensor = s.id_sensor
        WHERE r.error <> 'S'
          AND r.fecha >= date_trunc('hour', now() - INTERVAL 1 HOUR)
          AND r.fecha <  date_trunc('hour', now())
    ),
    trafico_hora AS (
        SELECT
            id_sensor,
            DATE_TRUNC('hour', fecha) AS fecha_hora,
            AVG(intensidad) AS intensidad_media,
            MAX(intensidad) AS intensidad_max,
            MIN(intensidad) AS intensidad_min,
            AVG(ocupacion) AS ocupacion_media,
            MAX(ocupacion) AS ocupacion_max,
            CASE WHEN MAX(tipo_elem) = 'URB' THEN 0 ELSE COALESCE(AVG(velocidad_media), 0) END AS velocidad_media,
            CASE WHEN MAX(tipo_elem) = 'URB' THEN 0 ELSE COALESCE(MIN(velocidad_media), 0) END AS velocidad_min,
            COUNT(*) AS num_mediciones,
            SUM(CASE WHEN error='E' THEN 1 ELSE 0 END) AS num_error_E,
            ROUND(100.0 * COUNT(*) FILTER (WHERE error='N') / COUNT(*), 2) AS porcentaje_calidad
        FROM trafico
        GROUP BY id_sensor, fecha_hora
    )
    SELECT
        id_sensor,
        CAST(fecha_hora AS DATE) AS id_fecha,
        EXTRACT(HOUR FROM fecha_hora)::INTEGER AS hora,
        intensidad_media, intensidad_max, intensidad_min,
        ocupacion_media, ocupacion_max,
        velocidad_media, velocidad_min,
        num_mediciones, num_error_E, porcentaje_calidad
    FROM trafico_hora
""")

print("\n=== 3. Resultado del agregado (10 primeras filas) ===")
con.sql("SELECT * FROM fact_trafico_hora_live ORDER BY id_sensor LIMIT 10").show()

print("\n=== 4. Comprobación manual para el sensor 9841 ===")
con.sql("""
    SELECT AVG(intensidad), MAX(intensidad), MIN(intensidad), COUNT(*)
    FROM raw_live WHERE id_sensor = 9841
""").show()
con.sql("SELECT * FROM fact_trafico_hora_live WHERE id_sensor = 9841").show()

print("\n=== 5. Comprobación de join con dim_sensor ===")
con.sql("""
    SELECT COUNT(DISTINCT r.id_sensor) AS en_raw,
           COUNT(DISTINCT s.id_sensor) AS con_match
    FROM raw_live r
    LEFT JOIN dim_sensor s ON r.id_sensor = s.id_sensor
""").show()

con.close()