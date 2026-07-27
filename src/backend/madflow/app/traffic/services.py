import sys
from pathlib import Path
import joblib
import pandas as pd
import duckdb
import datetime

# Umbrales fijos para etiquetar el nivel de congestión según la ocupación predicha
UMBRAL_BAJO_MEDIO = 1.0
UMBRAL_MEDIO_ALTO = 4.06

# Configuración de rutas relativas para ubicar la raíz del proyecto y el PYTHONPATH
# src/backend/madflow/app/traffic/services.py
SRC_DIR = Path(__file__).resolve().parents[4]      # .../src
PROJECT_ROOT = SRC_DIR.parent                        # .../Inteligencia-de-movilidad-urbana-de-Madrid

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from etl.features import construir_fila_features

# Rutas al modelo entrenado (.pkl) y a la base de datos analítica (DuckDB)
MODELO_PATH = PROJECT_ROOT / "models" / "trafico.pkl"
DB_PATH = PROJECT_ROOT / "database" / "trafico.duckdb"
CATEGORIAS_TIPO_ELEM = ["other", "URB", "M30"]

# Variable global para cachear el modelo en memoria y no cargarlo en cada petición
_modelo = None

def _get_modelo():
    """Carga perezosa (Lazy Loading) del modelo de Machine Learning.    
       Se asegura de leer el fichero .pkl una sola vez para que las siguientes 
       predicciones vuelen sin penalizar la CPU.
    """
    global _modelo
    if _modelo is None:
        _modelo = joblib.load(MODELO_PATH)
    return _modelo

def predecir_sensor(id_sensor: int, fecha_hora: datetime.datetime | None = None) -> dict:
    """Construye las features de un sensor, ejecuta el modelo y devuelve la predicción."""
    fila, imputados = construir_fila_features(id_sensor, fecha_hora_objetivo=fecha_hora)

    X = fila.to_pandas()
    # Forzamos las categorías exactas que espera el modelo para evitar desajustes
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


def predecir_sensores_batch(ids_sensores: list[int], fecha_hora: datetime.datetime | None = None) -> list[dict]:
    """Predicción para varios sensores a la vez.
       Reutiliza predecir_sensor() para cada id, uno a uno: no cambia el
       modelo ni la lógica de predicción, solo evita que el frontend tenga
       que hacer una petición HTTP por cada sensor. Si un sensor concreto
       falla (por ejemplo, sin histórico suficiente), se omite del resultado
       en vez de tirar toda la petición abajo.
    """
    resultados = []
    for id_sensor in ids_sensores:
        try:
            resultados.append(predecir_sensor(int(id_sensor), fecha_hora=fecha_hora))
        except ValueError:
            continue
    return resultados

# CONSULTAS DE SENSORES (DISTRITOS)

def obtener_sensores_por_distrito(id_distrito: int) -> list[dict]:
    """Conexión de solo lectura a DuckDB para rescatar los sensores de un distrito."""
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


def obtener_todos_los_sensores() -> list[dict]:
    """Trae los sensores de TODOS los distritos en una sola conexión/consulta.
       Antes, el frontend pedía distrito a distrito (21 peticiones, 21
       conexiones a DuckDB abiertas y cerradas una detrás de otra). Esta
       función hace lo mismo que 21 llamadas a obtener_sensores_por_distrito
       juntas, pero en una sola conexión y una sola consulta, que es donde
       estaba el coste real (no en cómo se lanzaban las peticiones desde
       fuera, sino en cuántas veces se abría la base de datos).
    """
    con = duckdb.connect(str(DB_PATH), read_only=True)
    resultado = con.execute(
        """
        SELECT id_sensor, cod_cent, nombre_norm, nombre_calle, latitud, longitud, distrito
        FROM dim_sensor
        ORDER BY distrito, id_sensor
        """
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
            "distrito": fila[6],
        }
        for fila in resultado
    ]

def clasificar_congestion(ocupacion: float) -> str:
    """Mapea el valor numérico de ocupación a una etiqueta de texto legible."""
    if ocupacion < UMBRAL_BAJO_MEDIO:
        return "bajo"
    elif ocupacion < UMBRAL_MEDIO_ALTO:
        return "medio"
    else:
        return "alto"

# HISTÓRICOS Y PATRONES ANALÍTICOS

def obtener_evolucion_sensor(id_sensor: int, fecha_inicio: str, fecha_fin: str) -> list[dict]:
    """Extrae la serie temporal de intensidad y ocupación para un sensor y rango de fechas."""
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
    """Calcula la media de tráfico hora a hora (0-23h) agrupando los sensores de un distrito."""
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
    """Agrega el tráfico por día de la semana (Lunes-Domingo) para un distrito concreto."""
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
    """Ordena los distritos de mayor a menor congestión media en un periodo de fechas."""
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
    """Obtiene los patrones horarios de velocidad, ocupación e intensidad específicos para la M-30."""
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