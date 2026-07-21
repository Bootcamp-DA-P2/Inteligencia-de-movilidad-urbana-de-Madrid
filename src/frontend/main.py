import os
import sys
import streamlit as st

# Importamos las funciones de renderizado
from pages.login import show_login_page
from pages.register import show_register_page
from pathlib import Path

# La carpeta assets/ está en la raíz del repo (dos niveles arriba de src/frontend)
LOGO_PATH = str(Path(__file__).resolve().parents[2] / "assets" / "logomadrid.png")

# --- CONFIGURACIÓN DE DESARROLLO ---
# Cambia esto a False cuando quieras que el login sea obligatorio
DEVELOPMENT_MODE = True 
# -----------------------------------

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(
    page_title="Inteligencia de movilidad urbana de Madrid",
    page_icon="🚗",
    layout="wide"
)

from theme import apply_theme
apply_theme()

from theme import apply_theme
apply_theme()
st.logo(LOGO_PATH)   # fija el logo en el tope del sidebar, arriba del menú

# 2. Inicializar estado de la sesión
if "logged_in" not in st.session_state:
    # Si estamos en modo desarrollo, iniciamos directamente como logueados
    if DEVELOPMENT_MODE:
        st.session_state["logged_in"] = True
    else:
        st.session_state["logged_in"] = False

if "page" not in st.session_state:
    st.session_state["page"] = "login"

# 3. Navegación dinámica
if not st.session_state["logged_in"]:
    # Ocultar la barra lateral (Sidebar) mientras no esté logueado
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
    # Si está logueado (o estamos en modo desarrollo), construimos el menú
    
    # Opcional: Añadir un botón para salir en modo desarrollo
    if DEVELOPMENT_MODE:
        st.sidebar.warning("Modo Desarrollo Activo: Login saltado")
        if st.sidebar.button("Forzar Logout"):
            st.session_state["logged_in"] = False
            st.rerun()

    pages = {
        "Inicio": [
            st.Page("pages/home.py", title="Inicio", icon="🏠")
        ],
        "Movilidad": [
            st.Page("pages/mobility.py", title="Movilidad Madrid", icon="🚦")
        ],
        "Sobre Nosotros": [
            st.Page("pages/about_us.py", title="Sobre Nosotros", icon="🙋🏻")
        ],
        "Dashboard": [
            st.Page("pages/dashboard.py", title="Dashboard histórico", icon="📊")
        ],

    }

    pg = st.navigation(pages)
    pg.run()