import os
import sys
import streamlit as st

# Importamos las funciones de renderizado de tus archivos de login y registro
# Nota: Asegúrate de que login.py y register.py definan estas funciones (abajo te muestro cómo adaptarlos)
from pages.login import show_login_page
from pages.register import show_register_page

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(
    page_title="Inteligencia de movilidad urbana de Madrid",
    page_icon="🚗",
    layout="wide"
)

# 2. Inicializar estado de la sesión
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "page" not in st.session_state:
    st.session_state["page"] = "login"

# 3. Navegación dinámica
if not st.session_state["logged_in"]:
    # Ocultar la barra lateral (Sidebar) usando CSS inyectado mientras no esté logueado
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """, unsafe_allow_html=True)
    
    # Renderizado directo sin pasar por st.navigation
    if st.session_state["page"] == "login":
        show_login_page()
    else:
        show_register_page()
else:
    # Si está logueado, construimos el menú con st.navigation
    # Aquí puedes pasar tanto rutas a archivos "pages/..." como funciones directas si quisieras
    pages = {
        "Inicio": [
            st.Page("pages/home.py", title="Inicio", icon="🏠")
        ],
        "Movilidad": [
            st.Page("pages/mobility.py", title="Movilidad Madrid", icon="🚦")
        ],
        "Sobre Nosotros": [
            st.Page("pages/about_us.py", title="Sobre Nosotros", icon="🙋🏻")
        ]
    }

    pg = st.navigation(pages)
    pg.run()