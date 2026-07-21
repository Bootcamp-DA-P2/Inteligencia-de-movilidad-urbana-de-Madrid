import math
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import osmnx as ox
import networkx as nx
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.traffic_service import get_prediction, get_sensores_distrito

from theme import apply_theme, header_banner
apply_theme()
header_banner("MadFlow: Ruta Optimizada", "Mejor recorrido según la ocupación")

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


@st.cache_resource(show_spinner="Descargando red de calles reales de Madrid (OpenStreetMap)...")
def cargar_grafo_calles(north: float, south: float, east: float, west: float):
    """
    Descarga el grafo real de calles (con sentidos únicos) para la zona indicada.
    Se cachea por bounding box: la primera vez tarda unos segundos, las
    siguientes veces sobre la misma zona es instantáneo.
    """
    grafo = ox.graph_from_bbox(
        bbox=(west, south, east, north),
        network_type="drive",   # solo vías para tráfico rodado, respeta sentidos únicos
        simplify=True,
    )
    return grafo


def calcular_bbox_corredor(lat1, lon1, lat2, lon2, factor_margen=0.4, margen_minimo_m=500):
    """
    Bounding box ajustado al corredor entre origen y destino (no al distrito
    entero), con un margen proporcional a la distancia directa para permitir
    pequeños rodeos. Esto reduce muchísimo el tamaño del grafo a descargar.
    """
    dist_directa = distancia_metros(lat1, lon1, lat2, lon2)
    margen_m = max(margen_minimo_m, dist_directa * factor_margen)

    lat_centro = (lat1 + lat2) / 2
    margen_lat = margen_m / 111320
    margen_lon = margen_m / (111320 * math.cos(math.radians(lat_centro)))

    north = max(lat1, lat2) + margen_lat
    south = min(lat1, lat2) - margen_lat
    east = max(lon1, lon2) + margen_lon
    west = min(lon1, lon2) - margen_lon
    return north, south, east, west


def filtrar_sensores_en_bbox(sensores: list[dict], north, south, east, west) -> list[dict]:
    """Nos quedamos solo con los sensores dentro del corredor de la ruta,
    para no tener que predecir la ocupación de todo el distrito."""
    filtrados = []
    for s in sensores:
        if s.get("latitud") is None or s.get("longitud") is None:
            continue
        lat, lon = float(s["latitud"]), float(s["longitud"])
        if south <= lat <= north and west <= lon <= east:
            filtrados.append(s)
    return filtrados


def obtener_ocupaciones_sensores(
    sensores: list[dict],
    intentos_previos: dict[int, float | None] | None = None,
) -> dict[int, float | None]:
    """
    Predice la ocupación de los sensores dados EN PARALELO (son peticiones
    HTTP independientes). Si una predicción falla, se guarda como None (no
    como 0.0) para no confundir "el sensor falló" con "ocupación real 0%".

    `intentos_previos`: dict compartido entre varias llamadas dentro del
    MISMO cálculo de ruta (por ejemplo, al ampliar el corredor). Si un
    sensor ya se intentó (con éxito o con fallo), no se vuelve a pedir:
    evita esperar otra vez 15s por sensores que ya sabemos que fallan.
    """
    ocupaciones = {}
    total = len(sensores)
    if total == 0:
        return ocupaciones

    if intentos_previos is None:
        intentos_previos = {}
    cache_sesion = st.session_state.setdefault("cache_predicciones_sensores", {})

    pendientes = []
    for s in sensores:
        id_s = s["id_sensor"]
        if id_s in intentos_previos:
            ocupaciones[id_s] = intentos_previos[id_s]
        elif id_s in cache_sesion:
            ocupaciones[id_s] = cache_sesion[id_s]
        else:
            pendientes.append(s)

    if not pendientes:
        return ocupaciones

    def predecir(s):
        id_s = s["id_sensor"]
        try:
            resp = get_prediction(int(id_s))
            if resp.status_code == 200:
                return id_s, resp.json()["prediccion_ocupacion"], None
            return id_s, None, f"HTTP {resp.status_code}"
        except Exception as e:
            return id_s, None, str(e)

    progreso = st.progress(0, text="Calculando ocupación prevista de los sensores cercanos a la ruta...")
    completados = 0
    errores = []

    # Muy pocos workers a la vez: el backend Django en desarrollo puede no
    # soportar bien varias peticiones simultáneas (provoca timeouts en cascada)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futuros = [executor.submit(predecir, s) for s in pendientes]
        for futuro in as_completed(futuros):
            id_s, valor, error = futuro.result()
            ocupaciones[id_s] = valor
            intentos_previos[id_s] = valor  # no se vuelve a intentar en esta misma ruta
            if valor is not None:
                cache_sesion[id_s] = valor
            else:
                errores.append((id_s, error))
            completados += 1
            progreso.progress(completados / len(pendientes), text=f"Calculando ocupación prevista... ({completados}/{len(pendientes)})")

    progreso.empty()

    if errores:
        st.warning(
            f"No se pudo predecir la ocupación de {len(errores)} de {len(pendientes)} sensores nuevos "
            f"(se excluyen del cálculo de la ruta). Ejemplo de error: sensor #{errores[0][0]} → {errores[0][1]}"
        )

    return ocupaciones


def calcular_ocupacion_por_arista(grafo, sensores: list[dict], ocupaciones: dict[int, float | None]) -> dict:
    """
    Para cada tramo de calle (arista) del grafo, busca el sensor real más
    cercano a su punto medio (excluyendo los que fallaron al predecir) y le
    asigna su ocupación prevista. Vectorizado con numpy para que sea rápido
    incluso con muchos tramos de calle.

    Devuelve: {(u, v): {"ocupacion": float, "id_sensor": int}}
    """
    coords_sensores = [
        (float(s["latitud"]), float(s["longitud"]), ocupaciones[s["id_sensor"]], s["id_sensor"])
        for s in sensores
        if s.get("latitud") is not None
        and s.get("longitud") is not None
        and ocupaciones.get(s["id_sensor"]) is not None
    ]
    if not coords_sensores:
        return {}

    lat_s = np.radians(np.array([c[0] for c in coords_sensores]))
    lon_s = np.radians(np.array([c[1] for c in coords_sensores]))
    ocup_s = np.array([c[2] for c in coords_sensores])
    id_s_arr = np.array([c[3] for c in coords_sensores])

    # (u, v) únicos, sin duplicar aristas paralelas
    pares = list(dict.fromkeys(grafo.edges()))
    lat_mid = np.radians(np.array([(grafo.nodes[u]["y"] + grafo.nodes[v]["y"]) / 2 for u, v in pares]))
    lon_mid = np.radians(np.array([(grafo.nodes[u]["x"] + grafo.nodes[v]["x"]) / 2 for u, v in pares]))

    R = 6371000
    dlat = lat_s[None, :] - lat_mid[:, None]
    dlon = lon_s[None, :] - lon_mid[:, None]
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat_mid[:, None]) * np.cos(lat_s[None, :]) * np.sin(dlon / 2) ** 2
    )
    distancias = 2 * R * np.arcsin(np.sqrt(a))  # forma (nº_aristas, nº_sensores)

    idx_min = np.argmin(distancias, axis=1)
    ocup_asignada = ocup_s[idx_min]
    id_asignado = id_s_arr[idx_min]

    return {
        par: {"ocupacion": float(ocup), "id_sensor": int(id_sensor)}
        for par, ocup, id_sensor in zip(pares, ocup_asignada, id_asignado)
    }


def sensores_relevantes_para_ruta(sensores: list[dict], grafo, ruta_nodos: list, radio_m: float = 350) -> list[dict]:
    """
    Devuelve solo los sensores que están cerca (a menos de radio_m) de ALGÚN
    punto de la ruta candidata. Así evitamos predecir la ocupación de todo
    el corredor rectangular cuando la ruta real solo usa unas pocas calles.
    """
    coords_ruta = [(grafo.nodes[n]["y"], grafo.nodes[n]["x"]) for n in ruta_nodos]
    relevantes = []
    for s in sensores:
        if s.get("latitud") is None or s.get("longitud") is None:
            continue
        lat_s, lon_s = float(s["latitud"]), float(s["longitud"])
        for lat_r, lon_r in coords_ruta:
            if distancia_metros(lat_s, lon_s, lat_r, lon_r) <= radio_m:
                relevantes.append(s)
                break
    return relevantes


def construir_grafo_ponderado(grafo, ocupacion_por_arista: dict, factor_trafico: float) -> nx.DiGraph:
    """
    Construye un grafo dirigido simple con el peso final de cada tramo:
    distancia × (1 + ocupación/100 × factor_tráfico). Al venir de un grafo
    "drive" de OSM, solo existen las aristas en el sentido real permitido:
    las calles de sentido único quedan respetadas automáticamente.
    """
    grafo_ponderado = nx.DiGraph()
    grafo_ponderado.add_nodes_from(grafo.nodes(data=True))

    for u, v, datos in grafo.edges(data=True):
        longitud_tramo = datos.get("length", 1.0)
        info_tramo = ocupacion_por_arista.get((u, v))
        ocupacion_tramo = info_tramo["ocupacion"] if info_tramo else None
        id_sensor_tramo = info_tramo["id_sensor"] if info_tramo else None
        peso = longitud_tramo * (1 + ((ocupacion_tramo or 0.0) / 100) * factor_trafico)

        nombre_calle = datos.get("name", "Calle sin nombre")
        if isinstance(nombre_calle, list):
            nombre_calle = nombre_calle[0]

        # Si hay varias aristas paralelas entre los mismos nodos, nos quedamos
        # con la de menor peso (la más favorable)
        if grafo_ponderado.has_edge(u, v):
            if peso < grafo_ponderado[u][v]["weight"]:
                grafo_ponderado[u][v].update(
                    weight=peso, length=longitud_tramo,
                    name=nombre_calle, ocupacion=ocupacion_tramo,
                    id_sensor=id_sensor_tramo,
                )
        else:
            grafo_ponderado.add_edge(
                u, v, weight=peso, length=longitud_tramo,
                name=nombre_calle, ocupacion=ocupacion_tramo,
                id_sensor=id_sensor_tramo,
            )

    return grafo_ponderado


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
    st.session_state.pop("ruta_nodos", None)
    st.session_state.pop("grafo_ruta", None)
    st.session_state.pop("grafo_nodos_coords", None)
    st.session_state.pop("ruta_sin_camino", None)

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
            # (usamos .get() en vez de acceso directo para que nunca falle
            # con AttributeError, pase lo que pase antes en la ejecución)
            if st.session_state.get("sel_origen") not in dict_sensores:
                st.session_state.sel_origen = sensores_distrito[0]["id_sensor"]
            if st.session_state.get("sel_destino") not in dict_sensores:
                st.session_state.sel_destino = sensores_distrito[min(1, len(sensores_distrito)-1)]["id_sensor"]

            # --- 2. DESPLEGABLES DE SELECCIÓN (OPTIMIZADO: CARGA INSTANTÁNEA) ---
            col1, col2 = st.columns(2)
            
            # Precalculamos los nombres una sola vez para evitar retrasos en el renderizado
            @st.cache_data(ttl=3600)
            def generar_nombres_sensores(sensores):
                nombres = {}
                for s in sensores:
                    id_s = s["id_sensor"]
                    nombre = s["nombre_calle"] or s["nombre_norm"] or f"Sensor {id_s}"
                    nombres[id_s] = f'{nombre.capitalize()} (# {id_s})'
                return nombres

            nombres_desplegable = generar_nombres_sensores(sensores_distrito)

            with col1:
                sensor_origen_id = st.selectbox(
                    "Sensor Origen",
                    options=list(dict_sensores.keys()),
                    format_func=lambda x: nombres_desplegable.get(x, f"Sensor #{x}"),
                    key="sel_origen"
                )

            with col2:
                opciones_dest = [ids for ids in dict_sensores.keys() if ids != st.session_state.sel_origen]
                sensor_destino_id = st.selectbox(
                    "Sensor Destino",
                    options=opciones_dest,
                    format_func=lambda x: nombres_desplegable.get(x, f"Sensor #{x}"),
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

            # --- 4. ALGORITMO DE RUTA REAL (GRAFO DE CALLES + DIJKSTRA) ---
            factor_trafico = st.slider(
                "Peso del tráfico en la ruta (más alto = evita más las calles con más ocupación)",
                min_value=0.0,
                max_value=30.0,
                value=8.0,
                step=1.0,
                help="Con 0 se obtiene la ruta más corta ignorando el tráfico. "
                     "Cuanto más alto, más está dispuesto el algoritmo a alargar la ruta con tal de evitar ocupación.",
            )

            if st.button("Calcular ruta con menos tráfico", type="primary"):
                sensor_origen = dict_sensores[st.session_state.sel_origen]
                sensor_destino = dict_sensores[st.session_state.sel_destino]

                lat_o, lon_o = float(sensor_origen["latitud"]), float(sensor_origen["longitud"])
                lat_d, lon_d = float(sensor_destino["latitud"]), float(sensor_destino["longitud"])

                ruta_nodos = None
                grafo = None
                grafo_ponderado = None
                intentos_previos_ocupacion: dict[int, float | None] = {}

                # Empezamos con un corredor ajustado (rápido) y solo lo ampliamos
                # si no se encuentra ni siquiera una ruta por distancia dentro de esa zona
                for factor_margen in (0.4, 0.8, 1.5):
                    with st.spinner("Calculando ruta sobre la red real de calles..."):
                        # 4.1 Bounding box del CORREDOR origen-destino (no de todo el distrito)
                        north, south, east, west = calcular_bbox_corredor(
                            lat_o, lon_o, lat_d, lon_d, factor_margen=factor_margen
                        )

                        grafo = cargar_grafo_calles(north, south, east, west)

                        # 4.2 "Enganchamos" el sensor de origen y destino al nodo de calle más cercano
                        nodo_origen = ox.distance.nearest_nodes(grafo, lon_o, lat_o)
                        nodo_destino = ox.distance.nearest_nodes(grafo, lon_d, lat_d)

                        # 4.3 PASADA RÁPIDA: ruta más corta por distancia, SIN llamar al backend.
                        #     Sirve de punto de partida para saber qué calles hay que mirar de verdad.
                        try:
                            ruta_actual = nx.dijkstra_path(grafo, nodo_origen, nodo_destino, weight="length")
                        except nx.NetworkXNoPath:
                            ruta_actual = None

                        if ruta_actual is None:
                            continue  # no hay ni ruta por distancia en este corredor: lo ampliamos

                        # 4.4 REFINAMIENTO ITERATIVO: en vez de predecir todos los sensores del
                        #     corredor (podían ser 50-90), solo predecimos los que están cerca de
                        #     la ruta candidata actual. Si al aplicar el tráfico la ruta cambia de
                        #     calles, repetimos (con las nuevas calles) hasta que se estabilice o
                        #     hasta un máximo de 3 vueltas.
                        grafo_ponderado = None
                        for _ in range(3):
                            sensores_cercanos = sensores_relevantes_para_ruta(sensores_distrito, grafo, ruta_actual)
                            obtener_ocupaciones_sensores(sensores_cercanos, intentos_previos=intentos_previos_ocupacion)

                            # Usamos TODOS los sensores con dato válido conocidos hasta ahora
                            # (de esta y de vueltas/corredores anteriores), no solo los de esta vuelta
                            sensores_con_dato = [
                                s for s in sensores_distrito
                                if intentos_previos_ocupacion.get(s["id_sensor"]) is not None
                            ]
                            ocupacion_por_arista = calcular_ocupacion_por_arista(
                                grafo, sensores_con_dato, intentos_previos_ocupacion
                            )
                            grafo_ponderado = construir_grafo_ponderado(grafo, ocupacion_por_arista, factor_trafico)

                            nueva_ruta = nx.dijkstra_path(grafo_ponderado, nodo_origen, nodo_destino, weight="weight")
                            if nueva_ruta == ruta_actual:
                                break  # la ruta ya no cambia: convergió, no hace falta seguir prediciendo
                            ruta_actual = nueva_ruta

                        ruta_nodos = ruta_actual
                        break  # ruta encontrada, no hace falta ampliar el corredor

                if ruta_nodos is not None:
                    st.session_state.ruta_nodos = ruta_nodos
                    st.session_state.grafo_ruta = grafo_ponderado
                    st.session_state.grafo_nodos_coords = {
                        n: (d["y"], d["x"]) for n, d in grafo.nodes(data=True)
                    }
                    st.session_state.pop("ruta_sin_camino", None)
                else:
                    st.session_state.pop("ruta_nodos", None)
                    st.session_state.ruta_sin_camino = True

            # --- 5. PRESENTACIÓN DE RESULTADOS Y MAPA DE RUTA ---
            if st.session_state.get("ruta_sin_camino"):
                st.error(
                    "No existe una ruta por calles reales entre esos dos sensores dentro de la zona "
                    "descargada (puede deberse a sentidos únicos o a que están fuera del radio cargado)."
                )

            if "ruta_nodos" in st.session_state:
                ruta_nodos = st.session_state.ruta_nodos
                grafo_ruta = st.session_state.grafo_ruta
                coords_nodos = st.session_state.grafo_nodos_coords

                st.divider()
                st.success("¡Ruta calculada sobre la red real de calles, respetando sentidos únicos!")

                # 5.1 Agrupamos tramos consecutivos con el mismo nombre de calle en una tabla legible
                tramos = []
                distancia_total = 0.0
                for u, v in zip(ruta_nodos[:-1], ruta_nodos[1:]):
                    datos = grafo_ruta[u][v]
                    nombre = datos.get("name") or "Calle sin nombre"
                    longitud = datos.get("length", 0.0)
                    ocupacion = datos.get("ocupacion")  # puede ser None si no hubo dato válido
                    id_sensor_edge = datos.get("id_sensor")
                    distancia_total += longitud

                    if tramos and tramos[-1]["nombre"] == nombre:
                        tramos[-1]["longitud"] += longitud
                        if ocupacion is not None:
                            tramos[-1]["ocup_ponderada"] += ocupacion * longitud
                            tramos[-1]["longitud_con_dato"] += longitud
                        if id_sensor_edge is not None:
                            tramos[-1]["sensores"].add(id_sensor_edge)
                    else:
                        tramos.append({
                            "nombre": nombre,
                            "longitud": longitud,
                            "ocup_ponderada": ocupacion * longitud if ocupacion is not None else 0.0,
                            "longitud_con_dato": longitud if ocupacion is not None else 0.0,
                            "sensores": {id_sensor_edge} if id_sensor_edge is not None else set(),
                        })

                datos_tabla = []
                for idx, t in enumerate(tramos):
                    tipo = "📍 Origen" if idx == 0 else ("🏁 Destino" if idx == len(tramos) - 1 else f"🔄 Tramo {idx}")
                    if t["longitud_con_dato"] > 0:
                        ocup_media = t["ocup_ponderada"] / t["longitud_con_dato"]
                        ocup_texto = f"{ocup_media:.2f}%"
                    else:
                        ocup_texto = "N/D"
                    ids_texto = ", ".join(f"#{i}" for i in sorted(t["sensores"])) if t["sensores"] else "—"
                    datos_tabla.append({
                        "Tramo": tipo,
                        "Calle": t["nombre"],
                        "Sensor(es) de referencia": ids_texto,
                        "Distancia (m)": round(t["longitud"]),
                        "Ocupación Prevista": ocup_texto,
                    })

                df_tabla = pd.DataFrame(datos_tabla)
                tabla_alineada = (
                    df_tabla.style
                    .set_properties(**{"text-align": "right"})
                    .set_table_styles([{"selector": "th", "props": [("text-align", "right")]}])
                )
                st.dataframe(tabla_alineada, use_container_width=True, hide_index=True)
                st.caption(f"Distancia total de la ruta: **{distancia_total / 1000:.2f} km** por calles reales, respetando sentidos únicos.")

                # 5.2 Mapa con la trayectoria real (siguiendo las calles) + origen/destino
                st.subheader("Mapa final de la trayectoria calculada")

                lats_ruta = [coords_nodos[n][0] for n in ruta_nodos]
                lons_ruta = [coords_nodos[n][1] for n in ruta_nodos]

                fig_ruta = go.Figure()

                fig_ruta.add_trace(go.Scattermapbox(
                    lat=lats_ruta,
                    lon=lons_ruta,
                    mode="lines",
                    line=dict(width=4, color="#1D4ED8"),
                    name="Ruta calculada",
                ))

                fig_ruta.add_trace(go.Scattermapbox(
                    lat=[lats_ruta[0]],
                    lon=[lons_ruta[0]],
                    mode="markers",
                    marker=dict(size=16, color="#EF4444"),
                    name="Origen",
                ))

                fig_ruta.add_trace(go.Scattermapbox(
                    lat=[lats_ruta[-1]],
                    lon=[lons_ruta[-1]],
                    mode="markers",
                    marker=dict(size=16, color="#10B981"),
                    name="Destino",
                ))

                fig_ruta.update_layout(
                    mapbox=dict(
                        style="open-street-map",
                        zoom=14,
                        center={"lat": sum(lats_ruta) / len(lats_ruta), "lon": sum(lons_ruta) / len(lons_ruta)},
                    ),
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    height=450,
                    legend=dict(bgcolor="rgba(255,255,255,0.7)"),
                )
                st.plotly_chart(fig_ruta, use_container_width=True)