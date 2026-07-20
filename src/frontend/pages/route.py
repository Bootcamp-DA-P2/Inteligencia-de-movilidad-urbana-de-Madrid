import math
import streamlit as st
import pandas as pd
import plotly.express as px
from services.traffic_service import get_prediction, get_sensores_distrito

st.title("🛣️ Ruta Optimizada por Ocupación")

DISTRITOS = {
    1: "Centro", 2: "Arganzuela", 3: "Retiro", 4: "Salamanca", 5: "Chamartín",
    6: "Tetuán", 7: "Chamberí", 8: "Fuencarral-El Pardo", 9: "Moncloa-Aravaca",
    10: "Latina", 11: "Carabanchel", 12: "Usera", 13: "Puente de Vallecas",
    14: "Moratalaz", 15: "Ciudad Lineal", 16: "Hortaleza", 17: "Villaverde",
    18: "Villa de Vallecas", 19: "Vicálvaro", 20: "San Blas-Canillejas",
    21: "Barajas",
}

def distancia_metros(lat1, lon1, lat2, lon2) -> float:
    """Distancia en metros entre dos puntos usando Haversine."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

# 1. Selección de Distrito
id_distrito = st.selectbox(
    "Selecciona un Distrito para la Ruta",
    options=list(DISTRITOS.keys()),
    format_func=lambda x: f"{x} - {DISTRITOS[x]}",
    key="ruta_distrito_selectbox"
)

if "distrito_anterior" not in st.session_state or st.session_state.distrito_anterior != id_distrito:
    st.session_state.distrito_anterior = id_distrito
    st.session_state.sel_origen = None
    st.session_state.sel_destino = None
    st.session_state.pop("ruta_calculada_df", None)
    st.session_state.pop("sensores_ruta_filtrados", None)

if id_distrito:
    response_sensores = get_sensores_distrito(id_distrito)

    if response_sensores.status_code != 200:
        st.error("No se pudieron cargar los sensores de este distrito.")
    else:
        sensores_distrito = response_sensores.json()["sensores"]

        if not sensores_distrito:
            st.warning("Este distrito no tiene sensores disponibles.")
        else:
            dict_sensores = {s["id_sensor"]: s for s in sensores_distrito}
            
            # Inicializar origen y destino por defecto si no están definidos
            if st.session_state.sel_origen not in dict_sensores:
                st.session_state.sel_origen = sensores_distrito[0]["id_sensor"]
            if st.session_state.sel_destino not in dict_sensores:
                st.session_state.sel_destino = sensores_distrito[min(1, len(sensores_distrito)-1)]["id_sensor"]

            # --- 2. DESPLEGABLES DE SELECCIÓN ---
            col1, col2 = st.columns(2)
            
            def obtener_nombre_por_id(id_s):
                s = dict_sensores.get(id_s)
                if not s: return f"Sensor #{id_s}"
                nombre = s["nombre_calle"] or s["nombre_norm"] or f"Sensor {s['id_sensor']}"
                return f'{nombre.capitalize()} (# {s["id_sensor"]})'

            with col1:
                sensor_origen_id = st.selectbox(
                    "Sensor Origen",
                    options=list(dict_sensores.keys()),
                    format_func=obtener_nombre_por_id,
                    key="sel_origen"
                )

            with col2:
                opciones_dest = [ids for ids in dict_sensores.keys() if ids != st.session_state.sel_origen]
                sensor_destino_id = st.selectbox(
                    "Sensor Destino",
                    options=opciones_dest,
                    format_func=obtener_nombre_por_id,
                    key="sel_destino"
                )

            # --- 3. MAPA GLOBAL DE PREVISUALIZACIÓN ---
            df_seleccion = pd.DataFrame(sensores_distrito)
            df_seleccion["latitud"] = pd.to_numeric(df_seleccion["latitud"], errors="coerce")
            df_seleccion["longitud"] = pd.to_numeric(df_seleccion["longitud"], errors="coerce")
            df_seleccion = df_seleccion.dropna(subset=["latitud", "longitud"])
            
            def asignar_estado(id_s):
                if id_s == st.session_state.sel_origen:
                    return "🔴 Origen Seleccionado"
                if id_s == st.session_state.sel_destino:
                    return "🟢 Destino Seleccionado"
                return "🔵 Sensor Disponible"
                
            df_seleccion["Estado"] = df_seleccion["id_sensor"].apply(asignar_estado)
            df_seleccion["tamano"] = df_seleccion["id_sensor"].apply(
                lambda x: 25 if (x == st.session_state.sel_origen or x == st.session_state.sel_destino) else 12
            )
            df_seleccion["nombre_hover"] = df_seleccion["nombre_calle"].fillna(df_seleccion["nombre_norm"])

            fig_select = px.scatter_mapbox(
                df_seleccion,
                lat="latitud",
                lon="longitud",
                color="Estado",
                size="tamano",
                size_max=25,
                hover_name="nombre_hover",
                color_discrete_map={
                    "🔴 Origen Seleccionado": "#EF4444",
                    "🟢 Destino Seleccionado": "#10B981",
                    "🔵 Sensor Disponible": "#93C5FD"
                },
                center={"lat": df_seleccion["latitud"].mean(), "lon": df_seleccion["longitud"].mean()},
                zoom=13,
                height=400,
            )
            fig_select.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig_select, use_container_width=True)

            # --- 4. ALGORITMO MULTI-RUTA DE ALTA VELOCIDAD (OPTIMIZADO CON CACHÉ DE RED) ---
            if st.button("Calcular ruta con menos tráfico", type="primary"):
                sensor_origen = dict_sensores[st.session_state.sel_origen]
                sensor_destino = dict_sensores[st.session_state.sel_destino]
                
                with st.spinner("Optimizando trayectorias en tiempo real..."):
                    lat_dest = float(sensor_destino["latitud"])
                    lon_dest = float(sensor_destino["longitud"])
                    
                    # Diccionario local de caché para evitar peticiones HTTP duplicadas
                    cache_predicciones = {}
                    
                    def obtener_ocupacion_veloz(id_sensor):
                        """Consulta la predicción una sola vez y la guarda en memoria rápida."""
                        if id_sensor in cache_predicciones:
                            return cache_predicciones[id_sensor]
                        try:
                            resp = get_prediction(int(id_sensor))
                            if resp.status_code == 200:
                                val = resp.json()["prediccion_ocupacion"]
                            else:
                                val = 50.0  # Valor neutral por defecto
                        except Exception:
                            val = 50.0
                        cache_predicciones[id_sensor] = val
                        return val

                    rutas_candidatas = []
                    
                    # Reducimos a 3 iteraciones estratégicas y óptimas para no sobrecargar
                    for radio_salto in [1000, 1800, 2800]:
                        ruta_actual = [sensor_origen]
                        visitados = {sensor_origen["id_sensor"]}
                        nodo_actual = sensor_origen
                        fallo = False
                        
                        for _ in range(12):
                            lat_act = float(nodo_actual["latitud"])
                            lon_act = float(nodo_actual["longitud"])
                            
                            dist_al_destino = distancia_metros(lat_act, lon_act, lat_dest, lon_dest)
                            
                            if dist_al_destino < 180:
                                break
                                
                            vecinos = []
                            for s in sensores_distrito:
                                if s["id_sensor"] in visitados or s["id_sensor"] == sensor_destino["id_sensor"]:
                                    continue
                                    
                                d_vecino = distancia_metros(lat_act, lon_act, float(s["latitud"]), float(s["longitud"]))
                                d_futura = distancia_metros(float(s["latitud"]), float(s["longitud"]), lat_dest, lon_dest)
                                
                                # Filtrado geométrico instantáneo antes de llamar a la red
                                if d_vecino < radio_salto and d_futura < dist_al_destino:
                                    vecinos.append((d_futura, s))
                            
                            if not vecinos:
                                # Margen de emergencia rápido
                                for s in sensores_distrito:
                                    if s["id_sensor"] in visitados or s["id_sensor"] == sensor_destino["id_sensor"]:
                                        continue
                                    d_vecino = distancia_metros(lat_act, lon_act, float(s["latitud"]), float(s["longitud"]))
                                    if d_vecino < (radio_salto * 1.3):
                                        vecinos.append((distancia_metros(float(s["latitud"]), float(s["longitud"]), lat_dest, lon_dest), s))
                            
                            if not vecinos:
                                fallo = True
                                break
                            
                            # Filtro geométrico rápido: nos quedamos con los 3 que mejor avancen
                            vecinos.sort(key=lambda x: x[0])
                            candidatos_reales = [v[1] for v in vecinos[:3]]
                            
                            # Evaluación veloz usando la caché local
                            puntuaciones = []
                            for cand in candidatos_reales:
                                ocup = obtener_ocupacion_veloz(cand["id_sensor"])
                                puntuaciones.append((ocup, cand))
                            
                            puntuaciones.sort(key=lambda x: x[0])
                            nodo_actual = puntuaciones[0][1]
                            
                            ruta_actual.append(nodo_actual)
                            visitados.add(nodo_actual["id_sensor"])
                        
                        if not fallo or len(ruta_actual) > 1:
                            if ruta_actual[-1]["id_sensor"] != sensor_destino["id_sensor"]:
                                ruta_actual.append(sensor_destino)
                            
                            # Coste total de la ruta resuelto desde memoria local
                            suma_ocupacion = sum(obtener_ocupacion_veloz(s["id_sensor"]) for s in ruta_actual)
                            ocupacion_media = suma_ocupacion / len(ruta_actual)
                            rutas_candidatas.append((ocupacion_media, ruta_actual))
                    
                    if rutas_candidatas:
                        rutas_candidatas.sort(key=lambda x: x[0])
                        mejor_ruta = rutas_candidatas[0][1]
                    else:
                        mejor_ruta = [sensor_origen, sensor_destino]
                    
                    # Formatear la tabla final extrayendo los datos ya almacenados en caché
                    datos_tabla = []
                    for idx, s in enumerate(mejor_ruta):
                        tipo = "📍 Origen" if idx == 0 else ("🏁 Destino" if idx == len(mejor_ruta) - 1 else f"🔄 Paso {idx}")
                        nombre_calle = s["nombre_calle"] or s["nombre_norm"] or f"Sensor {s['id_sensor']}"
                        
                        ocup_val = cache_predicciones.get(s["id_sensor"], 50.0)
                        ocupacion_texto = f"{ocup_val:.2f}%" if ocup_val != 50.0 else "N/D"
                            
                        datos_tabla.append({
                            "Tramo": tipo,
                            "Calle / Sensor": f"{nombre_calle.capitalize()} (#{s['id_sensor']})",
                            "Ocupación Prevista": ocupacion_texto
                        })
                    
                    st.session_state.ruta_calculada_df = pd.DataFrame(datos_tabla)
                    st.session_state.sensores_ruta_filtrados = mejor_ruta

            # --- 5. PRESENTACIÓN DE RESULTADOS Y MAPA DE RUTA ---
            if "ruta_calculada_df" in st.session_state:
                st.divider()
                st.success("¡Ruta óptima de menor ocupación calculada con éxito!")
                st.dataframe(st.session_state.ruta_calculada_df, use_container_width=True, hide_index=True)
                
                st.subheader("Mapa final de la trayectoria calculada")
                
                df_mapa = pd.DataFrame(st.session_state.sensores_ruta_filtrados)
                df_mapa["latitud"] = pd.to_numeric(df_mapa["latitud"], errors="coerce")
                df_mapa["longitud"] = pd.to_numeric(df_mapa["longitud"], errors="coerce")
                
                id_o = st.session_state.sel_origen
                id_d = st.session_state.sel_destino
                
                df_mapa["Color Ruta"] = df_mapa["id_sensor"].apply(
                    lambda x: "Azul Fuerte (Origen/Destino)" if (x == id_o or x == id_d) else "Azul Claro (Paso Intermedio)"
                )
                df_mapa["tamano"] = df_mapa["id_sensor"].apply(lambda x: 24 if (x == id_o or x == id_d) else 14)
                df_mapa["nombre_hover"] = df_mapa["nombre_calle"].fillna(df_mapa["nombre_norm"])

                fig_ruta = px.scatter_mapbox(
                    df_mapa,
                    lat="latitud",
                    lon="longitud",
                    color="Color Ruta",
                    size="tamano",
                    size_max=24,
                    hover_name="nombre_hover",
                    hover_data={"id_sensor": True, "tamano": False},
                    color_discrete_map={
                        "Azul Fuerte (Origen/Destino)": "#1D4ED8",
                        "Azul Claro (Paso Intermedio)": "#60A5FA"
                    },
                    center={"lat": df_mapa["latitud"].mean(), "lon": df_mapa["longitud"].mean()},
                    zoom=14,
                    height=450,
                )
                fig_ruta.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
                st.plotly_chart(fig_ruta, use_container_width=True)