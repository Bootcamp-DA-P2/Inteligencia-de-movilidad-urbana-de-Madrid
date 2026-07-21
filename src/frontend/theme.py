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
      }}
      [data-testid="stSidebar"] img {{
        height: 100px !important;
        max-height: 100px !important;
        width: auto !important;
        margin: 12px auto 8px auto !important;
        display: block !important;
        object-fit: contain !important;
      }}

      /* ---------- TABS TIPO PÍLDORA ---------- */
      .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        background: transparent;
        border-bottom: none;
      }}
      .stTabs [data-baseweb="tab"] {{
        background-color: #FFFFFF;
        border: 1px solid var(--teal-borde);
        border-radius: 10px;
        padding: 8px 22px;
        color: var(--azul-oscuro);
        font-weight: 600;
      }}
      .stTabs [aria-selected="true"] {{
        background-color: var(--violeta) !important;
        color: #FFFFFF !important;
        border-color: var(--violeta) !important;
      }}
      .stTabs [data-baseweb="tab-highlight"] {{ display: none; }}

      /* ---------- TARJETAS KPI (st.metric) ---------- */
      [data-testid="stMetric"] {{
        background-color: #FFFFFF;
        border: 1px solid var(--teal-borde);
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 2px 8px rgba(11,95,165,0.06);
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
      .stButton > button {{
        border-radius: 10px;
        border: 1px solid var(--violeta);
        color: var(--violeta);
        font-weight: 600;
      }}
      .stButton > button:hover {{
        background-color: var(--violeta);
        color: #FFFFFF;
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
        text-align:center;">
        <div style="font-size:14px;color:{COLORS['azul_oscuro']};opacity:0.75;font-weight:600;">{label}</div>
        <div style="font-size:30px;font-weight:800;color:{color};margin-top:8px;">{value}</div>
        {obj}
    </div>
    """, unsafe_allow_html=True)
