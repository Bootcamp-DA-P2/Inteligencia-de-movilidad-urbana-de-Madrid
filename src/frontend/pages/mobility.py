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

# Si cambia el distrito, se olvida el sensor elegido antes
if "distrito_anterior" not in st.session_state:
    st.session_state.distrito_anterior = id_distrito
if st.session_state.distrito_anterior != id_distrito:
    st.session_state.pop("id_sensor_click", None)
    st.session_state.pop("selectbox_sensor", None)
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
            st.write(f"**{len(sensores)} sensores encontrados en {DISTRITOS[id_distrito]}. Haz clic en un punto del mapa para elegirlo:**")

            df = pd.DataFrame(sensores)

            # sensor ya elegido por clic previo (si lo hay)
            id_click = st.session_state.get("id_sensor_click")

            df["seleccionado"] = df["id_sensor"] == id_click
            df["tamano"] = df["seleccionado"].map({True: 22, False: 10})
            df["color"] = df["seleccionado"].map({True: "Seleccionado", False: "Sensor"})

            # --- Calcular centro y zoom automático según la dispersión de los sensores ---
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
                hover_name="id_sensor",
                hover_data={"cod_cent": True, "nombre_norm": True, "latitud": False, "longitud": False, "tamano": False, "color": False},
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

            # Si hubo clic nuevo, actualiza el sensor elegido y refresca
            puntos = evento["selection"]["points"] if evento and "selection" in evento else []
            if puntos:
                nuevo_id = puntos[0]["customdata"][0]
                if nuevo_id != id_click:
                    st.session_state.id_sensor_click = nuevo_id
                    st.session_state.selectbox_sensor = nuevo_id
                    st.rerun()

            # --- Desplegable como alternativa/confirmación ---
            #opciones_sensor = {
            #    s["id_sensor"]: f'Sensor {s["id_sensor"]} ({s["cod_cent"]})'
            #    for s in sensores
            #}
            opciones_sensor = {
                s["id_sensor"]: f'{s["nombre_norm"].capitalize()} (#{s["id_sensor"]})'
                for s in sensores
            }
            ids_disponibles = list(opciones_sensor.keys())

            id_sensor_seleccionado = st.selectbox(
                "Sensor elegido (o cámbialo aquí)",
                options=ids_disponibles,
                format_func=lambda x: opciones_sensor[x],
                key="selectbox_sensor",
            )

            # si el usuario cambia el desplegable en vez del mapa, sincronizamos
            if id_sensor_seleccionado != id_click:
                st.session_state.id_sensor_click = id_sensor_seleccionado

st.divider()

# --- Paso 3: predecir el sensor elegido ---
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