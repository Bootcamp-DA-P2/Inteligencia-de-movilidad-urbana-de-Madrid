import streamlit as st
from streamlit_carousel_uui import uui_carousel

from theme import apply_theme, header_banner
apply_theme()
header_banner("MadFlow: Movilidad Urbana de Madrid", "Inicio")


st.title("Inteligencia de movilidad urbana de Madrid")
st.write("Bienvenido a la aplicación de inteligencia de movilidad urbana de Madrid.")
st.write("Esta aplicación proporciona información y análisis sobre la movilidad urbana en la ciudad de Madrid, utilizando datos de transporte público, tráfico y otros factores relevantes.")
st.write("Navega por las diferentes secciones de la aplicación utilizando el menú de navegación en la parte superior.")

slides = [
    {
        "image": "https://www.telemadrid.es/2021/10/08/noticias/madrid/Trafico-M-30-Madrid_2385071546_29886830_1300x731.jpg",
        "title": "",
        "description": ""
    },
    {
        "image": "https://tse4.mm.bing.net/th/id/OIP.a6Z5xLuB65GJM0P9T72zxgHaE8?r=0&rs=1&pid=ImgDetMain&o=7&rm=3",
        "title": "",
        "description": ""
    },
    {
        "image": "https://bubo.sk/uploads/galleries/7351/wikipedia-plaza-mayor-de-madrid-02.jpg",
        "title": "",
        "description": ""
    },
    {
        "image": "https://espanaviajar.com/wp-content/uploads/2018/10/puerta-de-alcala-de-madrid-899x600.jpg",
        "title": "",
        "description": ""
    },
]


uui_carousel(items=slides, variant="md")
# ... aquí va el resto del contenido de tu página (carrusel, gráficos, etc.) ...

st.divider()

# --- Banner de cierre ---
col_izq, col_centro, col_der = st.columns([1, 2, 1])

with col_izq:
    st.image(
        "https://marcaporhombro.com/wp-content/uploads/2012/02/madrid1-600x295.jpg"
        )

with col_centro:
    st.markdown(
        """
        <div style="text-align: center;">
            <h2 style="margin-bottom: 0;">🚦 Por una ciudad más ordenada</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_der:
    st.image(
        "https://www.fbm.es/archivos/noticias/12743/foto-61157.jpg"
    )
