import streamlit as st
import pandas as pd
import plotly.express as px

from utils import DISTRITOS
from theme import apply_theme, header_banner, kpi_card, PLOTLY_LAYOUT, COLORS
from services.traffic_service import (
    get_patron_horario_distrito, get_patron_semanal_distrito,
    get_ranking_distritos, get_patron_horario_m30,
)

# ---------------------------------------------------------------------------
# Config visual
# ---------------------------------------------------------------------------
apply_theme()
header_banner("MadFlow: Dashboard de Movilidad Urbana", "Análisis histórico de tráfico")

NOMBRES_DIAS = {0: "Domingo", 1: "Lunes", 2: "Martes", 3: "Miércoles",
                4: "Jueves", 5: "Viernes", 6: "Sábado"}
ORDEN_DIAS = [1, 2, 3, 4, 5, 6, 0]          # Lunes ... Domingo
FINDE = {6, 0}                               # Sábado, Domingo


def col_ocupacion(df: pd.DataFrame) -> str:
    """Devuelve el nombre de la columna de ocupación, con fallback al primer numérico."""
    if "ocupacion_media" in df.columns:
        return "ocupacion_media"
    num = df.select_dtypes("number").columns
    return num[0] if len(num) else df.columns[-1]


# ---------------------------------------------------------------------------
# Filtros globales (en el sidebar, imitando el panel de slicers del mockup)
# ---------------------------------------------------------------------------
st.sidebar.header("Filtros")
fecha_desde = st.sidebar.date_input("Desde", value=pd.Timestamp("2025-07-01"))
fecha_hasta = st.sidebar.date_input("Hasta", value=pd.Timestamp("2026-06-30"))
desde_str, hasta_str = fecha_desde.isoformat(), fecha_hasta.isoformat()

# ---------------------------------------------------------------------------
# Datos globales (solo dependen de las fechas)
# ---------------------------------------------------------------------------
df_ranking = pd.DataFrame(get_ranking_distritos(desde_str, hasta_str).json())
df_ranking = df_ranking[df_ranking["distrito"].isin(DISTRITOS.keys())].copy()
df_ranking["nombre"] = df_ranking["distrito"].map(DISTRITOS)
rk_col = col_ocupacion(df_ranking)

df_m30 = pd.DataFrame(get_patron_horario_m30(desde_str, hasta_str).json())
df_m30 = pd.DataFrame({"hora": range(24)}).merge(df_m30, on="hora", how="left")
m30_col = col_ocupacion(df_m30)

# ---------------------------------------------------------------------------
# KPIs (fila de tarjetas, calculados de los datos reales)
# ---------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
with k1:
    if df_m30[m30_col].notna().any():
        hora_pico = int(df_m30.loc[df_m30[m30_col].idxmax(), "hora"])
        kpi_card("Hora de más tráfico (M-30)", f"A las {hora_pico}:00 h")
    else:
        kpi_card("Hora de más tráfico (M-30)", "s/d")
with k2:
    kpi_card("Ocupación media M-30", f"{df_m30[m30_col].mean():.2f} %")
with k3:
    top = df_ranking.sort_values(rk_col, ascending=False).iloc[0]
    kpi_card("Distrito más congestionado", top["nombre"], objetivo=f"{top[rk_col]:.2f} %")
with k4:
    kpi_card("Distritos con datos", str(df_ranking["distrito"].nunique()))

st.write("")  # aire

# ---------------------------------------------------------------------------
# Tabs (como las pestañas del dashboard de Power BI)
# ---------------------------------------------------------------------------
tab_resumen, tab_temporal = st.tabs(["Resumen", "Temporalidad"])

# ============================ RESUMEN ============================
with tab_resumen:
    st.subheader("Ranking de distritos por ocupación media")
    df_rk = df_ranking.sort_values(rk_col, ascending=True)   # asc: mayor arriba en barra horizontal
    # top-1 en violeta, el resto en gris
    colores = [COLORS["gris"]] * len(df_rk)
    if len(colores):
        colores[-1] = COLORS["violeta"]
    fig_rk = px.bar(df_rk, x=rk_col, y="nombre", orientation="h")
    fig_rk.update_traces(marker_color=colores)
    fig_rk.update_layout(**PLOTLY_LAYOUT, height=520)
    fig_rk.update_layout(xaxis_title="Ocupación media (%)", yaxis_title="")
    st.plotly_chart(fig_rk, use_container_width=True)

# ========================= TEMPORALIDAD =========================
with tab_temporal:
    st.subheader("Análisis por distrito")
    id_distrito = st.selectbox(
        "Distrito", options=list(DISTRITOS.keys()),
        format_func=lambda x: f"{x} - {DISTRITOS[x]}", key="distrito_dashboard",
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Promedio por hora del día**")
        df_hora = pd.DataFrame(get_patron_horario_distrito(id_distrito, desde_str, hasta_str).json())
        df_hora = pd.DataFrame({"hora": range(24)}).merge(df_hora, on="hora", how="left")
        h_col = col_ocupacion(df_hora)
        fig_h = px.line(df_hora, x="hora", y=h_col, markers=False)
        fig_h.update_traces(line_color=COLORS["azul_linea"], line_width=3)
        fig_h.update_layout(**PLOTLY_LAYOUT, height=340)
        fig_h.update_layout(xaxis_title="Hora del día (0-23)", yaxis_title="Ocupación (%)")
        st.plotly_chart(fig_h, use_container_width=True)

    with col2:
        st.markdown("**Promedio por día de la semana**")
        df_sem = pd.DataFrame(get_patron_semanal_distrito(id_distrito, desde_str, hasta_str).json())
        s_col = col_ocupacion(df_sem)
        df_sem["dia_semana"] = pd.Categorical(df_sem["dia_semana"], categories=ORDEN_DIAS, ordered=True)
        df_sem = df_sem.sort_values("dia_semana")
        df_sem["dia_nombre"] = df_sem["dia_semana"].map(NOMBRES_DIAS)
        # finde en violeta, días laborales en gris (igual que el mockup)
        colores_sem = [COLORS["violeta"] if d in FINDE else COLORS["gris"] for d in df_sem["dia_semana"]]
        fig_s = px.bar(df_sem, x="dia_nombre", y=s_col)
        fig_s.update_traces(marker_color=colores_sem)
        fig_s.update_layout(**PLOTLY_LAYOUT, height=340)
        fig_s.update_layout(xaxis_title="", yaxis_title="Ocupación (%)")
        st.plotly_chart(fig_s, use_container_width=True)

    st.divider()

    st.subheader("M-30: ocupación media por hora del día")
    fig_m30 = px.line(df_m30, x="hora", y=m30_col, markers=False)
    fig_m30.update_traces(line_color=COLORS["azul_linea"], line_width=3)
    fig_m30.update_layout(**PLOTLY_LAYOUT, height=360)
    fig_m30.update_layout(xaxis_title="Hora del día (0-23)", yaxis_title="Ocupación (%)")
    st.plotly_chart(fig_m30, use_container_width=True)
