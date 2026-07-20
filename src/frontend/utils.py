import os
from dotenv import load_dotenv
import streamlit as st

def load_config():
    load_dotenv()
    config = {
        'URL_AUTH': os.getenv('URL_AUTH'),
        'URL_TRAFFIC': os.getenv('URL_TRAFFIC'),
    }
    return config