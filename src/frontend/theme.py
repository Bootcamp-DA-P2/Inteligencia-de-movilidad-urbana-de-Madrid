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


    /* =========================
       SIDEBAR CORPORATIVO
    ========================= */

    [data-testid="stSidebar"]{
        background:linear-gradient(180deg,#0B5FA5 0%,#0A4E88 100%);
    }

    [data-testid="stSidebar"] *{
        color:white;
    }


    /* Navegación */
    [data-testid="stSidebarNav"] a {
        border-radius:10px;
        margin:14px 8px !important;
        padding:10px 10px !important;
    }


    [data-testid="stSidebarNav"] a:hover{
        background:rgba(255,255,255,.10);
        border-radius:10px;
    }


      /* =========================
      LOGO MADFLOW (st.logo)
    ========================= */

    [data-testid="stSidebarHeader"]{
        height:120px !important;
        padding:0 !important;
        display:flex !important;
        align-items:center !important;
        justify-content:center !important;
    }


    [data-testid="stSidebarHeader"] img{
        height:100px !important;
        width:auto !important;
        max-width:none !important;
        object-fit:contain !important;
        display:block !important;
    }


    /* =========================
       BOTÓN SIDEBAR CERRADO
    ========================= */

    [data-testid="stSidebarCollapsedControl"]{
        width:70px !important;
        height:70px !important;
        margin-top:10px !important;
    }


    [data-testid="stSidebarCollapsedControl"] svg{
        width:45px !important;
        height:45px !important;
    }


    /* =========================
       BOTONES
    ========================= */

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


    /* =========================
       TABS
    ========================= */

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


    /* =========================
       KPI
    ========================= */

    div[data-testid="stMetric"]{

        border-radius:12px;
        border:1px solid rgba(126,87,194,.25);
        padding:15px;
    }


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


def kpi_card(label: str, value: str, positive: bool | None = None, objetivo: str = "") -> None:
    """
    Tarjeta KPI personalizada.
    positive=True -> verde, False -> rojo, None -> color adaptado al tema
    (azul oscuro en modo claro, azul claro en modo oscuro).
    """
    if positive is True:
        color = COLORS["verde"]
    elif positive is False:
        color = COLORS["rojo"]
    else:
      color = "color-mix(in srgb, var(--text-color) 80%, #0B5FA5)"

    obj = f'<div style="font-size:12px;color:var(--text-color);opacity:.7;margin-top:6px;">{objetivo}</div>'

    st.markdown(f"""
        <div style="
        background:var(--secondary-background-color);
        border:1px solid #BFE3E0;
        border-radius:14px;
        padding:18px;
        text-align:center;
        ">

        <div style="
        font-size:14px;
        font-weight:600;
        color:var(--text-color);
        opacity:.8;
        ">
            {label}
        </div>

        <div class="madflow-kpi-value" style="
        font-size:30px;
        font-weight:700;
        margin-top:8px;
        color:{color};
        ">
        {value}
        </div>

        {obj}

        </div>
        """, unsafe_allow_html=True)

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