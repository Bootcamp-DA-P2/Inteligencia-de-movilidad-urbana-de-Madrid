import base64
from pathlib import Path
import streamlit as st
from theme import apply_theme, header_banner

apply_theme()
header_banner("MadFlow: El Backstage", "El Modelo Dimensional de nuestro Equipo")

# -------------------------------------------------------------------
# PRESENTACIÓN
# -------------------------------------------------------------------

st.subheader("☕ La verdadera energía detrás del código")

st.write(
    "Detrás de cada predicción de tráfico de MadFlow no solo hay sensores, "
    "archivos CSV pesados y modelos de Machine Learning... Hay miles de horas "
    "de debates, café infinito, risas en llamadas a deshoras y un equipo "
    "que aprendió a coordinarse como los semáforos de la M-30 en hora punta."
)

st.write(
    "Lo divertido de construir MadFlow no ha sido solo enfrentarnos a "
    "cerca de un millón de datos, sino darnos cuenta de que cada uno "
    "aportaba una 'superpotencia' totalmente distinta al grupo."
)

st.write(
    "### 🚗 Del caos de los datos al engranaje perfecto\n\n"
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
# ICONOS SVG ELEGANTES (Vectoriales)
# -------------------------------------------------------------------

SVG_ICONS = {
    "key": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#8B263E" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-1.5 1.5L14 9.5M10.5 13a5 5 0 1 1 7-7l-1.5 1.5M7.5 16l-3 3v2h2l2-2h2l1.5-1.5"/></svg>',
    "zap": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "link": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#4B5563" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    "chart": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "coffee": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#7C2D12" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>',
    "heart": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
    "table": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#374151" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>'
}
# -------------------------------------------------------------------
# PROCESAMIENTO DE IMÁGENES
# -------------------------------------------------------------------

def resolve_img_src(img_path: str) -> str:
    """Convierte imágenes a base64 para inyectarlas en HTML/CSS."""
    if not img_path:
        return ""
    if img_path.startswith("http://") or img_path.startswith("https://"):
        return img_path
    try:
        path = Path(img_path)
        if path.is_file():
            data = base64.b64encode(path.read_bytes()).decode()
            ext = path.suffix.lstrip(".").lower()
            mime = "jpeg" if ext in ["jpg", "jpeg"] else ext
            return f"data:image/{mime};base64,{data}"
    except Exception:
        pass
    return ""

logo_madflow = resolve_img_src("assets/madflow.png")

# -------------------------------------------------------------------
# DATOS GRACIOSOS DE LAS DIMENSIONES
# -------------------------------------------------------------------

dim_elena = {
    "table_name": "Dimension_Elena",
    "fk": "idElena: INT (FK)",
    "name": "Elena Suárez",
    "role": "Software Dev & Data Analyst",
    "hobby": "¡MadFlow, yo te elijo! Entrena modelos de Machine Learning y captura excepciones como si fueran Pokémon legendarios.",
    "url": "https://www.linkedin.com/in/elena-suarez-dev/",
    "img": resolve_img_src("assets/equipo/elena-suarez-dev.png"),
    "conector_pos": "bottom" # Conecta hacia abajo
}

dim_ana = {
    "table_name": "Dimension_Ana",
    "fk": "idAna: INT (FK)",
    "name": "Ana Paula Montiel",
    "role": "Data Analyst & ML Specialist",
    "hobby": "Fan absoluta de Shin-chan. Si hay un bug a las 3 AM, ella lo extermina.",
    "url": "https://www.linkedin.com/in/ana-paula-montiel-923386378/",
    "img": resolve_img_src("assets/equipo/ana-paula-montiel-923386378.png"),
    "conector_pos": "bottom"
}

dim_jose = {
    "table_name": "Dimension_JoseCarlos",
    "fk": "idJoseCarlos: INT (FK)",
    "name": "Jose Carlos De Santiago",
    "role": "Data Analyst & ML Engine",
    "hobby": "El mismísimo Goku del equipo: junta toda la energía del universo para lanzar un Kamehameha a las bases de datos y transformar los CSVs en Super Saiyan.",
    "url": "https://www.linkedin.com/in/jose-carlos-de-santiago-sanchez-12b855408/",
    "img": resolve_img_src("assets/equipo/jose-carlos-de-santiago-sanchez-12b855408.PNG"),
    "conector_pos": "bottom"
}

dim_daniel = {
    "table_name": "Dimension_Daniel",
    "fk": "idDaniel: INT (FK)",
    "name": "Daniel Luque",
    "role": "Full-Stack Dev & AI",
    "hobby": "«La mente de un desarrollador es un enigma...» Vive en una piña debajo del código al más puro estilo Patricia Estrella.",
    "url": "https://www.linkedin.com/in/daniel-luque-gallardo/",
    "img": resolve_img_src("assets/equipo/daniel-luque-gallardo.jpg"),
    "conector_pos": "right" # Conecta a la derecha
}

dim_irene = {
    "table_name": "Dimension_Irene",
    "fk": "idIrene: INT (FK)",
    "name": "Irene Condado",
    "role": "Software Dev & BI Developer",
    "hobby": "¡Invocamos la magia de Reena y Gaudi para aniquilar el overfitting y elevar el Accuracy al infinito! ¡¡MATADRAGONES DE MÉTRICAS!!",
    "url": "https://www.linkedin.com/in/irene-condado/",
    "img": resolve_img_src("assets/equipo/irene-condado.jpg"),
    "conector_pos": "left" # Conecta a la izquierda
}

# -------------------------------------------------------------------
# CSS CON CONECTORES DE BASE DE DATOS (LÍNEAS DE UNIÓN)
# -------------------------------------------------------------------

st.markdown("""
<style>
/* Estilo tabla de dimensión */
.db-table {
    background-color: #ffffff;
    border: 2px solid #a0a0a0;
    border-radius: 6px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin-bottom: 25px;
    position: relative;
}

.db-header {
    background: linear-gradient(135deg, #e0e0e0 0%, #cccccc 100%);
    padding: 6px 10px;
    font-weight: 700;
    font-size: 12px;
    color: #222;
    border-bottom: 2px solid #a0a0a0;
    display: flex;
    justify-content: space-between;
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

.db-icon {
    margin-right: 5px;
    font-size: 10px;
}

.db-type {
    color: #d63384;
    font-family: 'Courier New', Courier, monospace;
    font-size: 10px;
    font-weight: bold;
    margin-left: 4px;
}

/* LÍNEAS DE CONEXIÓN (Líneas de relación 1:N estilo diagrama ER) */
.connector-bottom::after {
    content: '';
    position: absolute;
    bottom: -22px;
    left: 50%;
    width: 2px;
    height: 20px;
    background-color: #8B263E;
    border-left: 1px dashed #8B263E;
    z-index: 10;
}

.connector-bottom::before {
    content: '◆';
    position: absolute;
    bottom: -27px;
    left: calc(50% - 4px);
    color: #8B263E;
    font-size: 8px;
    z-index: 11;
}

.connector-right::after {
    content: '';
    position: absolute;
    right: -22px;
    top: 50%;
    width: 20px;
    height: 2px;
    background-color: #8B263E;
    border-top: 1px dashed #8B263E;
    z-index: 10;
}

.connector-left::after {
    content: '';
    position: absolute;
    left: -22px;
    top: 50%;
    width: 20px;
    height: 2px;
    background-color: #8B263E;
    border-top: 1px dashed #8B263E;
    z-index: 10;
}

/* Tabla de Hechos Central */
.fact-table {
    background-color: #fffafb;
    border: 2px solid #8B263E;
    border-radius: 8px;
    box-shadow: 0 6px 16px rgba(139,38,62,0.2);
    position: relative;
}

.fact-header {
    background: linear-gradient(135deg, #8B263E 0%, #5C182A 100%);
    color: white;
    padding: 8px;
    font-weight: bold;
    text-align: center;
    font-size: 13px;
    letter-spacing: 0.5px;
}

.profile-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    object-fit: cover;
    border: 1px solid #ccc;
    margin-right: 8px;
}
</style>
""", unsafe_allow_html=True)

def render_db_dimension(data):
    """Genera el HTML de la tabla con conectores y tipos de datos divertidos."""
    name_link = (
        f'<a href="{data["url"]}" target="_blank" style="color:#111; text-decoration:none; font-weight:bold;">{data["name"]}</a>'
        if data["url"] else data["name"]
    )
    
    connector_class = f"connector-{data['conector_pos']}" if 'conector_pos' in data else ""
    
    html = f"""
    <div class="db-table {connector_class}">
        <div class="db-header">
            <span>📊 {data["table_name"]}</span>
            <span style="font-size:9px; color:#666;">DIM_TABLE</span>
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
            <div style="font-size: 10px; color: #444; background: #f8f9fa; padding: 5px; border-radius: 4px; margin-top: 4px; border-left: 2.5px solid #8B263E;">
                "{data["hobby"]}"
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# -------------------------------------------------------------------
# MODELADO EN ESTRELLA CON LÍNEAS DE RELACIÓN
# -------------------------------------------------------------------

# FILA 1: Dimensiones Superiores (Apuntan hacia abajo a la Fact Table)
c1, c2, c3 = st.columns(3)
with c1:
    render_db_dimension(dim_elena)
with c2:
    render_db_dimension(dim_ana)
with c3:
    render_db_dimension(dim_jose)

# FILA 2: Dimensiones Laterales + Tabla de Hechos Central
f1, f2, f3 = st.columns([1, 1.2, 1], vertical_alignment="center")

with f1:
    render_db_dimension(dim_daniel)

with f2:
    # TABLA DE HECHOS CENTRADA
    fact_html = f"""
    <div class="db-table fact-table">
        <div class="fact-header">
            ⚡ Fact_MadFlow_Project
        </div>
        <div class="db-body" style="text-align: center;">
            <img src="{logo_madflow}" style="max-width: 150px; margin: 8px 0;">
            <div style="text-align: left; background: white; padding: 6px 8px; border-radius: 4px; border: 1px solid #e0e0e0; font-size: 10px;">
                <div class="db-field"><span class="db-icon">🔗</span> <b>{dim_elena["fk"]}</b></div>
                <div class="db-field"><span class="db-icon">🔗</span> <b>{dim_ana["fk"]}</b></div>
                <div class="db-field"><span class="db-icon">🔗</span> <b>{dim_jose["fk"]}</b></div>
                <div class="db-field"><span class="db-icon">🔗</span> <b>{dim_daniel["fk"]}</b></div>
                <div class="db-field"><span class="db-icon">🔗</span> <b>{dim_irene["fk"]}</b></div>
                <hr style="margin: 3px 0; border:0; border-top: 1px dashed #ccc;">
                <div class="db-field"><span class="db-icon">📈</span> <b>Total_Lineas_Codigo</b>: <span class="db-type">BIGINT_INFINITO</span></div>
                <div class="db-field"><span class="db-icon">☕</span> <b>Cafes_Consumidos</b>: <span class="db-type">DOUBLE_PRECISION</span></div>
                <div class="db-field"><span class="db-icon">❤️</span> <b>Buen_Ambiente</b>: <span class="db-type">ALWAYS_TRUE</span></div>
            </div>
        </div>
    </div>
    """
    st.markdown(fact_html, unsafe_allow_html=True)

with f3:
    render_db_dimension(dim_irene)

st.divider()
st.caption("MadFlow Analytics © 2026 • Optimizando la gestión del flujo vehicular mediante Ciencia de Datos.")