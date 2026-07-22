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
    font=dict(family="sans-serif", color=COLORS["azul_oscuro"], size=13),
    title=dict(font=dict(color=COLORS["azul_oscuro"], size=16)),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    colorway=PLOTLY_SEQUENCE,
    margin=dict(l=10, r=10, t=50, b=10),
    xaxis=dict(gridcolor="#E3EAF2", zerolinecolor="#E3EAF2"),
    yaxis=dict(gridcolor="#E3EAF2", zerolinecolor="#E3EAF2"),
    legend=dict(bgcolor="rgba(255,255,255,0.6)"),
)


def apply_theme() -> None:
    """Inyecta el CSS global. Llamar al inicio de cada página, después de set_page_config."""
    c = COLORS
    st.markdown(f"""
    <style>
      :root {{
        --azul-madrid: {c['azul_madrid']};
        --azul-oscuro: {c['azul_oscuro']};
        --violeta: {c['violeta']};
        --teal-borde: {c['teal_borde']};
        --fondo: {c['fondo']};
      }}

      /* Fondo general */
      .stApp {{ background-color: var(--fondo); }}
      .block-container {{ padding-top: 1.5rem; }}

      /* ---------- SIDEBAR AZUL ---------- */
      [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, var(--azul-madrid) 0%, #0A4E88 100%);
      }}
      /* Todo el texto del sidebar en blanco */
      [data-testid="stSidebar"] * {{ color: #FFFFFF !important; }}
      /* Los links de navegación (st.navigation) */
      [data-testid="stSidebarNav"] a {{
        border-radius: 10px;
        margin: 2px 8px;
        padding: 6px 10px;
      }}
      [data-testid="stSidebarNav"] a:hover {{
        background-color: rgba(255,255,255,0.15);
      }}
      /* Página activa resaltada */
      [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background-color: rgba(255,255,255,0.22);
        font-weight: 700;
      }}
      /* Inputs del sidebar (fecha, selectbox) sobre fondo azul */
      [data-testid="stSidebar"] [data-baseweb="select"] > div,
      [data-testid="stSidebar"] input {{
        background-color: rgba(255,255,255,0.95) !important;
        color: var(--azul-oscuro) !important;
        border-radius: 8px;
      }}
      [data-testid="stSidebar"] [data-baseweb="select"] * {{
        color: var(--azul-oscuro) !important;
      }}

      /* ---------- LOGO MADRID (st.logo) ---------- */
      /* La única <img> del sidebar es el logo, así que lo agrandamos y centramos
         sin depender del data-testid (que cambia entre versiones de Streamlit). */
      [data-testid="stSidebarHeader"] {{
        display: flex !important;
        justify-content: center !important;
        min-height: 120px !important;
        padding-top: 28px !important;
        padding-bottom: 20px !important;
      }}
      [data-testid="stSidebar"] img {{
        height: 120px !important;
        max-height: 120px !important;
        width: auto !important;
        margin: 32px auto 20px auto !important;
        display: block !important;
        object-fit: contain !important;
        /* Tarjeta clara detrás del logo para dar contraste sobre el azul */
        background: #EAF3FC !important;      /* celeste claro; poné #FFFFFF para blanco */
        padding: 12px 18px !important;
        border-radius: 16px !important;
        box-shadow: 0 3px 12px rgba(0,0,0,0.18) !important;
      }}

      /* Espacio al fondo del sidebar para que el panel de filtros no quede pegado abajo */
      [data-testid="stSidebarUserContent"] {{
        padding-bottom: 36px !important;
      }}

      /* ---------- PANEL DE FILTROS (st.container(border=True, key="filtros")) ---------- */
      /* .st-key-filtros es una clase estable que Streamlit genera desde la key del contenedor */
      [data-testid="stSidebar"] .st-key-filtros {{
        background: #EAF3FC !important;
        border: 1px solid #BFE3E0 !important;
        border-radius: 12px !important;
        padding: 14px 14px 6px 14px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.12) !important;
      }}
      /* Sobre fondo claro, el texto del panel debe ir oscuro (no blanco) */
      [data-testid="stSidebar"] .st-key-filtros *:not(input) {{
        color: {COLORS['azul_oscuro']} !important;
      }}

      /* ---------- TABS TIPO PÍLDORA (Streamlit react-aria: data-testid="stTab") ---------- */
      .stTabs [role="tablist"] {{
        gap: 10px;
        background: transparent;
        border-bottom: none;
      }}
      /* Cada pestaña — doble atributo para ganar especificidad vs. la regla de Streamlit */
      [data-testid="stTab"][role="tab"] {{
        background-color: #FFFFFF !important;
        border: 1px solid var(--teal-borde) !important;
        border-radius: 10px !important;
        padding: 10px 36px !important;
        margin-bottom: 4px !important;
        font-weight: 600 !important;
      }}
      /* El espacio alrededor de la palabra lo da el margin del <p> interno.
         Selector estable por data-testid (NO usar la clase .st-emotion-cache-*,
         que cambia entre versiones de Streamlit). */
      [data-testid="stTab"] [data-testid="stMarkdownContainer"] p {{
        color: var(--azul-oscuro);
        margin: 5px 16px !important;
      }}
      /* Pestaña activa: pastilla violeta, texto blanco */
      [data-testid="stTab"][aria-selected="true"],
      [data-testid="stTab"][data-selected="true"] {{
        background-color: var(--violeta) !important;
        border-color: var(--violeta) !important;
      }}
      [data-testid="stTab"][aria-selected="true"] [data-testid="stMarkdownContainer"] p,
      [data-testid="stTab"][data-selected="true"] [data-testid="stMarkdownContainer"] p {{
        color: #FFFFFF !important;
      }}
      /* Indicador inferior (react-aria): azul en vez del rojo por defecto */
      .react-aria-SelectionIndicator {{
        background-color: var(--azul-madrid) !important;
      }}

      /* ---------- TARJETAS KPI (st.metric) ---------- */
      [data-testid="stMetric"] {{
        background-color: #FFFFFF;
        border: 1px solid var(--teal-borde);
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 2px 8px rgba(11,95,165,0.06);
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
      }}
      [data-testid="stMetricLabel"] {{
        color: var(--azul-oscuro);
        opacity: 0.75;
        font-weight: 600;
      }}
      [data-testid="stMetricValue"] {{
        color: var(--azul-oscuro);
        font-weight: 700;
      }}

      /* ---------- TÍTULOS ---------- */
      h1, h2, h3 {{ color: var(--azul-oscuro); }}

      /* ---------- BOTONES ---------- */
      /* Estado normal: fondo morado, texto blanco (legible sobre morado) */
      .stButton > button,
      .stDownloadButton > button,
      [data-testid="stFormSubmitButton"] button,
      [data-testid="stSidebar"] .stButton > button {{
        background-color: var(--violeta) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--violeta) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
      }}
      .stButton > button *,
      .stDownloadButton > button *,
      [data-testid="stFormSubmitButton"] button *,
      [data-testid="stSidebar"] .stButton > button * {{
        color: #FFFFFF !important;
      }}
      /* Hover / click / foco: fondo blanco, texto morado (legible sobre blanco) */
      .stButton > button:hover, .stButton > button:active, .stButton > button:focus, .stButton > button:focus-visible,
      .stDownloadButton > button:hover, .stDownloadButton > button:active, .stDownloadButton > button:focus,
      [data-testid="stFormSubmitButton"] button:hover, [data-testid="stFormSubmitButton"] button:active, [data-testid="stFormSubmitButton"] button:focus,
      [data-testid="stSidebar"] .stButton > button:hover, [data-testid="stSidebar"] .stButton > button:active, [data-testid="stSidebar"] .stButton > button:focus {{
        background-color: #FFFFFF !important;
        color: var(--violeta) !important;
        border-color: var(--violeta) !important;
      }}
      .stButton > button:hover *, .stButton > button:active *, .stButton > button:focus *,
      .stDownloadButton > button:hover *, .stDownloadButton > button:active *, .stDownloadButton > button:focus *,
      [data-testid="stFormSubmitButton"] button:hover *, [data-testid="stFormSubmitButton"] button:active *,
      [data-testid="stSidebar"] .stButton > button:hover *, [data-testid="stSidebar"] .stButton > button:active *, [data-testid="stSidebar"] .stButton > button:focus * {{
        color: var(--violeta) !important;
      }}
    </style>
    """, unsafe_allow_html=True)


def header_banner(titulo: str, subtitulo: str = "") -> None:
    """Banner superior con degradé azul, imitando la cabecera del dashboard."""
    sub = f'<div style="font-size:15px;opacity:0.9;margin-top:4px;">{subtitulo}</div>' if subtitulo else ""
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, {COLORS['azul_oscuro']} 0%, {COLORS['azul_madrid']} 100%);
        border-radius: 14px;
        padding: 22px 28px;
        margin-bottom: 20px;
        color: #FFFFFF;">
        <div style="font-size:26px;font-weight:800;">{titulo}</div>
        {sub}
    </div>
    """, unsafe_allow_html=True)


def kpi_card(label: str, value: str, positive: bool | None = None, objetivo: str = "") -> None:
    """
    Tarjeta KPI personalizada (más control que st.metric).
    positive=True -> verde, False -> rojo, None -> azul oscuro.
    """
    color = COLORS["azul_oscuro"]
    if positive is True:
        color = COLORS["verde"]
    elif positive is False:
        color = COLORS["rojo"]

    obj = f'<div style="font-size:12px;color:#7A8AA0;margin-top:6px;">{objetivo}</div>' if objetivo else ""
    st.markdown(f"""
    <div style="
        background:#FFFFFF;
        border:1px solid {COLORS['teal_borde']};
        border-radius:14px;
        padding:18px 20px;
        box-shadow:0 2px 8px rgba(11,95,165,0.06);
        text-align:center;
        min-height:140px;
        display:flex;
        flex-direction:column;
        justify-content:center;">
        <div style="font-size:14px;color:{COLORS['azul_oscuro']};opacity:0.75;font-weight:600;">{label}</div>
        <div style="font-size:30px;font-weight:800;color:{color};margin-top:8px;">{value}</div>
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
