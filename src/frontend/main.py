import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="Inteligencia de movilidad urbana de Madrid", page_icon="🚗", layout="wide")

pages = {
        "Inicio": [
            st.Page("pages/home.py", title="Inicio", icon="🏠")
        ],
        "Movilidad":[
            st.Page("pages/mobility.py", title="Movilidad Madrid", icon="🚦"),
        ],
        "Sobre Nosotros":[
            st.Page("pages/about_us.py", title="Sobre Nosotros", icon="🙋🏻")
        ]
    }

pg = st.navigation(pages)
pg.run()