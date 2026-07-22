import streamlit as st
from streamlit_carousel_uui import uui_carousel

from theme import apply_theme, header_banner, kpi_card, COLORS
from pathlib import Path

apply_theme()

BASE_DIR = Path(__file__).resolve().parents[3]

BANNER = BASE_DIR / "assets" / "bannermadrid.jpg"

IMG_MADRID_1 = "https://images.trvl-media.com/place/178281/edbf43cf-0496-4327-900f-411c38682541.jpg"
IMG_MADRID_2 = "https://tse4.mm.bing.net/th/id/OIP.a6Z5xLuB65GJM0P9T72zxgHaE8?r=0&rs=1&pid=ImgDetMain&o=7&rm=3"
IMG_MADRID_3 = "https://bubo.sk/uploads/galleries/7351/wikipedia-plaza-mayor-de-madrid-02.jpg"
IMG_MADRID_4 = "https://espanaviajar.com/wp-content/uploads/2018/10/puerta-de-alcala-de-madrid-899x600.jpg"

# -------------------------------------------------------------------
# CABECERA
# -------------------------------------------------------------------

header_banner(
    "MadFlow: Movilidad Urbana de Madrid",
    "Análisis y predicción de la movilidad urbana mediante datos oficiales e inteligencia artificial"
)

# -------------------------------------------------------------------
# PRESENTACIÓN
# -------------------------------------------------------------------

st.subheader("Inteligencia de movilidad para tomar mejores decisiones")

st.write(
    "MadFlow es una plataforma de **inteligencia de movilidad urbana** que "
    "transforma los datos abiertos de tráfico del Ayuntamiento de Madrid en "
    "información útil para comprender, analizar y anticipar el comportamiento "
    "del tráfico."
)

st.write(
    "Mediante técnicas de análisis de datos e inteligencia artificial, la "
    "plataforma identifica patrones históricos de congestión, visualiza la "
    "evolución de la movilidad y predice el tráfico a corto plazo para apoyar "
    "la toma de decisiones basada en datos."
)

st.divider()

# -------------------------------------------------------------------
# KPIs
# -------------------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    kpi_card(
        "Sensores monitorizados",
        "~4.900",
        objetivo="Cobertura de la red oficial de Madrid"
    )

with col2:
    kpi_card(
        "Histórico analizado",
        "1 año",
        objetivo="Base para detectar patrones de movilidad"
    )

with col3:
    kpi_card(
        "Predicción",
        "1 hora",
        objetivo="Anticipación para la toma de decisiones"
    )

st.divider()

# -------------------------------------------------------------------
# CASOS DE USO
# -------------------------------------------------------------------

st.subheader("Casos de uso")

col_admin, col_empresas, col_ciudadanos = st.columns(3)

with col_admin:
    st.markdown(
        f"""
        <div style="border-left:4px solid {COLORS['violeta']}; padding-left:14px;">
            <h3 style="margin-top:0; color:inherit;">Administración pública</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        "Identifica zonas con congestión recurrente, analiza patrones de "
        "movilidad y apoya la planificación urbana mediante datos históricos "
        "y modelos predictivos."
    )

with col_empresas:
    st.markdown(
        f"""
        <div style="border-left:4px solid {COLORS['azul_madrid']}; padding-left:14px;">
            <h3 style="margin-top:0; color:inherit;">Empresas</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        "Optimiza la planificación de rutas, recursos y horarios "
        "anticipando la congestión prevista y mejorando la eficiencia "
        "operativa."
    )

with col_ciudadanos:
    st.markdown(
        f"""
        <div style="border-left:4px solid {COLORS['verde']}; padding-left:14px;">
            <h3 style="margin-top:0; color:inherit;">Ciudadanía e investigación</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        "Consulta visualizaciones interactivas, explora el comportamiento "
        "del tráfico y utiliza las predicciones para planificar mejor los "
        "desplazamientos."
    )

st.divider()

# -------------------------------------------------------------------
# MADRID Y SU MOVILIDAD
# -------------------------------------------------------------------

st.subheader("Madrid: una ciudad en movimiento")

st.write(
    "La movilidad urbana está condicionada por miles de desplazamientos "
    "diarios. MadFlow analiza estos patrones para comprender cómo se mueve "
    "la ciudad y anticipar situaciones de congestión."
)


def madrid_image(url):
    st.markdown(
        f"""
        <div style="
            width:100%;
            height:220px;
            overflow:hidden;
            border-radius:16px;
            margin-bottom:12px;
        ">
            <img src="{url}"
                 style="
                    width:100%;
                    height:100%;
                    object-fit:cover;
                 ">
        </div>
        """,
        unsafe_allow_html=True,
    )


col1, col2 = st.columns(2)

with col1:
    madrid_image(IMG_MADRID_1)

    st.markdown(
        """
        **Tráfico urbano**

        Los sensores de Madrid permiten analizar la intensidad del tráfico
        y detectar zonas con mayor congestión.
        """
    )


with col2:
    madrid_image(IMG_MADRID_2)

    st.markdown(
        """
        **Una ciudad conectada**

        La movilidad urbana refleja la interacción entre ciudadanos,
        infraestructuras y redes de transporte.
        """
    )


st.write("")


col1, col2 = st.columns(2)

with col1:
    madrid_image(IMG_MADRID_3)

    st.markdown(
        """
        **Patrones de movilidad**

        Los datos históricos permiten descubrir tendencias y
        comportamientos recurrentes de desplazamiento.
        """
    )


with col2:
    madrid_image(IMG_MADRID_4)

    st.markdown(
        """
        **Datos para decidir mejor**

        MadFlow transforma datos abiertos en información útil para
        comprender y anticipar la movilidad.
        """
    )


st.divider()

# -------------------------------------------------------------------
# CIERRE
# -------------------------------------------------------------------

st.markdown(
    """
    <div style="text-align:center; padding:20px 0; color:inherit;">
        <h2 style="margin-bottom:10px;">
            Comprender el tráfico hoy para tomar mejores decisiones mañana
        </h2>
        <p style="font-size:18px;">
            MadFlow combina datos abiertos, análisis e inteligencia artificial
            para transformar la movilidad urbana en conocimiento útil.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns([2,1,2])

with col2:
    st.image(str(BANNER), width=300)
