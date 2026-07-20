import sys
from pathlib import Path
import joblib
import pandas as pd
import duckdb
import datetime

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

def predecir_sensor(id_sensor: int, fecha_hora: datetime.datetime | None = None) -> dict:
    fila, imputados = construir_fila_features(id_sensor, fecha_hora_objetivo=fecha_hora)

    X = fila.to_pandas()
    X["tipo_elem"] = pd.Categorical(X["tipo_elem"], categories=CATEGORIAS_TIPO_ELEM)

    modelo = _get_modelo()
    prediccion = modelo.predict(X)[0]

    return {
        "id_sensor": id_sensor,
        "prediccion_ocupacion": float(prediccion),
        "nivel_congestion": clasificar_congestion(float(prediccion)),
        "campos_imputados": list(imputados.keys()),
        "confiable": len(imputados) == 0,
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