import os
import sys
import streamlit as st
from pathlib import Path

# Importamos las funciones de renderizado
from views.login import show_login_page
from views.register import show_register_page


# La carpeta assets/ está en la raíz del repo (dos niveles arriba de src/frontend)
LOGO_PATH = str(Path(__file__).resolve().parents[2] / "assets" / "logomadrid.png")
MADFLOW_PATH = str(Path(__file__).resolve().parents[2] / "assets" / "madflow.png")


# CONFIGURACIÓN DE DESARROLLO
# Cambia esto a False cuando quieras que el login sea obligatorio
DEVELOPMENT_MODE = True


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# CONFIGURACIÓN INICIAL
st.set_page_config(
    page_title="MadFlow",
    page_icon=MADFLOW_PATH,
    layout="wide"
)


from theme import apply_theme

st.logo(MADFLOW_PATH)
apply_theme()


# Inicializar estado de sesión
if "logged_in" not in st.session_state:
    if DEVELOPMENT_MODE:
        st.session_state["logged_in"] = True
    else:
        st.session_state["logged_in"] = False


if "page" not in st.session_state:
    st.session_state["page"] = "login"


# Navegación dinámica

if not st.session_state["logged_in"]:

    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    if st.session_state["page"] == "login":
        show_login_page()
    else:
        show_register_page()


else:

    pages = [
        st.Page(
            "views/home.py",
            title="Inicio",
            icon=":material/home:",
            default=True
        ),
        st.Page(
            "views/dashboard.py",
            title="Análisis histórico",
            icon=":material/analytics:"
        ),
        st.Page(
            "views/mobility.py",
            title="Movilidad predictiva",
            icon=":material/auto_graph:"
        ),
        st.Page(
            "views/route.py",
            title="Rutas inteligentes",
            icon=":material/route:"
        ),
        st.Page(
            "views/about_us.py",
            title="Backstage",
            icon=":material/groups:"
        ),
    ]


    pg = st.navigation(
        pages,
        position="sidebar"
    )

    pg.run()