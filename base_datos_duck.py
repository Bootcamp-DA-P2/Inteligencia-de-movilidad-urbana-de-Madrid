import duckdb
from pathlib import Path


# =====================================================
# RUTAS
# =====================================================

ruta_csv = "data/historico-trafico/*.csv"
ruta_ubicaciones = "data/ubicacion_maestra.csv"
ruta_salida = Path("gold")

ruta_salida.mkdir(exist_ok=True)


# =====================================================
# CONEXIÓN DUCKDB
# =====================================================

con = duckdb.connect("trafico.duckdb")


# =====================================================
# 1. CREAR DIM_SENSOR
# =====================================================

con.execute(f"""

COPY (

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
    )


)

TO '{ruta_salida}/dim_sensor.parquet'
(FORMAT PARQUET);


""")


print("dim_sensor creada")


# =====================================================
# 2. CREAR FACT_TRAFiCO_HORA
# =====================================================

con.execute(f"""

COPY (

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


    -- Eliminamos muestras totalmente erróneas
    WHERE error <> 'S'


),


trafico_hora AS (

    SELECT


        id_sensor,


        DATE_TRUNC(
            'hour',
            fecha
        ) AS fecha_hora,


        AVG(intensidad)
            AS intensidad_media,


        MAX(intensidad)
            AS intensidad_max,


        MIN(intensidad)
            AS intensidad_min,


        AVG(ocupacion)
            AS ocupacion_media,


        MAX(ocupacion)
            AS ocupacion_max,


        AVG(velocidad_media)
            AS velocidad_media,


        MIN(velocidad_media)
            AS velocidad_min,


        COUNT(*)
            AS num_mediciones,


        SUM(
            CASE
                WHEN error='E'
                THEN 1
                ELSE 0
            END
        ) AS num_error_E,


        ROUND(

            100.0 *

            COUNT(*) FILTER(
                WHERE error='N'
            )

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


    CAST(fecha_hora AS DATE)
        AS id_fecha,


    EXTRACT(
        HOUR FROM fecha_hora
    )::INTEGER
        AS hora,


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



FROM trafico_hora



)

TO '{ruta_salida}/fact_trafico_hora.parquet'
(FORMAT PARQUET);


""")


print("fact_trafico_hora creada")


# =====================================================
# 3. CREAR DIM_FECHA
# =====================================================

con.execute(f"""

COPY (

WITH fechas AS (

    SELECT DISTINCT

        id_fecha


    FROM read_parquet(
        '{ruta_salida}/fact_trafico_hora.parquet'
    )


)


SELECT


    id_fecha,


    YEAR(id_fecha)
        AS año,


    MONTH(id_fecha)
        AS mes,


    STRFTIME(
        id_fecha,
        '%B'
    )
        AS nombre_mes,


    QUARTER(id_fecha)
        AS trimestre,


    DAY(id_fecha)
        AS dia,


    DAYOFWEEK(id_fecha)
        AS dia_semana,


    CASE

        WHEN DAYOFWEEK(id_fecha) IN (0,6)

        THEN TRUE

        ELSE FALSE

    END AS fin_semana



FROM fechas



)

TO '{ruta_salida}/dim_fecha.parquet'
(FORMAT PARQUET);


""")


print("dim_fecha creada")


# =====================================================
# CERRAR
# =====================================================

con.close()


print("Proceso terminado correctamente")