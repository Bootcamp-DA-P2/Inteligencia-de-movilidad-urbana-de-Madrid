import duckdb
import polars as pl
import numpy as np
import datetime
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "trafico.duckdb"

VARIABLES_LAG = ["intensidad_media", "ocupacion_media", "velocidad_media"]
LAGS = [1, 24, 168]

@lru_cache(maxsize=300)
def cargar_historico_sensor(id_sensor):
    con = duckdb.connect(str(DB_PATH), read_only=True)

    historico = con.execute("""
        SELECT
            id_sensor,
            id_fecha,
            hora,
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
        FROM fact_trafico_completa
        WHERE id_sensor = ?
        ORDER BY id_fecha, hora
    """, [id_sensor]).pl()

    metadata = con.execute("""
        SELECT tipo_elem,distrito,latitud,longitud
        FROM dim_sensor
        WHERE id_sensor=?
    """,[id_sensor]).fetchone()

    con.close()

    return historico, metadata


def _duckdb_dia_semana(fecha: datetime.date) -> int:
    # Replica DAYOFWEEK() de DuckDB: 0=domingo ... 6=sábado
    return (fecha.weekday() + 1) % 7


def _climatologia(historico: pl.DataFrame, hora: int, dia_semana: int, variable: str):
    """Media histórica de una variable para esa hora + día de la semana; si no hay
    suficientes datos, cae a la media solo por hora."""
    filtro = historico.filter(
        (pl.col("hora") == hora) & (pl.col("dia_semana") == dia_semana)
    )
    if filtro.height == 0:
        filtro = historico.filter(pl.col("hora") == hora)
    if filtro.height == 0:
        return None
    return filtro[variable].mean()


def construir_fila_features(
    id_sensor: int,
    fecha_hora_objetivo: datetime.datetime | None = None,
) -> tuple[pl.DataFrame, dict]:
    
    imputados = {}

    historico, metadata_sensor = cargar_historico_sensor(id_sensor)
   
    if historico.height == 0 or metadata_sensor is None:
        raise ValueError(f"Sensor {id_sensor}: no hay ningún dato disponible.")

    tipo_elem, distrito, latitud, longitud = metadata_sensor

    historico = historico.with_columns(
        pl.datetime(
            year=pl.col("id_fecha").dt.year(),
            month=pl.col("id_fecha").dt.month(),
            day=pl.col("id_fecha").dt.day(),
            hour=pl.col("hora"),
        ).alias("fecha_hora")
    ).with_columns(
        pl.col("id_fecha").map_elements(_duckdb_dia_semana, return_dtype=pl.Int64).alias("dia_semana")
    )

    # --- Determinar la fecha/hora objetivo: la pedida, o si no se pide ninguna, la más reciente ---
    if fecha_hora_objetivo is None:
        ultima_real = historico.tail(1)
        fecha_hora = ultima_real["fecha_hora"][0]
    else:
        fecha_hora = fecha_hora_objetivo

    hora = fecha_hora.hour
    dia_semana_obj = _duckdb_dia_semana(fecha_hora.date())
    mes = fecha_hora.month

    # --- Buscar si existe un dato REAL exacto para esa fecha/hora ---
    fila_real = historico.filter(pl.col("fecha_hora") == fecha_hora)

    if fila_real.height > 0:
        # Hay dato real (pasado con histórico completo, o última hora en vivo)
        intensidad_media = fila_real["intensidad_media"][0]
        ocupacion_media = fila_real["ocupacion_media"][0]
        velocidad_media = fila_real["velocidad_media"][0]
    else:
        # No hay dato real para esa fecha/hora (futuro, o hueco) → climatología
        intensidad_media = _climatologia(historico, hora, dia_semana_obj, "intensidad_media")
        ocupacion_media = _climatologia(historico, hora, dia_semana_obj, "ocupacion_media")
        velocidad_media = _climatologia(historico, hora, dia_semana_obj, "velocidad_media")
        imputados["fila_base"] = True  # marca que TODA la fila base es estimada, no real

    fila = {
        "id_sensor": id_sensor, "hora": hora,
        "intensidad_media": intensidad_media,
        "intensidad_max": intensidad_media,
        "intensidad_min": intensidad_media,
        "ocupacion_media": ocupacion_media,
        "ocupacion_max": ocupacion_media,
        "velocidad_media": velocidad_media,
        "velocidad_min": velocidad_media,
        "num_mediciones": 1, "num_error_E": 0, "porcentaje_calidad": 100.0,
        "año": fecha_hora.year, "mes": mes, "trimestre": (mes - 1) // 3 + 1, "dia": fecha_hora.day,
        "dia_semana": dia_semana_obj, "fin_semana": dia_semana_obj in (0, 6),
        "tipo_elem": tipo_elem, "distrito": distrito, "latitud": latitud, "longitud": longitud,
        "hora_sin": np.sin(2 * np.pi * hora / 24), "hora_cos": np.cos(2 * np.pi * hora / 24),
        "dia_semana_sin": np.sin(2 * np.pi * dia_semana_obj / 7), "dia_semana_cos": np.cos(2 * np.pi * dia_semana_obj / 7),
        "mes_sin": np.sin(2 * np.pi * mes / 12), "mes_cos": np.cos(2 * np.pi * mes / 12),
    }

    # --- Lags: buscar en memoria, si no existe usar climatología (también en memoria) ---
    for variable in VARIABLES_LAG:
        for lag in LAGS:
            objetivo = fecha_hora - datetime.timedelta(hours=lag)
            fila_objetivo = historico.filter(pl.col("fecha_hora") == objetivo)
            clave = f"{variable}_lag_{lag}"

            if fila_objetivo.height > 0 and fila_objetivo[variable][0] is not None:
                fila[clave] = fila_objetivo[variable][0]
            else:
                dia_semana_lag = _duckdb_dia_semana(objetivo.date())
                valor = _climatologia(historico, objetivo.hour, dia_semana_lag, variable)
                fila[clave] = valor
                imputados[clave] = True

    # --- Rolling: climatología general del sensor (media/std de toda la serie) ---
    for variable, sufijo in [("intensidad_media", "intensidad"), ("ocupacion_media", "ocupacion")]:
        for ventana in [3, 24]:
            fila[f"rolling_{sufijo}_mean_{ventana}"] = historico[variable].mean()
            imputados[f"rolling_{sufijo}_mean_{ventana}"] = True
        fila[f"rolling_{sufijo}_std_24"] = historico[variable].std()
        imputados[f"rolling_{sufijo}_std_24"] = True

    # --- Deltas ---
    fila["delta_intensidad_1"] = fila["intensidad_media"] - fila["intensidad_media_lag_1"]
    fila["delta_intensidad_24"] = fila["intensidad_media"] - fila["intensidad_media_lag_24"]
    fila["delta_ocupacion_1"] = fila["ocupacion_media"] - fila["ocupacion_media_lag_1"]
    fila["delta_ocupacion_24"] = fila["ocupacion_media"] - fila["ocupacion_media_lag_24"]

    df = pl.DataFrame([fila])
    return df, imputados

from functools import lru_cache

if __name__ == "__main__":
    fila, imputados = construir_fila_features(9841)
    print(fila)
    print("\nCampos imputados:", list(imputados.keys()))

    # Prueba con una fecha futura (dentro de una semana, por ejemplo)
    futuro = datetime.datetime.now() + datetime.timedelta(days=7)
    futuro = futuro.replace(minute=0, second=0, microsecond=0)
    fila2, imputados2 = construir_fila_features(9841, fecha_hora_objetivo=futuro)
    print(f"\n--- Predicción para {futuro} (futuro) ---")
    print(fila2)
    print("Campos imputados:", list(imputados2.keys()))