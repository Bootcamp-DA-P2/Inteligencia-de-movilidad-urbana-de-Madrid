import duckdb
import polars as pl
import numpy as np
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "trafico.duckdb"

VARIABLES_LAG = ["intensidad_media", "ocupacion_media", "velocidad_media"]
LAGS = [1, 24, 168]


def _duckdb_dia_semana(fecha: datetime.date) -> int:
    # Replica DAYOFWEEK() de DuckDB: 0=domingo ... 6=sábado
    return (fecha.weekday() + 1) % 7


def construir_fila_features(id_sensor: int) -> tuple[pl.DataFrame, dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    imputados = {}

    # --- UNA sola consulta: todo el histórico del sensor ---
    historico = con.execute("""
        SELECT id_fecha, hora, intensidad_media, ocupacion_media, velocidad_media
        FROM fact_trafico_completa
        WHERE id_sensor = ?
        ORDER BY id_fecha, hora
    """, [id_sensor]).pl()

    metadata_sensor = con.execute("""
        SELECT tipo_elem, distrito, latitud, longitud FROM dim_sensor WHERE id_sensor = ?
    """, [id_sensor]).fetchone()
    con.close()

    if historico.height == 0 or metadata_sensor is None:
        raise ValueError(f"Sensor {id_sensor}: no hay ningún dato disponible.")

    tipo_elem, distrito, latitud, longitud = metadata_sensor

    historico = historico.with_columns(
        pl.col("id_fecha").cast(pl.Datetime).dt.combine(
            pl.duration(hours="hora")
        ) if False else pl.datetime(
            year=pl.col("id_fecha").dt.year(),
            month=pl.col("id_fecha").dt.month(),
            day=pl.col("id_fecha").dt.day(),
            hour=pl.col("hora"),
        ).alias("fecha_hora")
    ).with_columns(
        pl.col("id_fecha").map_elements(_duckdb_dia_semana, return_dtype=pl.Int64).alias("dia_semana")
    )

    # --- Fila actual = la hora más reciente disponible ---
    ultima = historico.tail(1)
    id_fecha = ultima["id_fecha"][0]
    hora = ultima["hora"][0]
    fecha_hora = ultima["fecha_hora"][0]
    dia_semana = ultima["dia_semana"][0]
    mes = fecha_hora.month

    fila = {
        "id_sensor": id_sensor, "hora": hora,
        "intensidad_media": ultima["intensidad_media"][0],
        "intensidad_max": ultima["intensidad_media"][0],   # ver nota abajo
        "intensidad_min": ultima["intensidad_media"][0],
        "ocupacion_media": ultima["ocupacion_media"][0],
        "ocupacion_max": ultima["ocupacion_media"][0],
        "velocidad_media": ultima["velocidad_media"][0],
        "velocidad_min": ultima["velocidad_media"][0],
        "num_mediciones": 1, "num_error_E": 0, "porcentaje_calidad": 100.0,
        "año": fecha_hora.year, "mes": mes, "trimestre": (mes - 1) // 3 + 1, "dia": fecha_hora.day,
        "dia_semana": dia_semana, "fin_semana": dia_semana in (0, 6),
        "tipo_elem": tipo_elem, "distrito": distrito, "latitud": latitud, "longitud": longitud,
        "hora_sin": np.sin(2 * np.pi * hora / 24), "hora_cos": np.cos(2 * np.pi * hora / 24),
        "dia_semana_sin": np.sin(2 * np.pi * dia_semana / 7), "dia_semana_cos": np.cos(2 * np.pi * dia_semana / 7),
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
                dia_semana_obj = _duckdb_dia_semana(objetivo.date())
                climatologia = historico.filter(
                    (pl.col("hora") == objetivo.hour) & (pl.col("dia_semana") == dia_semana_obj)
                )
                if climatologia.height == 0:
                    climatologia = historico.filter(pl.col("hora") == objetivo.hour)
                valor = climatologia[variable].mean() if climatologia.height > 0 else None
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


if __name__ == "__main__":
    fila, imputados = construir_fila_features(9841)
    print(fila)
    print("\nCampos imputados:", list(imputados.keys()))