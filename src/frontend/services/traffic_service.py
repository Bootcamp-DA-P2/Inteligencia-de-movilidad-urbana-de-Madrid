import requests
from utils import load_config

# Cargamos la URL base de la API de tráfico desde el archivo de configuración
url_traffic = load_config()["URL_TRAFFIC"]

# PREDICCIONES PUNTUALES Y EN BATCH

def get_prediction(id_sensor: int, fecha=None, hora=None):
    """Pide la predicción de tráfico para un sensor en concreto.
       Si pasamos fecha y hora se añade como query param; si no, el backend
       asume tiempo real/próxima hora disponible.
    """
    params = ""
    if fecha and hora is not None:
        params = f"?fecha={fecha}&hora={hora}"

    return requests.get(
        url_traffic + f"predict/{id_sensor}/{params}",
        timeout=40, # Timeout generoso por si el modelo ML tarda en inferir
    )


def get_predictions_batch(sensores: list[int], fecha=None, hora=None):
    """Lanza una petición masiva (POST) para obtener predicciones de varios sensores.
       Se usa en la búsqueda de rutas alternativas para no saturar con N peticiones individuales.
    """
    payload = {
        "sensores": sensores,
    }

    if fecha:
        payload["fecha"] = fecha

    if hora is not None:
        payload["hora"] = hora

    return requests.post(
        url_traffic + "predict/batch/",
        json=payload,
        timeout=120, # 2 minutos de margen porque procesar una lista de sensores pesa más
    )


# CONSULTAS POR DISTRITO Y HISTÓRICOS

def get_sensores_distrito(id_distrito: int):
    """Obtiene el listado con la información de todos los sensores de un distrito."""
    return requests.get(
        url_traffic + f"distrito/{id_distrito}/sensores/",
        timeout=60,
    )


def get_evolucion(id_sensor: int, desde: str, hasta: str):
    """Trae la serie temporal histórica de ocupación para un sensor entre dos fechas."""
    return requests.get(
        url_traffic + f"historico/evolucion/{id_sensor}/?desde={desde}&hasta={hasta}",
        timeout=60,
    )


def get_ranking_distritos(desde: str, hasta: str):
    """Consulta el ranking de distritos más/menos congestionados en un periodo."""
    return requests.get(
        url_traffic + f"historico/ranking-distritos/?desde={desde}&hasta={hasta}",
        timeout=15,
    )


def get_patron_horario_distrito(id_distrito: int, desde: str, hasta: str):
    """Obtiene el promedio de tráfico hora a hora (0-23h) para un distrito."""
    return requests.get(
        url_traffic + f"historico/patron-horario-distrito/{id_distrito}/?desde={desde}&hasta={hasta}",
        timeout=60,
    )


def get_patron_semanal_distrito(id_distrito: int, desde: str, hasta: str):
    """Obtiene la tendencia de ocupación por día de la semana (Lunes a Domingo)."""
    return requests.get(
        url_traffic + f"historico/patron-semanal-distrito/{id_distrito}/?desde={desde}&hasta={hasta}",
        timeout=60,
    )


def get_patron_horario_m30(desde: str, hasta: str):
    """Obtiene los patrones horarios específicos para los sensores de la M-30."""
    return requests.get(
        url_traffic + f"historico/patron-horario-m30/?desde={desde}&hasta={hasta}",
        timeout=60,
    )

# RUTAS GENERALES

def get_todos_los_sensores():
   """Descarga de golpe todos los sensores de Madrid.    
      Ideal para mapas globales o cuando necesitamos la red completa sin filtrar por distrito.
    """
   return requests.get(url_traffic + "sensores/", timeout=60)