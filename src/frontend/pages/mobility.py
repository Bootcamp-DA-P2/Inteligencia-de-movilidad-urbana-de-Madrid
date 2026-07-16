import streamlit as st
from services.traffic_service import get_prediction

st.title("🚦 Predicción de tráfico en Madrid")

id_sensor = st.number_input("ID de sensor", min_value=1, value=9841, step=1)

if st.button("Predecir"):
    with st.spinner("Calculando predicción..."):
        response = get_prediction(int(id_sensor))
    if response.status_code == 200:
        data = response.json()
        st.metric("Ocupación prevista (%)", f"{data['prediccion_ocupacion']:.2f}")
        if not data["confiable"]:
            st.warning("⚠️ Predicción con estimación histórica (aún acumulando datos en vivo para este sensor).")
        else:
            st.success("🟢 Predicción con datos reales completos.")
    else:
        st.error(f"Error: {response.json().get('error', 'desconocido')}")