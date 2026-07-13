import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="Inteligencia de movilidad urbana de Madrid", page_icon="🚗", layout="wide")
# 2. Inicializar estado
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "page" not in st.session_state:
    st.session_state["page"] = "login"

# 3. Navegación dinámica
if not st.session_state["logged_in"]:
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """, unsafe_allow_html=True)
    # Si no está logueado, mostrar login o registro
    if st.session_state["page"] == "login":
        st.Page("pages/login.py")
    else:
        st.Page("pages/register.py")
else:
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