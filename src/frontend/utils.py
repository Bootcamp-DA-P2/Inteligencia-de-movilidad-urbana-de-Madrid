import os
from dotenv import load_dotenv
import streamlit as st

def load_config():
    load_dotenv()
    config = {
        'URL_AUTH': os.getenv('URL_AUTH'),
        'URL_TRAFFIC': os.getenv('URL_TRAFFIC'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
    }
    return config

DISTRITOS = {
    1: "Centro", 2: "Arganzuela", 3: "Retiro", 4: "Salamanca", 5: "Chamartín",
    6: "Tetuán", 7: "Chamberí", 8: "Fuencarral-El Pardo", 9: "Moncloa-Aravaca",
    10: "Latina", 11: "Carabanchel", 12: "Usera", 13: "Puente de Vallecas",
    14: "Moratalaz", 15: "Ciudad Lineal", 16: "Hortaleza", 17: "Villaverde",
    18: "Villa de Vallecas", 19: "Vicálvaro", 20: "San Blas-Canillejas",
    21: "Barajas",
}