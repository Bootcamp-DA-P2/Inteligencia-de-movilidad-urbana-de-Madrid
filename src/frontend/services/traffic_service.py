import requests
from utils import load_config

url_traffic = load_config()['URL_TRAFFIC']

def get_prediction(id_sensor: int):
    response = requests.get(url_traffic + f"predict/{id_sensor}/", timeout=15)
    return response