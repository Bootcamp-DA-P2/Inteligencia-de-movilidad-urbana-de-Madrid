import base64
from pathlib import Path
import streamlit as st
from theme import apply_theme, header_banner

# Aplica el tema global y el header
apply_theme()
header_banner("MadFlow: Backstage", "El Modelo Dimensional de nuestro Equipo")

# -------------------------------------------------------------------
# PRESENTACIÓN
# -------------------------------------------------------------------

st.subheader("La verdadera energía detrás del código")

st.write(
    "Detrás de cada predicción de tráfico de MadFlow no solo hay sensores, "
    "archivos CSV pesados y modelos de Machine Learning... Hay miles de horas "
    "de debates, café infinito, risas en llamadas a deshoras y un equipo "
    "que aprendió a coordinarse como los semáforos de la M-30 en hora punta."
)

st.write(
    "Lo divertido de construir MadFlow no ha sido solo enfrentarnos a "
    "millones de datos, sino darnos cuenta de que cada uno "
    "aportaba una 'superpotencia' totalmente distinta al grupo."
)

st.write(
    "### Del caos de los datos al engranaje perfecto\n\n"
    "Al principio, procesar la movilidad urbana de Madrid se sentía como intentar cruzar la "
    "Glorieta de Atocha a las 8:00 AM en patinete eléctrico. Teníamos gigabytes de registros de "
    "intensidad, ocupación y carga que amenazaban con colapsar nuestras CPUs, junto con errores "
    "en las bases de datos que aparecían justo antes de cada entrega.\n\n"
    "Sin embargo, entre *queries* reoptimizadas a última hora, la búsqueda implacable de *bugs* "
    "fantasma y la magia para hacer encajar el frontend en Streamlit, logramos transformar un mar "
    "de datos crudos en una herramienta funcional y visual.\n\n"
    "Así como un data warehouse necesita un buen esquema en estrella para funcionar sin bloqueos, "
    "nuestro equipo encontró la estructura perfecta: **cada integrante actúa como una dimensión clave "
    "conectada a la misma tabla de hechos: la pasión por resolver problemas reales.**"
)

st.divider()

# -------------------------------------------------------------------
# BÚSQUEDA AUTOMÁTICA DE ASSETS Y PROCESAMIENTO DE IMÁGENES
# -------------------------------------------------------------------

def find_assets_dir() -> Path:
    """Busca la carpeta 'assets' subiendo desde el archivo actual hasta la raíz."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = current / "assets"
        if candidate.is_dir():
            return candidate
        current = current.parent
    return Path(__file__).resolve().parent

ASSETS_DIR = find_assets_dir()

def resolve_img_src(relative_path: str) -> str:
    """Convierte imágenes a base64 localizándolas automáticamente en assets/."""
    if not relative_path:
        return ""
    if relative_path.startswith("http://") or relative_path.startswith("https://"):
        return relative_path

    try:
        clean_path = relative_path.replace("assets/", "")
        full_path = ASSETS_DIR / clean_path

        if full_path.is_file():
            data = base64.b64encode(full_path.read_bytes()).decode()
            ext = full_path.suffix.lstrip(".").lower()
            mime = "jpeg" if ext in ["jpg", "jpeg"] else ext
            return f"data:image/{mime};base64,{data}"
        else:
            print(f"Imagen no encontrada en: {full_path}")
    except Exception as e:
        print(f"Error cargando {relative_path}: {e}")

    return ""

logo_madflow = resolve_img_src("assets/madflow.png")

# -------------------------------------------------------------------
# ICONOS SVG
# -------------------------------------------------------------------

# Icono para tablas de dimensión (Grid / Layout)
SVG_DIM_TABLE = """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>"""

# Icono para tabla de hechos (Rayo / Spark)
SVG_FACT_TABLE = """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>"""

# Icono para Claves Foráneas (Link / Cadena)
SVG_FK = """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#8B263E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:5px; flex-shrink:0;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>"""

# Iconos para Métricas
SVG_METRIC_CODE = """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:5px; flex-shrink:0;"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>"""
SVG_METRIC_COFFEE = """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:5px; flex-shrink:0;"><path d="M18 8h1a4 4 0 0 1 0 8h-1"></path><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"></path><line x1="6" y1="1" x2="6" y2="4"></line><line x1="10" y1="1" x2="10" y2="4"></line><line x1="14" y1="1" x2="14" y2="4"></line></svg>"""
SVG_METRIC_HEART = """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#8B263E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:5px; flex-shrink:0;"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>"""

# -------------------------------------------------------------------
# DATOS DE LAS DIMENSIONES DEL EQUIPO
# -------------------------------------------------------------------

dim_elena = {
    "table_name": "Dimension_Elena",
    "fk": "idElena: INT (FK)",
    "name": "Elena Suárez",
    "role": "Software Dev & Data Analyst",
    "hobby": "¡MadFlow, yo te elijo! Entrena modelos de Machine Learning y captura excepciones como si fueran Pokémon legendarios.",
    "url": "https://www.linkedin.com/in/elena-suarez-dev/",
    "img": resolve_img_src("assets/equipo/elena-suarez-dev.png")
}

dim_ana = {
    "table_name": "Dimension_Ana",
    "fk": "idAna: INT (FK)",
    "name": "Ana Paula Montiel",
    "role": "Data Analyst & ML Specialist",
    "hobby": "Fan absoluta de Shin-chan. Si hay un bug a las 3 AM, ella lo extermina.",
    "url": "https://www.linkedin.com/in/ana-paula-montiel-923386378/",
    "img": resolve_img_src("assets/equipo/ana-paula-montiel-923386378.png")
}

dim_jose = {
    "table_name": "Dimension_JoseCarlos",
    "fk": "idJoseCarlos: INT (FK)",
    "name": "Jose Carlos De Santiago",
    "role": "Data Analyst & ML Engine",
    "hobby": "El mismísimo Goku del equipo: junta toda la energía del universo para lanzar un Kamehameha a las bases de datos y transformar los CSVs en Super Saiyan.",
    "url": "https://www.linkedin.com/in/jose-carlos-de-santiago-sanchez-12b855408/",
    "img": resolve_img_src("assets/equipo/jose-carlos-de-santiago-sanchez-12b855408.PNG")
}

dim_daniel = {
    "table_name": "Dimension_Daniel",
    "fk": "idDaniel: INT (FK)",
    "name": "Daniel Luque",
    "role": "Full-Stack Dev & AI",
    "hobby": "«La mente de un desarrollador es un enigma...» Vive en una piña debajo del código al más puro estilo Patricia Estrella.",
    "url": "https://www.linkedin.com/in/daniel-luque-gallardo/",
    "img": resolve_img_src("assets/equipo/daniel-luque-gallardo.jpg")
}

dim_irene = {
    "table_name": "Dimension_Irene",
    "fk": "idIrene: INT (FK)",
    "name": "Irene Condado",
    "role": "Software Dev & BI Developer",
    "hobby": "¡Invocamos la magia de Reena y Gaudi para aniquilar el overfitting y elevar el Accuracy al infinito! ¡¡MATADRAGONES DE MÉTRICAS!!",
    "url": "https://www.linkedin.com/in/irene-condado/",
    "img": resolve_img_src("assets/equipo/irene-condado.jpg")
}


def render_db_dimension(data):
    """Genera la estructura HTML de cada dimensión con iconos vectoriales."""
    name_link = (
        f'<a href="{data["url"]}" target="_blank" style="color:#111; text-decoration:none; font-weight:bold;">{data["name"]}</a>'
        if data["url"] else data["name"]
    )

    html = f"""
    <div class="db-table">
        <div class="db-header">
            <div class="db-title-wrapper">
                {SVG_DIM_TABLE}
                <span>{data["table_name"]}</span>
            </div>
            <span style="font-size:8px; color:#7f8c8d; letter-spacing:0.5px;">DIM_TABLE</span>
        </div>
        <div class="db-body">
            <div style="display: flex; align-items: center; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid #f0f0f0;">
                <img src="{data["img"]}" class="profile-avatar">
                <div>
                    <div style="font-size: 12px;">{name_link}</div>
                    <div style="font-size: 10px; color: #666;">{data["role"]}</div>
                </div>
            </div>
            <div class="db-field">
                <div style="font-size: 11px; color: #444; background: #f8f9fa; padding: 5px; border-radius: 4px; margin-top: 4px; border-left: 2.5px solid #8B263E;">
                    "{data["hobby"]}"
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# -------------------------------------------------------------------
# DISPOSICIÓN DEL MODELO EN ESTRELLA
# -------------------------------------------------------------------

# Fila 1: Dimensiones superiores
c1, c2, c3 = st.columns(3)
with c1:
    render_db_dimension(dim_elena)
with c2:
    render_db_dimension(dim_ana)
with c3:
    render_db_dimension(dim_jose)

st.write("")

# Fila 2: Dimensiones laterales + Tabla de hechos central
f1, f2, f3 = st.columns([1, 1.2, 1], vertical_alignment="center")

with f1:
    render_db_dimension(dim_daniel)

with f2:
    fact_html = f"""
    <div class="db-table fact-table">
        <div class="fact-header">
            {SVG_FACT_TABLE} Fact_MadFlow_Project
        </div>
        <div class="db-body" style="text-align: center;">
            <img src="{logo_madflow}" style="max-width: 110px; width: 100%; margin: 6px 0;">
            <div style="text-align: left; background: #fafafa; padding: 6px 8px; border-radius: 6px; border: 1px solid #e2e8f0; font-size: 10px;">
                <div class="db-field">{SVG_FK} <b>{dim_elena["fk"]}</b></div>
                <div class="db-field">{SVG_FK} <b>{dim_ana["fk"]}</b></div>
                <div class="db-field">{SVG_FK} <b>{dim_jose["fk"]}</b></div>
                <div class="db-field">{SVG_FK} <b>{dim_daniel["fk"]}</b></div>
                <div class="db-field">{SVG_FK} <b>{dim_irene["fk"]}</b></div>
                <hr style="margin: 4px 0; border:0; border-top: 1px dashed #cbd5e1;">
                <div class="db-field">{SVG_METRIC_CODE} <b>Total_Lineas_Codigo</b>: <span class="db-type">BIGINT</span></div>
                <div class="db-field">{SVG_METRIC_COFFEE} <b>Cafes_Consumidos</b>: <span class="db-type">DOUBLE</span></div>
                <div class="db-field">{SVG_METRIC_HEART} <b>Buen_Ambiente</b>: <span class="db-type">BOOLEAN</span></div>
            </div>
        </div>
    </div>
    """
    st.markdown(fact_html, unsafe_allow_html=True)

with f3:
    render_db_dimension(dim_irene)

st.divider()
st.caption("MadFlow Analytics © 2026 • Optimizando la gestión del flujo vehicular mediante Ciencia de Datos.")