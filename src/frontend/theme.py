"""
theme.py — Estilo visual de MadFlow para Streamlit.

Replica el lenguaje visual del dashboard de Power BI: sidebar azul Madrid,
tarjetas KPI redondeadas, tabs tipo píldora con acento violeta y banner header.

Uso:
    from theme import apply_theme, header_banner, kpi_card, PLOTLY_LAYOUT, COLORS

    apply_theme()                 # una vez, al inicio de cada página
    header_banner("MadFlow: Dashboard de Movilidad Urbana")
    kpi_card("Variación fin de semana", "-26,54 %", positive=True)
"""

import base64
from pathlib import Path

import streamlit as st

# NOTA sobre por qué cambié de enfoque:
# Intentar DETECTAR el tema activo desde Python (st.context.theme,
# st.get_option, etc.) no es fiable: ese código de módulo solo corre una vez
# por proceso, y en tu instalación tampoco refleja el toggle manual.
# En vez de detectar nada, uso la variable CSS "--text-color" que Streamlit
# SÍ actualiza en vivo en el navegador cada vez que cambiás de tema (es la
# misma variable que ya usan el label y el "objetivo" de la tarjeta KPI, por
# eso esos dos sí te cambiaban bien). Con color-mix() el navegador la mezcla
# con el azul de marca y se recalcula solo, sin Python de por medio.
# Ver kpi_card() y la clase .madflow-kpi-value en apply_theme() más abajo.

TEXT = "#0A2A4A"  # valor por defecto solo para PLOTLY_LAYOUT (ver nota abajo)

font=dict(color=TEXT)
title=dict(font=dict(color=TEXT))


# --- Paleta central (única fuente de verdad) ---
COLORS = {
    "azul_madrid": "#0B5FA5",
    "azul_oscuro": "#0A2A4A",
    "violeta": "#7E57C2",
    "violeta_claro": "#B39DDB",
    "gris": "#C9CDD4",
    "azul_linea": "#2E86DE",
    "verde": "#21A366",
    "rojo": "#E63946",
    "teal_borde": "#BFE3E0",
    "fondo": "#F4F8FC",
}

# Orden de colores para las series de Plotly (barra destacada violeta + resto gris)
PLOTLY_SEQUENCE = [
    COLORS["violeta"], COLORS["gris"], COLORS["azul_linea"],
    COLORS["azul_madrid"], COLORS["verde"], COLORS["violeta_claro"],
]

# Layout base para pasar a fig.update_layout(**PLOTLY_LAYOUT)
PLOTLY_LAYOUT = dict(
    font=dict(family="sans-serif", color=TEXT, size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    colorway=PLOTLY_SEQUENCE,
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor="#E3EAF2", zerolinecolor="#E3EAF2"),
    yaxis=dict(gridcolor="#E3EAF2", zerolinecolor="#E3EAF2"),
    legend=dict(bgcolor="rgba(255,255,255,0.6)"),
)


def apply_theme():

    st.markdown("""
    <style>

    /* Un poco de aire */
    .block-container{
        padding-top:1.5rem;
    }

    /* Sidebar corporativo */
    [data-testid="stSidebar"]{
        background:linear-gradient(180deg,#0B5FA5 0%,#0A4E88 100%);
    }

    [data-testid="stSidebar"] *{
        color:white;
    }

    /* El texto DENTRO de los propios inputs (fecha, selects) va sobre un
       fondo claro nativo del navegador, no sobre el azul del sidebar —
       blanco ahí sería invisible. Lo dejamos oscuro y legible. */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-baseweb="input"] *{
        color:#0A2A4A !important;
    }

    /* Página activa */
    [data-testid="stSidebarNav"] a {
        border-radius: 10px;
        margin: 14px 8px !important;   /* antes 2px */
        padding: 10px 10px !important; /* antes 6px */
    }

    /* Hover */
    [data-testid="stSidebarNav"] a:hover{
        background:rgba(255,255,255,.10);
        border-radius:10px;
    }

    /* Logo del sidebar */
    [data-testid="stSidebarHeader"]{
        min-height:130px !important;
        padding: 0 !important;

        display:flex !important;
        justify-content:center !important;
        align-items:center !important;
    }

    [data-testid="stSidebarHeader"] > *{
        width:100%;
        display:flex !important;
        justify-content:center !important;
        align-items:center !important;
    }

    /*  LOGO /Efecto LOGO  */
    [data-testid="stSidebarHeader"] img{
        height:130px !important;
        width:auto !important;
        max-width:none !important;
        max-height:none !important;
        margin:0 auto !important;
        display:block !important;        
        filter: 
            drop-shadow(0 -0.1px 0 rgba(255, 255, 255, 0.55)) !important;
    }

    /* Logo cuando el sidebar está colapsado */

    [data-testid="stSidebarCollapsedControl"]{
        min-height:70px !important;
        display:flex !important;
        justify-content:center !important;
        align-items:center !important;
        margin-top:10px !important;
    }

    [data-testid="stSidebarCollapsedControl"] img{
        height:68px !important;
        width:auto !important;
        max-width:none !important;
        max-height:none !important;
        display:block !important;
        margin:0 auto !important;        
    }
    
    /* Botones */

    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #6c757d !important;
        color: white !important;
        border-color: #6c757d !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background-color: #5a6268 !important;
        border-color: #545b62 !important;
    }

    .stButton>button,
    .stDownloadButton>button{

        background:#7E57C2;
        color:white;
        border:none;
        border-radius:10px;
        font-weight:600;
    }

    .stButton>button:hover,
    .stDownloadButton>button:hover{

        background:#6848a8;
        color:white;
    }

    .stButton>button:focus,
    .stButton>button:active,
    .stDownloadButton>button:focus,
    .stDownloadButton>button:active{

        background:#6848a8;
        color:white;
    }

    /* Tabs */

    button[data-baseweb="tab"]{

        border-radius:10px;
        font-weight:600;
    }

    button[data-baseweb="tab"]:hover{

        background:rgba(126,87,194,.15);
    }

    button[data-baseweb="tab"][aria-selected="true"]{

        background:#7E57C2 !important;
        color:white !important;
    }

    /* KPI */

    div[data-testid="stMetric"]{

        border-radius:12px;
        border:1px solid rgba(126,87,194,.25);
        padding:15px;
    }

    /* Color del VALOR de la tarjeta KPI */

    .madflow-kpi-value{
        color: color-mix(in srgb, var(--text-color) 65%, #0B5FA5 35%);
    }

    /* Tarjetas KPI */

    div:has(> div[class*="st-key-kpi_"]){
        height:180px !important;
    }

    div[class*="st-key-kpi_"]{
        border-radius:14px !important;
        height:180px;
        display:flex;
        flex-direction:column;
        justify-content:center;
        overflow:hidden;
    }

    /*Banner all views.*/
    .st-emotion-cache-6c7yup{
        margin-top: 0.1rem;
    }

    /* ABOUT_US*/

    .db-table {
        background-color: #ffffff;
        border: 1.5px solid #bdc3c7;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        position: relative;
        height: 100%;
    }

    .db-header {
        background: linear-gradient(135deg, #f0f2f5 0%, #e4e7eb 100%);
        padding: 7px 10px;
        font-weight: 700;
        font-size: 11px;
        color: #2c3e50;
        border-bottom: 1.5px solid #bdc3c7;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .db-title-wrapper {
        display: flex;
        align-items: center;
    }

    .db-body {
        padding: 8px 10px;
        font-size: 11px;
        color: #333;
    }

    .db-field {
        display: flex;
        align-items: center;
        margin-bottom: 4px;
        line-height: 1.2;
    }

    .db-type {
        color: #8B263E;
        font-family: 'Courier New', Courier, monospace;
        font-size: 10px;
        font-weight: bold;
        margin-left: 4px;
    }

    .profile-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        object-fit: cover;
        border: 1px solid #d0d0d0;
        margin-right: 8px;
        flex-shrink: 0;
    }

    /* Tabla de Hechos Central */

    .fact-table {
        background-color: #ffffff;
        border: 2px solid #8B263E;
        border-radius: 10px;
        box-shadow: 0 8px 20px rgba(139,38,62,0.15);
    }

    .fact-header {
        background: linear-gradient(135deg, #8B263E 0%, #5C182A 100%);
        color: white;
        padding: 8px;
        font-weight: bold;
        text-align: center;
        font-size: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    /* ... */

    </style>
    """, unsafe_allow_html=True)


def header_banner(titulo: str, subtitulo: str = "") -> None:
    """Banner superior con degradado azul."""

    sub = ""
    if subtitulo:
        sub = f"""
        <div style="
            font-size:20px;
            opacity:0.9;
            margin-top:12px;
        ">
            {subtitulo}
        </div>
        """

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(90deg, {COLORS['azul_oscuro']} 0%, {COLORS['azul_madrid']} 100%);
            border-radius:18px;
            padding:40px 42px;
            margin-bottom:30px;
            color:white;
        ">
            <div style="
                font-size:40px;
                font-weight:800;
                line-height:1.2;
            ">
                {titulo}
            </div>

            {sub}
        </div>
        """,
        unsafe_allow_html=True,
    )

def kpi_card(
    label: str,
    value: str,
    positive: bool | None = None,
    objetivo: str = "",
    color: str | None = None,
    trend: list | None = None,
    key: str | None = None,
) -> None:
    """
    Tarjeta KPI con altura fija, borde de color a la izquierda y sparkline
    opcional.

    - positive=True/False sigue pintando el VALOR en verde/rojo (para KPIs
      de variación). Si no se pasa, el valor usa color-mix con --text-color
      (se adapta solo a claro/oscuro, ver nota de apply_theme).
    - color: color de acento para el borde izquierdo y la línea del
      sparkline. Por defecto usa violeta de marca. Pasale un COLORS[...]
      distinto por tarjeta para que la fila no se vea todas iguales.
    - trend: lista/serie de números para dibujar una mini línea de
      tendencia debajo del valor (p.ej. la curva horaria del KPI).
    - key: necesario si generás varias tarjetas en un bucle, para que
      Streamlit no colisione claves internas.
    """
    accent = color or COLORS["violeta"]

    valor_style = ""
    if positive is True:
        valor_style = f"color:{COLORS['verde']};"
    elif positive is False:
        valor_style = f"color:{COLORS['rojo']};"
    # si no hay positive, el color del valor lo pone la clase CSS
    # .madflow-kpi-value (color-mix con --text-color, se adapta solo)

    obj = f'<div style="font-size:12px;color:var(--text-color);opacity:.7;margin-top:4px;">{objetivo}</div>' if objetivo else ""

    contenedor_key = key or f"kpi_{label}"
    with st.container(border=True, key=contenedor_key):
        st.markdown(f"""
            <div style="border-left:4px solid {accent}; padding-left:12px;">
                <div style="font-size:13px;font-weight:600;color:var(--text-color);opacity:.75;">
                    {label}
                </div>
                <div class="madflow-kpi-value" style="font-size:28px;font-weight:700;margin-top:6px;{valor_style}">
                    {value}
                </div>
                {obj}
            </div>
            """, unsafe_allow_html=True)

        if trend:
            import plotly.graph_objects as go
            r, g, b = int(accent[1:3], 16), int(accent[3:5], 16), int(accent[5:7], 16)
            fig = go.Figure(go.Scatter(
                y=list(trend), mode="lines", line=dict(color=accent, width=2),
                fill="tozeroy", fillcolor=f"rgba({r},{g},{b},0.15)",
            ))
            fig.update_layout(
                height=48, margin=dict(l=0, r=0, t=6, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                showlegend=False,
            )
            st.plotly_chart(
                fig, width="stretch", config={"displayModeBar": False},
                key=f"{contenedor_key}_spark",
            )
        else:
            # Reserva el mismo hueco que ocupa un sparkline, para que las
            # tarjetas sin trend midan igual que las que sí lo tienen.
            st.markdown('<div style="height:48px;"></div>', unsafe_allow_html=True)

def sidebar_footer_logo(image_path: str, height_px: int = 100) -> None:
    """
    Coloca una imagen (p.ej. madflow.png) al final del sidebar, centrada.

    IMPORTANTE: llamá a esta función DESPUÉS de pg.run() en main.py, para que
    se dibuje debajo del contenido que agregan las páginas (como los Filtros)
    y no se solape con ellos.

    height_px: alto del logo. Por defecto 100, igual que el logo superior.
    """
    try:
        data = base64.b64encode(Path(image_path).read_bytes()).decode()
    except (FileNotFoundError, OSError):
        return  # si no encuentra la imagen, no rompe la app

    st.sidebar.markdown(
        f"""
        <div style="text-align:center; margin-top:28px; padding-bottom:12px;">
            <img src="data:image/png;base64,{data}"
                 style="height:{height_px}px; width:auto; display:inline-block;">
        </div>
        """,
        unsafe_allow_html=True,
    )