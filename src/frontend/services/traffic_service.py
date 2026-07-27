import requests
from utils import load_config

url_traffic = load_config()["URL_TRAFFIC"]


def get_prediction(id_sensor: int, fecha=None, hora=None):
    params = ""
    if fecha and hora is not None:
        params = f"?fecha={fecha}&hora={hora}"

    return requests.get(
        url_traffic + f"predict/{id_sensor}/{params}",
        timeout=40,
    )


def get_predictions_batch(sensores: list[int], fecha=None, hora=None):
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
        timeout=120,
    )


# Distrito
def get_sensores_distrito(id_distrito: int):
    return requests.get(
        url_traffic + f"distrito/{id_distrito}/sensores/",
        timeout=60,
    )


def get_evolucion(id_sensor: int, desde: str, hasta: str):
    return requests.get(
        url_traffic + f"historico/evolucion/{id_sensor}/?desde={desde}&hasta={hasta}",
        timeout=60,
    )


def get_ranking_distritos(desde: str, hasta: str):
    return requests.get(
        url_traffic + f"historico/ranking-distritos/?desde={desde}&hasta={hasta}",
        timeout=15,
    )


def get_patron_horario_distrito(id_distrito: int, desde: str, hasta: str):
    return requests.get(
        url_traffic + f"historico/patron-horario-distrito/{id_distrito}/?desde={desde}&hasta={hasta}",
        timeout=60,
    )


def get_patron_semanal_distrito(id_distrito: int, desde: str, hasta: str):
    return requests.get(
        url_traffic + f"historico/patron-semanal-distrito/{id_distrito}/?desde={desde}&hasta={hasta}",
        timeout=60,
    )


def get_patron_horario_m30(desde: str, hasta: str):
    return requests.get(
        url_traffic + f"historico/patron-horario-m30/?desde={desde}&hasta={hasta}",
        timeout=60,
    )