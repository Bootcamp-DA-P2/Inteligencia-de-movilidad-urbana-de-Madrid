import streamlit as st
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

# --- Paso 1: elegir distrito ---
st.subheader("Buscar sensor por distrito")

id_distrito = st.selectbox(
    "Distrito",
    options=list(DISTRITOS.keys()),
    format_func=lambda x: f"{x} - {DISTRITOS[x]}",
)

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
            # --- Paso 2: mostrar el listado de sensores del distrito ---
            st.write(f"**{len(sensores)} sensores encontrados en {DISTRITOS[id_distrito]}:**")
            st.dataframe(
                sensores,
                use_container_width=True,
                column_order=["id_sensor", "cod_cent", "nombre_norm", "latitud", "longitud"],
            )

            opciones_sensor = {
                s["id_sensor"]: f'Sensor {s["id_sensor"]} ({s["cod_cent"]})'
                for s in sensores
            }

            id_sensor_seleccionado = st.selectbox(
                "Elige un sensor de la lista",
                options=list(opciones_sensor.keys()),
                format_func=lambda x: opciones_sensor[x],
            )

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