import duckdb
from pathlib import Path


# =====================================================
# RUTAS
# =====================================================

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data"
DATABASE = ROOT / "database"

ruta_csv = str(DATA / "raw" / "historico-trafico" / "*.csv")
ruta_ubicaciones = str(DATA / "raw" / "ubicacion_maestra.csv")
ruta_salida = DATA / "gold"

DATABASE.mkdir(exist_ok=True)
ruta_salida.mkdir(parents=True, exist_ok=True)

# =====================================================
# CONEXIÓN DUCKDB
# =====================================================

con = duckdb.connect(str(DATABASE / "trafico.duckdb"))

print("Conexión establecida con DuckDB")

# =====================================================
# 1. CREAR DIM_SENSOR
# =====================================================

print("Creando dim_sensor...")

con.execute(f"""

CREATE OR REPLACE TABLE dim_sensor AS

SELECT DISTINCT

    CAST(id AS INTEGER) AS id_sensor,

    tipo_elem,

    CAST(distrito AS INTEGER) AS distrito,

    cod_cent,

    nombre_norm,

    CAST(utm_x AS DOUBLE) AS utm_x,

    CAST(utm_y AS DOUBLE) AS utm_y,

    CAST(latitud AS DOUBLE) AS latitud,

    CAST(longitud AS DOUBLE) AS longitud

FROM read_csv(

    '{ruta_ubicaciones}',

    delim=',',

    header=true,

    types={{
        'id':'INTEGER',
        'tipo_elem':'VARCHAR',
        'distrito':'INTEGER',
        'cod_cent':'VARCHAR',
        'utm_x':'DOUBLE',
        'utm_y':'DOUBLE',
        'latitud':'DOUBLE',
        'longitud':'DOUBLE',
        'nombre_norm':'VARCHAR'
    }}

);

""")

con.execute(f"""

COPY dim_sensor

TO '{ruta_salida / "dim_sensor.parquet"}'

(FORMAT PARQUET);

""")

print("dim_sensor creada")


# =====================================================
# 2. CREAR FACT_TRÁFICO_HORA
# =====================================================

print("Creando fact_trafico_hora...")

con.execute(f"""

CREATE OR REPLACE TABLE fact_trafico_hora AS

WITH trafico AS (

    SELECT

        CAST(id AS INTEGER) AS id_sensor,

        CAST(fecha AS TIMESTAMP) AS fecha,

        intensidad,

        ocupacion,

        carga,

        vmed AS velocidad_media,

        error,

        periodo_integracion

    FROM read_csv(

        '{ruta_csv}',

        delim=';',

        header=true,

        nullstr='NaN',

        types={{

            'id':'INTEGER',

            'fecha':'TIMESTAMP',

            'tipo_elem':'VARCHAR',

            'intensidad':'DOUBLE',

            'ocupacion':'DOUBLE',

            'carga':'DOUBLE',

            'vmed':'DOUBLE',

            'error':'VARCHAR',

            'periodo_integracion':'INTEGER'

        }}

    )

    -- Eliminamos registros totalmente erróneos
    WHERE error <> 'S'

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

        AVG(velocidad_media) AS velocidad_media,

        MIN(velocidad_media) AS velocidad_min,

        COUNT(*) AS num_mediciones,

        SUM(
            CASE
                WHEN error='E' THEN 1
                ELSE 0
            END
        ) AS num_error_E,

        ROUND(

            100.0 *

            COUNT(*) FILTER (WHERE error='N')

            /

            COUNT(*),

            2

        ) AS porcentaje_calidad

    FROM trafico

    GROUP BY

        id_sensor,

        fecha_hora

)

SELECT

    id_sensor,

    CAST(fecha_hora AS DATE) AS id_fecha,

    EXTRACT(HOUR FROM fecha_hora)::INTEGER AS hora,

    intensidad_media,

    intensidad_max,

    intensidad_min,

    ocupacion_media,

    ocupacion_max,

    velocidad_media,

    velocidad_min,

    num_mediciones,

    num_error_E,

    porcentaje_calidad

FROM trafico_hora;

""")

con.execute(f"""

COPY fact_trafico_hora

TO '{ruta_salida / "fact_trafico_hora.parquet"}'

(FORMAT PARQUET);

""")

print("fact_trafico_hora creada")


# =====================================================
# 3. CREAR DIM_FECHA
# =====================================================

print("Creando dim_fecha...")

con.execute("""

CREATE OR REPLACE TABLE dim_fecha AS

WITH fechas AS (

    SELECT DISTINCT

        id_fecha

    FROM fact_trafico_hora

)

SELECT

    id_fecha,

    YEAR(id_fecha) AS año,

    MONTH(id_fecha) AS mes,

    STRFTIME(id_fecha, '%B') AS nombre_mes,

    QUARTER(id_fecha) AS trimestre,

    DAY(id_fecha) AS dia,

    DAYOFWEEK(id_fecha) AS dia_semana,

    CASE

        WHEN DAYOFWEEK(id_fecha) IN (0, 6)

        THEN TRUE

        ELSE FALSE

    END AS fin_semana

FROM fechas;

""")

con.execute(f"""

COPY dim_fecha

TO '{ruta_salida / "dim_fecha.parquet"}'

(FORMAT PARQUET);

""")

print("dim_fecha creada")


# =====================================================
# CERRAR CONEXIÓN
# =====================================================

con.close()

print("\nProceso completado correctamente")
print(f"Base de datos creada: {DATABASE / 'trafico.duckdb'}")
print(f"Archivos Parquet exportados en: {ruta_salida}")