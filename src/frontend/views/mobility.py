import math
import streamlit as st
import pandas as pd
import plotly.express as px
from services.traffic_service import get_prediction, get_sensores_distrito
import datetime

from theme import apply_theme, header_banner
apply_theme()
header_banner("MadFlow: Movilidad en Tiempo Real", "Mapa de tráfico de Madrid")

st.title("🚦 Predicción de tráfico en Madrid")

DISTRITOS = {
    1: "Centro", 2: "Arganzuela", 3: "Retiro", 4: "Salamanca", 5: "Chamartín",
    6: "Tetuán", 7: "Chamberí", 8: "Fuencarral-El Pardo", 9: "Moncloa-Aravaca",
    10: "Latina", 11: "Carabanchel", 12: "Usera", 13: "Puente de Vallecas",
    14: "Moratalaz", 15: "Ciudad Lineal", 16: "Hortaleza", 17: "Villaverde",
    18: "Villa de Vallecas", 19: "Vicálvaro", 20: "San Blas-Canillejas",
    21: "Barajas",
}


def marcar_seleccion_activa():
    st.session_state.seleccion_activa = True


def distancia_metros(lat1, lon1, lat2, lon2) -> float:
    """Distancia en metros entre dos puntos (lat/lon) usando la fórmula de Haversine."""
    R = 6371000  # radio de la Tierra en metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


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
    st.session_state.seleccion_activa = False
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

            # Guardamos los sensores del distrito actual para poder usarlos
            # más abajo en la predicción alternativa (todos los sensores)
            st.session_state.sensores_distrito = sensores

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
                on_change=marcar_seleccion_activa,
            )

            id_click = id_sensor_seleccionado

            df["seleccionado"] = df["id_sensor"] == id_click

            if st.session_state.get("seleccion_activa"):
                df["color"] = df["seleccionado"].map({True: "Seleccionado", False: "No elegido"})
            else:
                df["color"] = "Sensor"

            df["tamano"] = df["seleccionado"].map({True: 22, False: 10})

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
                color_discrete_map={
                    "Sensor": "#1f77b4",       # todos azules, sin selección
                    "No elegido": "#9e9e9e",   # gris, cuando hay selección pero no es este
                    "Seleccionado": "#e63946", # rojo, el elegido
                },
                center={"lat": lat_centro, "lon": lon_centro},
                zoom=zoom,
                height=500,
            )
            fig.update_layout(
                mapbox_style="open-street-map",
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                legend_title_text="",
                # --- Leyenda movida a arriba a la izquierda y con texto en negro ---
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
                nuevo_id = puntos[0]["customdata"][0]
                if nuevo_id != id_click:
                    st.session_state.click_pendiente = nuevo_id
                    st.session_state.seleccion_activa = True
                    st.rerun()

st.divider()

st.subheader("Predicción")

ETIQUETAS = {"bajo": "🟢 Tráfico bajo", "medio": "🟡 Tráfico medio", "alto": "🔴 Tráfico alto"}

if id_sensor_seleccionado:
    usar_fecha_concreta = st.checkbox("Predecir para una fecha/hora concreta (en vez de la más reciente)")
    fecha_elegida = None
    hora_elegida = None
    if usar_fecha_concreta:
        fecha_elegida = st.date_input(
            "Fecha",
            value=datetime.date.today(),
            min_value=datetime.date.today(),
        )

        if fecha_elegida == datetime.date.today():
            # Sumamos 1 a la hora actual para empezar desde la siguiente hora
            hora_inicio = datetime.datetime.now().hour + 1
            
            # Si ya son las 23:00 o más tarde, limitamos el rango para evitar errores
            if hora_inicio > 23:
                horas_disponibles = [23]  # O podías dejar una lista vacía/aviso
            else:
                horas_disponibles = list(range(hora_inicio, 24))
        else:
            horas_disponibles = list(range(24))

        hora_elegida = st.selectbox("Hora", options=horas_disponibles)

    # Inicializar variables de estado
    if "mostrar_principal" not in st.session_state:
        st.session_state.mostrar_principal = False
    if "mostrar_alternativa" not in st.session_state:
        st.session_state.mostrar_alternativa = False

    # Al pulsar Predecir, activamos la vista principal y reseteamos la alternativa anterior
    if st.button("Predecir"):
        st.session_state.mostrar_principal = True
        st.session_state.mostrar_alternativa = False

    # Renderizar la predicción principal si está activa
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

            st.markdown(f"### {ETIQUETAS[nivel]}")
            st.caption(f"Ocupación estimada: {porcentaje:.2f}%")

            if "fila_base" in data["campos_imputados"]:
                st.warning(" Predicción basada completamente en patrones históricos (no hay datos reales para esa fecha/hora).")
            elif not data["confiable"]:
                st.warning(" Predicción con estimación histórica parcial (algunos datos recientes faltan).")
            else:
                st.success(" Predicción con datos reales completos.")
            
            # MOSTRAR SECCIÓN ALTERNATIVA SOLO SI NO ESTÁ MARCADA LA OPCIÓN
            if not usar_fecha_concreta:
                st.divider()
                st.subheader("Predicción alternativa: sensores cercanos al seleccionado")
                
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

                        # Control para elegir cuántos comparar
                        n_cercanos = st.slider(
                            "Número de sensores cercanos a comparar",
                            min_value=1,
                            max_value=min(20, max(len(sensores_distrito) - 1, 1)),
                            value=min(5, max(len(sensores_distrito) - 1, 1)),
                            key="slider_sensores_cercanos"
                        )

                        # SEGUNDO BOTÓN: Solo aparece aquí abajo si no está marcada la opción
                        if st.button("Calcular predicción alternativa"):
                            st.session_state.mostrar_alternativa = True

                        # Renderizar los resultados de los sensores cercanos si se pulsó el segundo botón
                        if st.session_state.mostrar_alternativa:
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

                            resultados = []
                            total = len(mas_cercanos)
                            progreso = st.progress(0, text="Calculando predicciones alternativas...")

                            for i, (dist, s) in enumerate(mas_cercanos):
                                id_s = s["id_sensor"]
                                nombre = s["nombre_calle"] or s["nombre_norm"] or f"Sensor {id_s}"
                                nombre_completo = f"{nombre.capitalize()} (# {id_s})"

                                try:
                                    # Mantiene la consulta en tiempo real (más reciente) para los alternativos
                                    resp = get_prediction(int(id_s))
                                    if resp.status_code == 200:
                                        data_alt = resp.json()
                                        nivel_alt = data_alt["nivel_congestion"]
                                        resultados.append({
                                            "Sensor": nombre_completo,
                                            "Distancia (m)": round(dist),
                                            "Nivel Ocupación": ETIQUETAS.get(nivel_alt, nivel_alt),
                                            "Ocupación prevista (%)": round(data_alt["prediccion_ocupacion"], 2),
                                            "Confiable": "🟢 Sí" if data_alt["confiable"] else "⚠️ Estimada",
                                        })
                                    else:
                                        resultados.append({
                                            "Sensor": nombre_completo,
                                            "Distancia (m)": round(dist),
                                            "Nivel Ocupación": "❌ Sin datos",
                                            "Ocupación prevista (%)": None,
                                            "Confiable": "❌ Error",
                                        })
                                except Exception:
                                    resultados.append({
                                        "Sensor": nombre_completo,
                                        "Distancia (m)": round(dist),
                                        "Nivel Ocupación": "❌ Error crítico",
                                        "Ocupación prevista (%)": None,
                                        "Confiable": "❌ Error",
                                    })

                                progreso.progress((i + 1) / total, text=f"Calculando... ({i + 1}/{total})")

                            progreso.empty()

                            df_resultados = (
                                pd.DataFrame(resultados)
                                .sort_values("Distancia (m)", ascending=True, na_position="last")
                                .reset_index(drop=True)
                            )
                            
                            st.write(
                                f"Sensores más cercanos a **{nombre_mostrar(sensor_base)}**, "
                                "ordenados de **menor a mayor** ocupación prevista:"
                            )

                            # Configuración para alinear las columnas de texto a la derecha
                            config_columnas = {
                                "Nivel Ocupación": st.column_config.TextColumn(
                                    "Nivel Ocupación",
                                    alignment="right"
                                ),
                                "Confiable": st.column_config.TextColumn(
                                    "Confiable",
                                    alignment="right"
                                )
                            }
                            st.dataframe(
                                df_resultados,
                                width="stretch",
                                hide_index=True,
                                column_config=config_columnas 
                            )
        else:
            st.error(f"Error: {response.json().get('error', 'desconocido')}")
else:
    st.info("Elige primero un distrito y un sensor para ver la predicción.")
    st.session_state.mostrar_principal = False
    st.session_state.mostrar_alternativa = False