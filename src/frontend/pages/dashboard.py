import streamlit as st
import pandas as pd
from utils import DISTRITOS
from services.traffic_service import (
    get_evolucion, get_patron_horario_distrito, get_patron_semanal_distrito,
    get_ranking_distritos, get_patron_horario_m30,
)

ORDEN_DIAS = [1, 2, 3, 4, 5, 6, 0]
NOMBRES_DIAS = {0: "Domingo", 1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado"}

st.title(" Dashboard histórico de tráfico")

#--- Filtro de fechas global, arriba de todo ---,
st.subheader(" Rango de fechas")
col_f1, col_f2 = st.columns(2)
with col_f1:
    fecha_desde = st.date_input("Desde", value=pd.Timestamp("2025-07-01"))
with col_f2:
    fecha_hasta = st.date_input("Hasta", value=pd.Timestamp("2026-06-30"))

desde_str = fecha_desde.isoformat()
hasta_str = fecha_hasta.isoformat()

st.divider()

#--- Ranking de distritos ---,
st.subheader(" Ranking de distritos (ocupación media)")
ranking = get_ranking_distritos(desde_str, hasta_str).json()
df_ranking = pd.DataFrame(ranking)
df_ranking = df_ranking[df_ranking["distrito"].isin(DISTRITOS.keys())]
df_ranking["distrito"] = df_ranking["distrito"].map(DISTRITOS)
st.bar_chart(df_ranking.set_index("distrito"))

st.divider()

#--- Análisis por distrito ---,
st.subheader(" Análisis por distrito")
id_distrito = st.selectbox(
    "Distrito", options=list(DISTRITOS.keys()),
    format_func=lambda x: f"{x} - {DISTRITOS[x]}", key="distrito_dashboard",
)

col1, col2 = st.columns(2)

with col1:
    st.write("Patrón típico por hora del día")
    patron_horario = get_patron_horario_distrito(id_distrito, desde_str, hasta_str).json()
    df_hora = pd.DataFrame(patron_horario)
    df_hora = pd.DataFrame({"hora": range(24)}).merge(df_hora, on="hora", how="left")
    st.line_chart(df_hora.set_index("hora")[["ocupacion_media"]])

with col2:
    st.write("Patrón típico por día de la semana")
    patron_semanal = get_patron_semanal_distrito(id_distrito, desde_str, hasta_str).json()
    df_semana = pd.DataFrame(patron_semanal)
    df_semana["dia_semana"] = pd.Categorical(df_semana["dia_semana"], categories=ORDEN_DIAS, ordered=True)
    df_semana = df_semana.sort_values("dia_semana")
    df_semana["dia_nombre"] = df_semana["dia_semana"].map(NOMBRES_DIAS)
    st.bar_chart(df_semana.set_index("dia_nombre")[["ocupacion_media"]])

st.divider()

#--- M30 ---,
st.subheader("M-30: ocupación media por hora del día")

patron_m30 = get_patron_horario_m30(desde_str, hasta_str).json()
df_m30 = pd.DataFrame(patron_m30)
df_m30 = pd.DataFrame({"hora": range(24)}).merge(df_m30, on="hora", how="left")
st.line_chart(df_m30.set_index("hora")[["ocupacion_media"]])