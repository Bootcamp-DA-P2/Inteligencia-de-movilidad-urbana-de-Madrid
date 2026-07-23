import sys
from pathlib import Path
import joblib
import pandas as pd
import duckdb
import datetime
from functools import lru_cache

UMBRAL_BAJO_MEDIO = 1.0
UMBRAL_MEDIO_ALTO = 4.06

# src/backend/madflow/app/traffic/services.py
SRC_DIR = Path(__file__).resolve().parents[4]      # .../src
PROJECT_ROOT = SRC_DIR.parent                        # .../Inteligencia-de-movilidad-urbana-de-Madrid

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from etl.features import construir_fila_features

MODELO_PATH = PROJECT_ROOT / "models" / "trafico.pkl"
DB_PATH = PROJECT_ROOT / "database" / "trafico.duckdb"
CATEGORIAS_TIPO_ELEM = ["other", "URB", "M30"]

_modelo = None

def _get_modelo():
    global _modelo
    if _modelo is None:
        _modelo = joblib.load(MODELO_PATH)
    return _modelo

@lru_cache(maxsize=5000)
def predecir_sensor(id_sensor: int, fecha_hora: datetime.datetime | None = None) -> dict:
    fila, imputados = construir_fila_features(id_sensor, fecha_hora_objetivo=fecha_hora)

    X = fila.to_pandas()
    X["tipo_elem"] = pd.Categorical(X["tipo_elem"], categories=CATEGORIAS_TIPO_ELEM)

    modelo = _get_modelo()
    prediccion = modelo.predict(X)[0]

    con = duckdb.connect(str(DB_PATH), read_only=True)

    ultima = con.execute("""
        SELECT id_fecha, hora
        FROM fact_trafico_hora_live
        ORDER BY id_fecha DESC, hora DESC
        LIMIT 1
    """).fetchone()

    con.close()

    ultima_hora_datos = (
        f"{ultima[1]:02d}:00"
        if ultima is not None
        else None
    )

    return {
        "id_sensor": id_sensor,
        "prediccion_ocupacion": float(prediccion),
        "nivel_congestion": clasificar_congestion(float(prediccion)),
        "campos_imputados": list(imputados.keys()),
        "confiable": len(imputados) == 0,
        "ultima_hora_datos": ultima_hora_datos,
    }

# Districto
def obtener_sensores_por_distrito(id_distrito: int) -> list[dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    resultado = con.execute(
        """
        SELECT id_sensor, cod_cent, nombre_norm, nombre_calle, latitud, longitud
        FROM dim_sensor
        WHERE distrito = ?
        ORDER BY id_sensor
        """,
        [id_distrito]
    ).fetchall()
    con.close()

    return [
        {
            "id_sensor": fila[0],
            "cod_cent": fila[1],
            "nombre_norm": fila[2],
            "nombre_calle": fila[3],
            "latitud": fila[4],
            "longitud": fila[5],
        }
        for fila in resultado
    ]

def clasificar_congestion(ocupacion: float) -> str:
    if ocupacion < UMBRAL_BAJO_MEDIO:
        return "bajo"
    elif ocupacion < UMBRAL_MEDIO_ALTO:
        return "medio"
    else:
        return "alto"

def obtener_evolucion_sensor(id_sensor: int, fecha_inicio: str, fecha_fin: str) -> list[dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    resultado = con.execute("""
        SELECT id_fecha, hora, intensidad_media, ocupacion_media
        FROM fact_trafico_hora
        WHERE id_sensor = ? AND id_fecha BETWEEN ? AND ?
        ORDER BY id_fecha, hora
    """, [id_sensor, fecha_inicio, fecha_fin]).fetchall()
    con.close()
    return [
        {"fecha": str(r[0]), "hora": r[1], "intensidad_media": r[2], "ocupacion_media": r[3]}
        for r in resultado
    ]


def obtener_patron_horario_distrito(id_distrito: int, fecha_inicio: str, fecha_fin: str) -> list[dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    resultado = con.execute("""
        SELECT f.hora, AVG(f.ocupacion_media) AS ocupacion_media, AVG(f.intensidad_media) AS intensidad_media
        FROM fact_trafico_hora f
        JOIN dim_sensor s ON f.id_sensor = s.id_sensor
        WHERE s.distrito = ? AND f.id_fecha BETWEEN ? AND ?
        GROUP BY f.hora
        ORDER BY f.hora
    """, [id_distrito, fecha_inicio, fecha_fin]).fetchall()
    con.close()
    return [{"hora": r[0], "ocupacion_media": r[1], "intensidad_media": r[2]} for r in resultado]


def obtener_patron_semanal_distrito(id_distrito: int, fecha_inicio: str, fecha_fin: str) -> list[dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    resultado = con.execute("""
        SELECT d.dia_semana, AVG(f.ocupacion_media) AS ocupacion_media
        FROM fact_trafico_hora f
        JOIN dim_sensor s ON f.id_sensor = s.id_sensor
        JOIN dim_fecha d ON f.id_fecha = d.id_fecha
        WHERE s.distrito = ? AND f.id_fecha BETWEEN ? AND ?
        GROUP BY d.dia_semana
        ORDER BY d.dia_semana
    """, [id_distrito, fecha_inicio, fecha_fin]).fetchall()
    con.close()
    return [{"dia_semana": r[0], "ocupacion_media": r[1]} for r in resultado]


def obtener_ranking_distritos_historico(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    resultado = con.execute("""
        SELECT s.distrito, AVG(f.ocupacion_media) AS ocupacion_media
        FROM fact_trafico_hora f
        JOIN dim_sensor s ON f.id_sensor = s.id_sensor
        WHERE f.id_fecha BETWEEN ? AND ?
        GROUP BY s.distrito
        ORDER BY ocupacion_media DESC
    """, [fecha_inicio, fecha_fin]).fetchall()
    con.close()
    return [{"distrito": r[0], "ocupacion_media": r[1]} for r in resultado]

def obtener_patron_horario_m30(fecha_inicio: str, fecha_fin: str) -> list[dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    resultado = con.execute("""
        SELECT f.hora,
               AVG(f.velocidad_media) AS velocidad_media,
               AVG(f.ocupacion_media) AS ocupacion_media,
               AVG(f.intensidad_media) AS intensidad_media
        FROM fact_trafico_hora f
        JOIN dim_sensor s ON f.id_sensor = s.id_sensor
        WHERE s.tipo_elem = 'M30' AND f.id_fecha BETWEEN ? AND ?
        GROUP BY f.hora
        ORDER BY f.hora
    """, [fecha_inicio, fecha_fin]).fetchall()
    con.close()
    return [
        {"hora": r[0], "velocidad_media": r[1], "ocupacion_media": r[2], "intensidad_media": r[3]}
        for r in resultado
    ]