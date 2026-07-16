import sys
from pathlib import Path
import joblib
import pandas as pd

# src/backend/madflow/app/traffic/services.py
SRC_DIR = Path(__file__).resolve().parents[4]      # .../src
PROJECT_ROOT = SRC_DIR.parent                        # .../Inteligencia-de-movilidad-urbana-de-Madrid

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from etl.features import construir_fila_features

MODELO_PATH = PROJECT_ROOT / "models" / "trafico.pkl"
CATEGORIAS_TIPO_ELEM = ["other", "URB", "M30"]

_modelo = None

def _get_modelo():
    global _modelo
    if _modelo is None:
        _modelo = joblib.load(MODELO_PATH)
    return _modelo

def predecir_sensor(id_sensor: int) -> dict:
    fila, imputados = construir_fila_features(id_sensor)

    X = fila.to_pandas()
    X["tipo_elem"] = pd.Categorical(X["tipo_elem"], categories=CATEGORIAS_TIPO_ELEM)

    modelo = _get_modelo()
    prediccion = modelo.predict(X)[0]

    return {
        "id_sensor": id_sensor,
        "prediccion_ocupacion": float(prediccion),
        "campos_imputados": list(imputados.keys()),
        "confiable": len(imputados) == 0,
    }