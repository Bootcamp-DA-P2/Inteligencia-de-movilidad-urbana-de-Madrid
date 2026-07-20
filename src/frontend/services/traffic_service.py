import requests
from utils import load_config

url_traffic = load_config()['URL_TRAFFIC']

def get_prediction(id_sensor: int, fecha=None, hora=None):
    params = ""
    if fecha and hora is not None:
        params = f"?fecha={fecha}&hora={hora}"
    response = requests.get(url_traffic + f"predict/{id_sensor}/{params}", timeout=15)
    return response

# Distrito
def get_sensores_distrito(id_distrito: int):
    response = requests.get(url_traffic + f"distrito/{id_distrito}/sensores/", timeout=60)
    return response

def get_sensores_distrito(id_distrito: int):
    response = requests.get(url_traffic + f"distrito/{id_distrito}/sensores/", timeout=60)
    return response

def get_evolucion(id_sensor: int, desde: str, hasta: str):
    return requests.get(url_traffic + f"historico/evolucion/{id_sensor}/?desde={desde}&hasta={hasta}", timeout=60)

def get_ranking_distritos(desde: str, hasta: str):
    return requests.get(url_traffic + f"historico/ranking-distritos/?desde={desde}&hasta={hasta}", timeout=15)

def get_patron_horario_distrito(id_distrito: int, desde: str, hasta: str):
    return requests.get(url_traffic + f"historico/patron-horario-distrito/{id_distrito}/?desde={desde}&hasta={hasta}", timeout=60)

def get_patron_semanal_distrito(id_distrito: int, desde: str, hasta: str):
    return requests.get(url_traffic + f"historico/patron-semanal-distrito/{id_distrito}/?desde={desde}&hasta={hasta}", timeout=60)

def get_patron_horario_m30(desde: str, hasta: str):
    return requests.get(url_traffic + f"historico/patron-horario-m30/?desde={desde}&hasta={hasta}", timeout=60)