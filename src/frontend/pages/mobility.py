import streamlit as st
import pandas as pd
import plotly.express as px
from services.traffic_service import get_prediction, get_sensores_distrito

st.title("🚦 Predicción de tráfico en Madrid")

DISTRITOS = {
    1: "Centro", 2: "Arganzuela", 3: "Retiro", 4: "Salamanca", 5: "Chamartín",
    6: "Tetuán", 7: "Chamberí", 8: "Fuencarral-El Pardo", 9: "Moncloa-Aravaca",
    10: "Latina", 11: "Carabanchel", 12: "Usera", 13: "Puente de Vallecas",
    14: "Moratalaz", 15: "Ciudad Lineal", 16: "Hortaleza", 17: "Villaverde",
    18: "Villa de Vallecas", 19: "Vicálvaro", 20: "San Blas-Canillejas",
    21: "Barajas",
}

# --- elegir distrito ---
st.subheader("Buscar sensor por distrito")

id_distrito = st.selectbox(
    "Distrito",
    options=list(DISTRITOS.keys()),
    format_func=lambda x: f"{x} - {DISTRITOS[x]}",
)

if "distrito_anterior" not in st.session_state:
    st.session_state.distrito_anterior = id_distrito
if st.session_state.distrito_anterior != id_distrito:
    st.session_state.pop("selectbox_sensor", None)
    st.session_state.pop("click_pendiente", None)
    st.session_state.distrito_anterior = id_distrito

id_sensor_seleccionado = None

if id_distrito:
    response_sensores = get_sensores_distrito(id_distrito)

    if response_sensores.status_code != 200:
        st.error("No se pudieron cargar los sensores de este distrito.")
    else:
        sensores = response_sensores.json()["sensores"]

        if not sensores:
            st.warning("Este distrito no tiene sensores disponibles.")
        else:
            st.write(f"**{len(sensores)} sensores encontrados en {DISTRITOS[id_distrito]}. Haz clic en un punto del mapa o elige de la lista:**")

            df = pd.DataFrame(sensores)
            df["latitud"] = pd.to_numeric(df["latitud"], errors="coerce")
            df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")
            df = df.dropna(subset=["latitud", "longitud"])

            df["nombre_hover"] = df["nombre_calle"].fillna(df["nombre_norm"]).fillna("Sin nombre")

            def nombre_mostrar(s: dict) -> str:
                nombre = s["nombre_calle"] or s["nombre_norm"] or f"Sensor {s['id_sensor']}"
                return f'{nombre.capitalize()} (#{s["id_sensor"]})'

            opciones_sensor = {
                s["id_sensor"]: nombre_mostrar(s)
                for s in sensores
            }
            ids_disponibles = list(opciones_sensor.keys())

            # Si hubo un clic pendiente del mapa, aplícalo ANTES de crear el widget
            if "click_pendiente" in st.session_state:
                st.session_state.selectbox_sensor = st.session_state.pop("click_pendiente")

            if st.session_state.get("selectbox_sensor") not in ids_disponibles:
                st.session_state.pop("selectbox_sensor", None)

            id_sensor_seleccionado = st.selectbox(
                "Sensor elegido (o cámbialo aquí)",
                options=ids_disponibles,
                format_func=lambda x: opciones_sensor[x],
                key="selectbox_sensor",
            )

            id_click = id_sensor_seleccionado

            df["seleccionado"] = df["id_sensor"] == id_click
            df["tamano"] = df["seleccionado"].map({True: 22, False: 10})
            df["color"] = df["seleccionado"].map({True: "Seleccionado", False: "Sensor"})

            lat_min, lat_max = df["latitud"].min(), df["latitud"].max()
            lon_min, lon_max = df["longitud"].min(), df["longitud"].max()

            lat_centro = (lat_min + lat_max) / 2
            lon_centro = (lon_min + lon_max) / 2

            margen = 1.3
            span_lat = (lat_max - lat_min) * margen
            span_lon = (lon_max - lon_min) * margen
            span = max(span_lat, span_lon, 0.005)
            zoom_calculado = 12 - (span ** 0.4) * 8
            zoom_auto = float(max(13.0, min(zoom_calculado, 15.0)))

            zoom = st.slider(
                "Zoom del mapa",
                min_value=9.0,
                max_value=17.0,
                value=zoom_auto,
                step=0.5,
                key=f"zoom_{id_distrito}",
            )

            fig = px.scatter_mapbox(
                df,
                lat="latitud",
                lon="longitud",
                color="color",
                size="tamano",
                size_max=22,
                custom_data=["id_sensor"],
                hover_name="nombre_hover",
                hover_data={"id_sensor": True, "cod_cent": True, "latitud": False, "longitud": False, "tamano": False, "color": False},
                color_discrete_map={"Sensor": "#1f77b4", "Seleccionado": "#e63946"},
                center={"lat": lat_centro, "lon": lon_centro},
                zoom=zoom,
                height=500,
            )
            fig.update_layout(
                mapbox_style="open-street-map",
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                legend_title_text="",
            )

            evento = st.plotly_chart(
                fig,
                use_container_width=True,
                on_select="rerun",
                selection_mode="points",
                key="mapa_sensores",
            )

            puntos = evento["selection"]["points"] if evento and "selection" in evento else []
            if puntos:
                nuevo_id = puntos[0]["customdata"][0]
                if nuevo_id != id_click:
                    st.session_state.click_pendiente = nuevo_id
                    st.rerun()

st.divider()

st.subheader("Predicción")

if id_sensor_seleccionado:
    if st.button("Predecir"):
        with st.spinner("Calculando predicción..."):
            response = get_prediction(int(id_sensor_seleccionado))
        if response.status_code == 200:
            data = response.json()
            st.metric("Ocupación prevista (%)", f"{data['prediccion_ocupacion']:.2f}")
            if not data["confiable"]:
                st.warning("⚠️ Predicción con estimación histórica (aún acumulando datos en vivo para este sensor).")
            else:
                st.success("🟢 Predicción con datos reales completos.")
        else:
            st.error(f"Error: {response.json().get('error', 'desconocido')}")
else:
    st.info("Elige primero un distrito y un sensor para ver la predicción.")