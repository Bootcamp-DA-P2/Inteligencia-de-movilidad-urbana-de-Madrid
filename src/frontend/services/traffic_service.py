import requests
from utils import load_config

url_traffic = load_config()['URL_TRAFFIC']

def get_prediction(id_sensor: int):
    response = requests.get(url_traffic + f"predict/{id_sensor}/", timeout=60)
    return response

# Distrito
def get_sensores_distrito(id_distrito: int):
    response = requests.get(url_traffic + f"distrito/{id_distrito}/sensores/", timeout=60)
    return response

def get_sensores_distrito(id_distrito: int):
    response = requests.get(url_traffic + f"distrito/{id_distrito}/sensores/", timeout=60)
    return response