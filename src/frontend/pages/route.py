import math
import streamlit as st
import pandas as pd
import numpy as np
import base64
import plotly.express as px
import plotly.graph_objects as go
import osmnx as ox
import networkx as nx
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.traffic_service import get_prediction, get_sensores_distrito

def svg_to_data_uri(svg_str: str) -> str:
    """Convierte una cadena SVG a Base64 seguro para HTML."""
    b64 = base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"

# Definición de SVGs limpios
SVG_ORIGEN_STR = """<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='#EF4444'><path d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z'/></svg>"""
SVG_DESTINO_STR = """<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='#10B981'><path d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z'/></svg>"""
SVG_RUTA_STR = """<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='#1D4ED8'><path d='M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z'/></svg>"""

SVG_ORIGEN = svg_to_data_uri(SVG_ORIGEN_STR)
SVG_DESTINO = svg_to_data_uri(SVG_DESTINO_STR)
SVG_RUTA = svg_to_data_uri(SVG_RUTA_STR)

st.set_page_config(page_title="{SVG_RUTA} Ruta Inteligente de Tráfico", layout="wide")

# Mensaje de cabecera limpio
st.title("🗺️ Planificador de Ruta Inteligente")
st.markdown("Optimiza tu trayecto evitando tramos con alta densidad de tráfico en tiempo real.")

DISTRITOS = {
    1: "Centro", 2: "Arganzuela", 3: "Retiro", 4: "Salamanca", 5: "Chamartín",
    6: "Tetuán", 7: "Chamberí", 8: "Fuencarral-El Pardo", 9: "Moncloa-Aravaca",
    10: "Latina", 11: "Carabanchel", 12: "Usera", 13: "Puente de Vallecas",
    14: "Moratalaz", 15: "Ciudad Lineal", 16: "Hortaleza", 17: "Villaverde",
    18: "Villa de Vallecas", 19: "Vicálvaro", 20: "San Blas-Canillejas",
    21: "Barajas",
}

# Constantes visuales
ESTADO_ORIGEN = "Origen Seleccionado"
ESTADO_DESTINO = "Destino Seleccionado"
ESTADO_DISPONIBLE = "Sensor Disponible"

COLOR_ORIGEN = "#EF4444"      
COLOR_DESTINO = "#10B981"     
COLOR_DISPONIBLE = "#93C5FD"  
COLOR_RUTA = "#1D4ED8"        


def distancia_metros(lat1, lon1, lat2, lon2) -> float:
    """Distancia en metros entre dos puntos usando Haversine."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


@st.cache_data(ttl=1800, show_spinner=False)
def cargar_todos_los_sensores():
    todos = []
    for id_d in DISTRITOS.keys():
        try:
            resp = get_sensores_distrito(id_d)
            if resp.status_code == 200:
                todos.extend(resp.json().get("sensores", []))
        except Exception:
            continue
    return todos


@st.cache_resource(show_spinner="Preparando mapa base del callejero...")
def cargar_grafo_calles(north: float, south: float, east: float, west: float):
    return ox.graph_from_bbox(
        bbox=(west, south, east, north),
        network_type="drive",
        simplify=True,
    )


def calcular_bbox_corredor(lat1, lon1, lat2, lon2, factor_margen=0.4, margen_minimo_m=500):
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


def obtener_ocupaciones_sensores(
    sensores: list[dict],
    intentos_previos: dict[int, float | None] | None = None,
) -> dict[int, float | None]:
    ocupaciones = {}
    if not sensores:
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

    progreso = st.progress(0, text="Analizando estado del tráfico en tiempo real...")
    completados = 0

    with ThreadPoolExecutor(max_workers=6) as executor:
        futuros = [executor.submit(predecir, s) for s in pendientes]
        for futuro in as_completed(futuros):
            id_s, valor, error = futuro.result()
            ocupaciones[id_s] = valor
            intentos_previos[id_s] = valor
            if valor is not None:
                cache_sesion[id_s] = valor
            completados += 1
            progreso.progress(completados / len(pendientes), text=f"Analizando tráfico en la zona... ({completados}/{len(pendientes)})")

    progreso.empty()
    return ocupaciones


def calcular_ocupacion_por_arista(grafo, sensores: list[dict], ocupaciones: dict[int, float | None]) -> dict:
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
    distancias = 2 * R * np.arcsin(np.sqrt(a))

    idx_min = np.argmin(distancias, axis=1)
    return {
        par: {"ocupacion": float(ocup_s[idx_min[i]]), "id_sensor": int(id_s_arr[idx_min[i]])}
        for i, par in enumerate(pares)
    }


def sensores_relevantes_para_ruta(sensores: list[dict], grafo, ruta_nodos: list, radio_m: float = 350) -> list[dict]:
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


# --- 1. SELECCIÓN DE ÁMBITO ---
modo_ambito = st.radio(
    "Selecciona el área de búsqueda:",
    options=["Madrid Completo", "Por Distrito"],
    horizontal=True,
    key="modo_ambito_radio"
)

sensores_disponibles = []

if modo_ambito == "Por Distrito":
    id_distrito = st.selectbox(
        "Selecciona un Distrito",
        options=list(DISTRITOS.keys()),
        format_func=lambda x: f"{x} - {DISTRITOS[x]}",
        key="ruta_distrito_selectbox"
    )
    if "distrito_anterior" not in st.session_state or st.session_state.distrito_anterior != id_distrito:
        st.session_state.distrito_anterior = id_distrito
        st.session_state.pop("sel_origen", None)
        st.session_state.pop("sel_destino", None)
        st.session_state.pop("ruta_nodos", None)

    if id_distrito:
        resp = get_sensores_distrito(id_distrito)
        if resp.status_code == 200:
            sensores_disponibles = resp.json().get("sensores", [])
        else:
            st.error("No se han podido obtener los datos del distrito seleccionado.")
else:
    with st.spinner("Cargando puntos de control en Madrid..."):
        sensores_disponibles = cargar_todos_los_sensores()

if not sensores_disponibles:
    st.warning("No hay datos de tráfico disponibles para esta zona.")
else:
    dict_sensores = {s["id_sensor"]: s for s in sensores_disponibles}

    if st.session_state.get("sel_origen") not in dict_sensores:
        st.session_state.sel_origen = sensores_disponibles[0]["id_sensor"]
    if st.session_state.get("sel_destino") not in dict_sensores:
        st.session_state.sel_destino = sensores_disponibles[min(1, len(sensores_disponibles)-1)]["id_sensor"]

    # --- 2. DESPLEGABLES DE SELECCIÓN CON ICONOS SVG ---
    col1, col2 = st.columns(2)

    @st.cache_data(ttl=3600)
    def generar_nombres_sensores(sensores):
        nombres = {}
        for s in sensores:
            id_s = s["id_sensor"]
            nombre = s.get("nombre_calle") or s.get("nombre_norm") or f"Punto #{id_s}"
            nombres[id_s] = f'{nombre.capitalize()} (Sensor #{id_s})'
        return nombres

    nombres_desplegable = generar_nombres_sensores(sensores_disponibles)

    with col1:
        st.markdown(f"### <img src='{SVG_ORIGEN}' style='vertical-align: middle; margin-right: 8px;'/> Punto de Origen", unsafe_allow_html=True)
        sensor_origen_id = st.selectbox(
            "Origen",
            options=list(dict_sensores.keys()),
            format_func=lambda x: nombres_desplegable.get(x, f"Sensor #{x}"),
            key="sel_origen",
            label_visibility="collapsed"
        )

    with col2:
        st.markdown(f"### <img src='{SVG_DESTINO}' style='vertical-align: middle; margin-right: 8px;'/> Punto de Destino", unsafe_allow_html=True)
        opciones_dest = [ids for ids in dict_sensores.keys() if ids != st.session_state.sel_origen]
        sensor_destino_id = st.selectbox(
            "Destino",
            options=opciones_dest,
            format_func=lambda x: nombres_desplegable.get(x, f"Sensor #{x}"),
            key="sel_destino",
            label_visibility="collapsed"
        )

    # --- 3. MAPA GLOBAL DE PREVISUALIZACIÓN ---
    df_seleccion = pd.DataFrame(sensores_disponibles)
    df_seleccion["latitud"] = pd.to_numeric(df_seleccion["latitud"], errors="coerce")
    df_seleccion["longitud"] = pd.to_numeric(df_seleccion["longitud"], errors="coerce")
    df_seleccion = df_seleccion.dropna(subset=["latitud", "longitud"])

    def asignar_estado(id_s):
        if id_s == st.session_state.sel_origen:
            return ESTADO_ORIGEN
        if id_s == st.session_state.sel_destino:
            return ESTADO_DESTINO
        return ESTADO_DISPONIBLE

    df_seleccion["Estado"] = df_seleccion["id_sensor"].apply(asignar_estado)

    if modo_ambito == "Madrid Completo":
        df_mapa_prev = df_seleccion[
            df_seleccion["id_sensor"].isin([st.session_state.sel_origen, st.session_state.sel_destino])
        ].copy()
    else:
        df_mapa_prev = df_seleccion.copy()

    df_mapa_prev["tamano"] = df_mapa_prev["id_sensor"].apply(
        lambda x: 20 if (x == st.session_state.sel_origen or x == st.session_state.sel_destino) else 10
    )
    df_mapa_prev["Calle"] = df_mapa_prev["nombre_calle"].fillna(df_mapa_prev["nombre_norm"]).fillna("Calle sin identificar")

    fig_select = px.scatter_mapbox(
        df_mapa_prev,
        lat="latitud",
        lon="longitud",
        color="Estado",
        size="tamano",
        size_max=20,
        hover_name="Calle",
        hover_data={
            "id_sensor": True,
            "Estado": True,
            "latitud": ":.5f",
            "longitud": ":.5f",
            "tamano": False,
        },
        color_discrete_map={
            ESTADO_ORIGEN: COLOR_ORIGEN,
            ESTADO_DESTINO: COLOR_DESTINO,
            ESTADO_DISPONIBLE: COLOR_DISPONIBLE
        },
        center={"lat": df_mapa_prev["latitud"].mean(), "lon": df_mapa_prev["longitud"].mean()},
        zoom=12 if modo_ambito == "Madrid Completo" else 13,
        height=380,
    )
    fig_select.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig_select, use_container_width=True)

    # --- 4. ALGORITMO DE RUTA REAL ---
    st.markdown("---")
    factor_trafico = st.slider(
        "Sensibilidad al tráfico (a mayor valor, la ruta evitará en mayor medida las retenciones):",
        min_value=0.0,
        max_value=30.0,
        value=8.0,
        step=1.0,
        help="0 calcula la distancia geométrica más corta. Valores altos priorizan calles más fluídas."
    )

    if st.button("Calcular Ruta Optimizada", type="primary", use_container_width=True):
        sensor_origen = dict_sensores[st.session_state.sel_origen]
        sensor_destino = dict_sensores[st.session_state.sel_destino]

        lat_o, lon_o = float(sensor_origen["latitud"]), float(sensor_origen["longitud"])
        lat_d, lon_d = float(sensor_destino["latitud"]), float(sensor_destino["longitud"])

        ruta_nodos = None
        grafo = None
        grafo_ponderado = None
        intentos_previos_ocupacion: dict[int, float | None] = {}

        for factor_margen in (0.4, 0.8, 1.5):
            with st.spinner("Calculando la trayectoria óptima por la red vial..."):
                north, south, east, west = calcular_bbox_corredor(
                    lat_o, lon_o, lat_d, lon_d, factor_margen=factor_margen
                )

                grafo = cargar_grafo_calles(north, south, east, west)

                nodo_origen = ox.distance.nearest_nodes(grafo, lon_o, lat_o)
                nodo_destino = ox.distance.nearest_nodes(grafo, lon_d, lat_d)

                try:
                    ruta_actual = nx.dijkstra_path(grafo, nodo_origen, nodo_destino, weight="length")
                except nx.NetworkXNoPath:
                    ruta_actual = None

                if ruta_actual is None:
                    continue

                for _ in range(3):
                    sensores_cercanos = sensores_relevantes_para_ruta(sensores_disponibles, grafo, ruta_actual)
                    obtener_ocupaciones_sensores(sensores_cercanos, intentos_previos=intentos_previos_ocupacion)

                    sensores_con_dato = [
                        s for s in sensores_disponibles
                        if intentos_previos_ocupacion.get(s["id_sensor"]) is not None
                    ]
                    ocupacion_por_arista = calcular_ocupacion_por_arista(
                        grafo, sensores_con_dato, intentos_previos_ocupacion
                    )
                    grafo_ponderado = construir_grafo_ponderado(grafo, ocupacion_por_arista, factor_trafico)

                    nueva_ruta = nx.dijkstra_path(grafo_ponderado, nodo_origen, nodo_destino, weight="weight")
                    if nueva_ruta == ruta_actual:
                        break
                    ruta_actual = nueva_ruta

                ruta_nodos = ruta_actual
                break

        if ruta_nodos is not None:
            st.session_state.ruta_nodos = ruta_nodos
            st.session_state.grafo_ruta = grafo_ponderado
            st.session_state.grafo_nodos_coords = {
                n: (d["y"], d["x"]) for n, d in grafo.nodes(data=True)
            }
            st.session_state.coords_origen_real = (lat_o, lon_o)
            st.session_state.coords_destino_real = (lat_d, lon_d)
            st.session_state.pop("ruta_sin_camino", None)
        else:
            st.session_state.pop("ruta_nodos", None)
            st.session_state.ruta_sin_camino = True

    # --- 5. RESULTADOS, TABLA Y MAPA FINAL ---
    if st.session_state.get("ruta_sin_camino"):
        st.error("No ha sido posible encontrar un trayecto accesible entre los dos puntos seleccionados.")

    if "ruta_nodos" in st.session_state:
        ruta_nodos = st.session_state.ruta_nodos
        grafo_ruta = st.session_state.grafo_ruta
        coords_nodos = st.session_state.grafo_nodos_coords
        lat_o_real, lon_o_real = st.session_state.coords_origen_real
        lat_d_real, lon_d_real = st.session_state.coords_destino_real

        sensor_origen = dict_sensores[st.session_state.sel_origen]
        sensor_destino = dict_sensores[st.session_state.sel_destino]

        st.divider()
        st.success("¡Ruta recomendada calculada con éxito!")

        # --- CONSTRUCCIÓN RÁPIDA DE LA TABLA CON LOGOS SVG ---
        tramos = []
        distancia_total = 0.0
        for u, v in zip(ruta_nodos[:-1], ruta_nodos[1:]):
            datos = grafo_ruta[u][v]
            nombre = datos.get("name") or "Calle sin nombre"
            longitud = datos.get("length", 0.0)
            ocupacion = datos.get("ocupacion")
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

        calle_origen = (sensor_origen.get("nombre_calle") or sensor_origen.get("nombre_norm") or "Calle sin nombre").capitalize()
        calle_destino = (sensor_destino.get("nombre_calle") or sensor_destino.get("nombre_norm") or "Calle sin nombre").capitalize()

        # Usamos marcas HTML con los SVGs incrustados para la tabla
        datos_tabla = [{
            "Etapa": "Origen",
            "Calle / Vía": calle_origen,
            "Sensor(es) Cercanos": f"#{sensor_origen['id_sensor']}",
            "Distancia": "0 m",
            "Saturación Prevista": "Punto de Salida",
        }]

        for idx, t in enumerate(tramos):
            ocup_texto = f"{t['ocup_ponderada'] / t['longitud_con_dato']:.1f}%" if t["longitud_con_dato"] > 0 else "Sin datos"
            ids_texto = ", ".join(f"#{i}" for i in sorted(t["sensores"])) if t["sensores"] else "—"
            dist_texto = f"{round(t['longitud'])} m" if t['longitud'] < 1000 else f"{t['longitud']/1000:.2f} km"

            datos_tabla.append({
                "Etapa": f"Tramo {idx + 1}",
                "Calle / Vía": t["nombre"],
                "Sensor(es) Cercanos": ids_texto,
                "Distancia": dist_texto,
                "Saturación Prevista": ocup_texto,
            })

        datos_tabla.append({
            "Etapa": "Destino",
            "Calle / Vía": calle_destino,
            "Sensor(es) Cercanos": f"#{sensor_destino['id_sensor']}",
            "Distancia": "Llegada",
            "Saturación Prevista": "Punto de Llegada",
        })

        st.markdown(f"### <img src='{SVG_RUTA}' align='top'/> Itinerario detallado de la ruta", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(datos_tabla), use_container_width=True, hide_index=True)
        st.caption(f"Distancia total estimada del recorrido: **{distancia_total / 1000:.2f} km**.")

        # --- MAPA FINAL CON DETALLES MEJORADOS ---
        st.markdown(f"### <img src='{SVG_RUTA}' align='top'/> Vista interactiva del trayecto", unsafe_allow_html=True)

        lats_ruta = [coords_nodos[n][0] for n in ruta_nodos]
        lons_ruta = [coords_nodos[n][1] for n in ruta_nodos]

        fig_ruta = go.Figure()

        # Línea de ruta
        fig_ruta.add_trace(go.Scattermapbox(
            lat=[lat_o_real] + lats_ruta + [lat_d_real],
            lon=[lon_o_real] + lons_ruta + [lon_d_real],
            mode="lines",
            line=dict(width=5, color=COLOR_RUTA),
            name="Ruta calculada",
            hoverinfo="skip"
        ))

        hovertemplate_fmt = (
            "<b>%{customdata[0]}</b><br><br>"
            "<b>ID Sensor:</b> %{customdata[1]}<br>"
            "<b>Estado:</b> %{customdata[2]}<br>"
            "<b>Latitud:</b> %{customdata[3]:.5f}<br>"
            "<b>Longitud:</b> %{customdata[4]:.5f}<extra></extra>"
        )

        # Marcador Origen
        fig_ruta.add_trace(go.Scattermapbox(
            lat=[lat_o_real], lon=[lon_o_real],
            mode="markers",
            marker=dict(size=16, color=COLOR_ORIGEN),
            name="Origen",
            customdata=[[calle_origen, sensor_origen["id_sensor"], ESTADO_ORIGEN, lat_o_real, lon_o_real]],
            hovertemplate=hovertemplate_fmt
        ))

        # Marcador Destino
        fig_ruta.add_trace(go.Scattermapbox(
            lat=[lat_d_real], lon=[lon_d_real],
            mode="markers",
            marker=dict(size=16, color=COLOR_DESTINO),
            name="Destino",
            customdata=[[calle_destino, sensor_destino["id_sensor"], ESTADO_DESTINO, lat_d_real, lon_d_real]],
            hovertemplate=hovertemplate_fmt
        ))

        fig_ruta.update_layout(
            mapbox=dict(
                style="open-street-map",
                zoom=13,
                center={"lat": (lat_o_real + lat_d_real) / 2, "lon": (lon_o_real + lon_d_real) / 2},
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=450,
            legend=dict(bgcolor="rgba(255,255,255,0.8)"),
        )
        st.plotly_chart(fig_ruta, use_container_width=True)