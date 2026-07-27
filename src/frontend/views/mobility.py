import math
import streamlit as st
import pandas as pd
import plotly.express as px
from services.traffic_service import get_prediction, get_sensores_distrito, get_predictions_batch
import datetime
import time

from theme import apply_theme, header_banner

apply_theme()
header_banner("MadFlow: Movilidad en Tiempo Real", "Mapa de tráfico de Madrid")

with st.container(border=True):
    st.markdown("### Planifica tus desplazamientos")
    st.markdown("""
Consulta la ocupación prevista del tráfico en Madrid en tiempo real o para una fecha futura.

MadFlow analiza datos históricos y recientes para recomendar las mejores alternativas cercanas y ayudarte a evitar zonas con mayor congestión.
""")

DISTRITOS = {
    1: "Centro", 2: "Arganzuela", 3: "Retiro", 4: "Salamanca", 5: "Chamartín",
    6: "Tetuán", 7: "Chamberí", 8: "Fuencarral-El Pardo", 9: "Moncloa-Aravaca",
    10: "Latina", 11: "Carabanchel", 12: "Usera", 13: "Puente de Vallecas",
    14: "Moratalaz", 15: "Ciudad Lineal", 16: "Hortaleza", 17: "Villaverde",
    18: "Villa de Vallecas", 19: "Vicálvaro", 20: "San Blas-Canillejas",
    21: "Barajas",
}

def distancia_metros(lat1, lon1, lat2, lon2) -> float:
    """Distancia en metros entre dos puntos (lat/lon) usando la fórmula de Haversine."""
    R = 6371000  # radio de la Tierra en metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# --- 1. SELECCIÓN DE TIPO Y FECHA DE PREDICCIÓN (ARRIBA) ---
st.subheader("Tipo de predicción")

modo_prediccion = st.radio(
    "Tipo de predicción",
    [
        "Tiempo real",
        "Fecha futura"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

usar_fecha_concreta = modo_prediccion == "Fecha futura"

fecha_elegida = None
hora_elegida = None

if modo_prediccion == "Tiempo real":
    st.caption(
        "Predice la ocupación del tráfico para la próxima hora disponible. "
        "Por ejemplo, si son las 12:15, la estimación se realizará para las 13:00."
    )
else:
    st.caption(
        "Selecciona una fecha y hora concreta para consultar la predicción."
    )
    
    # --- MOVIDO AQUÍ: Selección de fecha y hora ---
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        fecha_elegida = st.date_input(
            "Fecha",
            value=datetime.date.today(),
            min_value=datetime.date.today(),
        )

    with col_f2:
        if fecha_elegida == datetime.date.today():
            hora_inicio = datetime.datetime.now().hour + 1
            if hora_inicio > 23:
                horas_disponibles = [23]
            else:
                horas_disponibles = list(range(hora_inicio, 24))
        else:
            horas_disponibles = list(range(24))

        hora_elegida = st.selectbox(
            "Hora",
            options=horas_disponibles,
        )


st.divider()

# --- 2. SELECCIÓN DE UBICACIÓN Y MAPA ---
st.subheader("Selecciona una ubicación")

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
    st.session_state.pop("mapa_sensores", None)
    st.session_state.seleccion_activa = False
    st.session_state.distrito_anterior = id_distrito

id_sensor_seleccionado = None

if "seleccion_activa" not in st.session_state:
    st.session_state.seleccion_activa = False

if id_distrito:
    response_sensores = get_sensores_distrito(id_distrito)

    if response_sensores.status_code != 200:
        st.error("No se pudieron cargar los sensores de este distrito.")
    else:
        sensores = response_sensores.json()["sensores"]

        if not sensores:
            st.warning("Este distrito no tiene sensores disponibles.")
        else:
            st.caption(
                f"{len(sensores)} ubicaciones monitorizadas en {DISTRITOS[id_distrito]}."
            )

            df = pd.DataFrame(sensores)
            df["latitud"] = pd.to_numeric(df["latitud"], errors="coerce")
            df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")
            df = df.dropna(subset=["latitud", "longitud"])

            df["nombre_hover"] = df["nombre_calle"].fillna(df["nombre_norm"]).fillna("Sin nombre")

            st.session_state.sensores_distrito = sensores

            def nombre_mostrar(s: dict) -> str:
                nombre = s["nombre_calle"] or s["nombre_norm"] or f"Sensor {s['id_sensor']}"
                return f'{nombre.capitalize()} (#{s["id_sensor"]})'

            opciones_sensor = {
                s["id_sensor"]: nombre_mostrar(s)
                for s in sensores
            }
            ids_disponibles = list(opciones_sensor.keys())

            if "selectbox_sensor" not in st.session_state:
                st.session_state.selectbox_sensor = ids_disponibles[0]

            if "click_pendiente" in st.session_state:
                st.session_state.selectbox_sensor = st.session_state.pop("click_pendiente")
                st.session_state.seleccion_activa = True

            if st.session_state.get("selectbox_sensor") not in ids_disponibles:
                st.session_state.pop("selectbox_sensor", None)

            def cambiar_desde_lista():
                st.session_state.seleccion_activa = True

            id_sensor_seleccionado = st.selectbox(
                "Ubicación seleccionada",
                options=ids_disponibles,
                format_func=lambda x: opciones_sensor[x],
                key="selectbox_sensor",
                on_change=cambiar_desde_lista,
            )

            df["seleccionado"] = df["id_sensor"] == id_sensor_seleccionado

            if st.session_state.get("seleccion_activa"):
                df["color"] = df["seleccionado"].map({True: "Seleccionado", False: "No elegido"})
            else:
                df["color"] = "Sensor"

            df["tamano"] = df["seleccionado"].map({True: 22, False: 8})

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

            st.caption(
                "Selecciona una ubicación haciendo clic en el mapa o desde la lista."
            )

            fig = px.scatter_map(
                df,
                lat="latitud",
                lon="longitud",
                color="color",
                size="tamano",
                size_max=22,
                custom_data=["id_sensor"],
                hover_name="nombre_hover",
                hover_data={"id_sensor": True, "cod_cent": True, "latitud": False, "longitud": False, "tamano": False, "color": False},
                color_discrete_map={
                    "Sensor": "#1f77b4",
                    "No elegido": "#9e9e9e",
                    "Seleccionado": "#e63946",
                },
                center={"lat": lat_centro, "lon": lon_centro},
                zoom=zoom_auto,
                height=500,
            )
            fig.update_layout(
                map_style="open-street-map",
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                legend_title_text="",
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.98,
                    xanchor="left",
                    x=0.02,
                    bgcolor="rgba(255, 255, 255, 0.6)",
                    font=dict(color="black")
                )
            )

            evento = st.plotly_chart(
                fig,
                width="stretch",
                on_select="rerun",
                selection_mode="points",
                key="mapa_sensores",
            )

            puntos = evento["selection"]["points"] if evento and "selection" in evento else []
            if puntos:
                nuevo_id = int(puntos[0]["customdata"][0])
                if nuevo_id != st.session_state.get("selectbox_sensor"):
                    st.session_state.click_pendiente = nuevo_id
                    st.session_state.seleccion_activa = True
                    st.rerun()

st.divider()

# RESULTADOS DE LA PREDICCIÓN
st.subheader("Predicción de movilidad")

ETIQUETAS = {"bajo": "🟢 Tráfico bajo", "medio": "🟡 Tráfico medio", "alto": "🔴 Tráfico alto"}

if id_sensor_seleccionado:
    # Inicializar variables de estado
    if "mostrar_principal" not in st.session_state:
        st.session_state.mostrar_principal = False

    # Creamos dos columnas para poner los botones juntos
    col_btn1, col_btn2, _ = st.columns([0.2, 0.2, 0.6])

    with col_btn1:
        if st.button("Generar predicción", type="primary", width="content"):
            st.session_state.mostrar_principal = True

    with col_btn2:
        if st.button("Limpiar búsqueda", type="secondary", width="content"):
            st.session_state.mostrar_principal = False
            st.session_state.pop("click_pendiente", None)
            st.session_state.pop("mapa_sensores", None)
            st.session_state.seleccion_activa = False
            st.rerun()

    # Mostrar la predicción
    if st.session_state.mostrar_principal:
        with st.spinner("Calculando predicción..."):
            response = get_prediction(
                int(id_sensor_seleccionado),
                fecha=fecha_elegida.isoformat() if fecha_elegida else None,
                hora=hora_elegida,
            )
        
        if response.status_code == 200:
            data = response.json()
            nivel = data["nivel_congestion"]
            porcentaje = data["prediccion_ocupacion"]

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Estado previsto",
                    ETIQUETAS[nivel],
                )

            with col2:
                st.metric(
                    "Ocupación estimada",
                    f"{porcentaje:.1f} %",
                )

            ultima_hora = data.get("ultima_hora_datos")

            if "fila_base" in data["campos_imputados"]:
                st.warning(
                    "Predicción basada en patrones históricos para la fecha y hora seleccionadas."
                )
            elif ultima_hora:
                st.info(
                    f"Datos actualizados hasta las {ultima_hora}."
                )
            
            # MOSTRAR SECCIÓN ALTERNATIVA SOLO SI NO ESTÁ MARCADA LA OPCIÓN
            if not usar_fecha_concreta:
                st.divider()
                st.subheader("Rutas alternativas")

                st.caption(
                    "MadFlow ha identificado automáticamente las calles cercanas con menor congestión prevista para ayudarte a evitar retenciones."
                )
                
                sensores_distrito = st.session_state.get("sensores_distrito")
                
                if not sensores_distrito:
                    st.info("No hay sensores del distrito cargados todavía.")
                else:
                    sensor_base = next(
                        (s for s in sensores_distrito if s["id_sensor"] == id_sensor_seleccionado),
                        None,
                    )

                    if sensor_base is None or sensor_base.get("latitud") is None or sensor_base.get("longitud") is None:
                        st.warning("No se encontraron coordenadas para el sensor seleccionado.")
                    else:
                        lat_base = float(sensor_base["latitud"])
                        lon_base = float(sensor_base["longitud"])

                        n_cercanos = 8
                        candidatos = []
                        for s in sensores_distrito:
                            if s["id_sensor"] == id_sensor_seleccionado:
                                continue
                            if s.get("latitud") is None or s.get("longitud") is None:
                                continue
                            dist = distancia_metros(lat_base, lon_base, float(s["latitud"]), float(s["longitud"]))
                            candidatos.append((dist, s))

                        candidatos.sort(key=lambda x: x[0])
                        mas_cercanos = candidatos[:n_cercanos]

                        ids_sensores = [s["id_sensor"] for _, s in mas_cercanos]

                        with st.spinner("Espere unos momentos mientras analizamos las mejores alternativas de movilidad..."):
                            resp_batch = get_predictions_batch(ids_sensores)

                        predicciones = {}

                        if resp_batch.status_code != 200:
                            st.error("No se pudieron obtener las rutas alternativas.")
                        else:
                            predicciones = {
                                p["id_sensor"]: p
                                for p in resp_batch.json()
                            }
                        resultados = []
                       
                        for dist, s in mas_cercanos:
                            id_s = s["id_sensor"]
                            nombre = s["nombre_calle"] or s["nombre_norm"] or f"Sensor {id_s}"
                            nombre_completo = f"{nombre.capitalize()} (# {id_s})"

                            data_alt = predicciones.get(id_s)

                            if data_alt:
                                nivel_alt = data_alt["nivel_congestion"]
                                resultados.append({
                                    "Sensor": nombre_completo,
                                    "Distancia (m)": round(dist),
                                    "Nivel Ocupación": ETIQUETAS.get(nivel_alt, nivel_alt),
                                    "Ocupación prevista (%)": round(data_alt["prediccion_ocupacion"], 2),
                                    "Confiable": "Sí" if data_alt["confiable"] else "Estimada",
                                })
                            else:
                                resultados.append({
                                    "Sensor": nombre_completo,
                                    "Distancia (m)": round(dist),
                                    "Nivel Ocupación": "Sin datos",
                                    "Ocupación prevista (%)": None,
                                    "Confiable": "Sin datos",
                                })

                        df_resultados = (
                            pd.DataFrame(resultados)
                            .sort_values(
                                ["Ocupación prevista (%)", "Distancia (m)"],
                                ascending=[True, True],
                                na_position="last",
                            )
                            .reset_index(drop=True)
                        )

                        df_resultados.insert(
                            0,
                            "Recomendación",
                            [f"#{i}" for i in range(1, len(df_resultados) + 1)]
                        )

                        df_resultados = df_resultados.rename(
                            columns={
                                "Sensor": "Ubicación",
                                "Distancia (m)": "Distancia",
                                "Nivel Ocupación": "Estado previsto",
                                "Ocupación prevista (%)": "Ocupación",
                                "Confiable": "Calidad"
                            }
                        )

                        st.write(
                            f"Estas son las mejores alternativas cercanas a **{nombre_mostrar(sensor_base)}**, ordenadas de menor a mayor nivel de congestión previsto."
                        )

                        top3 = df_resultados.head(3)

                        for i, fila in top3.iterrows():
                            with st.container(border=True):
                                col1, col2 = st.columns([5,1])
                                with col1:
                                    st.markdown(f"""
                        ### #{i+1} {fila["Ubicación"]}

                        **{fila["Estado previsto"]}**

                        A {fila["Distancia"]} m
                        """)
                                with col2:
                                    st.metric(
                                        "Ocupación",
                                        f'{fila["Ocupación"]:.0f}%'
                                    )

                        st.divider()

                        st.subheader("Más alternativas cercanas")

                        st.dataframe(
                            df_resultados.iloc[3:],
                            hide_index=True,
                            width="stretch",
                            column_config={
                                "Recomendación": st.column_config.TextColumn(
                                    "Ranking",
                                    width="small",
                                ),
                                "Ubicación": st.column_config.TextColumn(
                                    "Ubicación",
                                    width="large",
                                ),
                                "Distancia": st.column_config.NumberColumn(
                                    "Distancia",
                                    format="%d m",
                                ),
                                "Ocupación": st.column_config.ProgressColumn(
                                    "Ocupación",
                                    min_value=0,
                                    max_value=100,
                                    format="%.0f%%",
                                ),
                            },
                        )
        else:
            st.error(f"Error API: {response.status_code}")
            st.code(response.text[:2000])
else:
    st.info("Elige primero un distrito y un sensor para ver la predicción.")
    st.session_state.mostrar_principal = False
    st.session_state.mostrar_alternativa = False