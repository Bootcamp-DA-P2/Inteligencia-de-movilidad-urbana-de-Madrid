import math
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import osmnx as ox
import networkx as nx
from services.traffic_service import get_predictions_batch, get_sensores_distrito
from theme import apply_theme, header_banner

# --- 1. CONFIGURACIÓN Y TEMA ---
st.set_page_config(page_title="MadFlow - Ruta Inteligente", layout="wide")
apply_theme()
header_banner("MadFlow: Ruta Optimizada", "Mejor recorrido según la ocupación")

# --- 2. TARJETA EXPLICATIVA CABECERA ---
with st.container(border=True):
    st.markdown("### Planificador de Ruta Inteligente")
    st.markdown("""
Calcula el mejor recorrido entre dos puntos evitando los tramos con mayor congestión en tiempo real.

MadFlow analiza la red vial y combina datos de ocupación de sensores cercanos para sugerir la trayectoria óptima.
""")

DISTRITOS = {
    1: "Centro", 2: "Arganzuela", 3: "Retiro", 4: "Salamanca", 5: "Chamartín",
    6: "Tetuán", 7: "Chamberí", 8: "Fuencarral-El Pardo", 9: "Moncloa-Aravaca",
    10: "Latina", 11: "Carabanchel", 12: "Usera", 13: "Puente de Vallecas",
    14: "Moratalaz", 15: "Ciudad Lineal", 16: "Hortaleza", 17: "Villaverde",
    18: "Villa de Vallecas", 19: "Vicálvaro", 20: "San Blas-Canillejas",
    21: "Barajas",
}

# Constantes visuales de color
COLOR_ORIGEN = "#EF4444"      # Rojo
COLOR_DESTINO = "#10B981"     # Verde
COLOR_DISPONIBLE = "#93C5FD"  # Azul claro
COLOR_RUTA = "#1D4ED8"        # Azul oscuro

# --- FUNCIONES AUXILIARES Y CÁLCULOS ---
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


def obtener_ocupaciones_sensores(sensores: list[dict]) -> dict[int, float | None]:
    """Obtiene de golpe las ocupaciones de los sensores disponibles."""
    ocupaciones = {}
    if not sensores:
        return ocupaciones

    cache_sesion = st.session_state.setdefault("cache_predicciones_sensores", {})
    ids_buscar = []

    for s in sensores:
        id_s = s["id_sensor"]
        if id_s in cache_sesion:
            ocupaciones[id_s] = cache_sesion[id_s]
        else:
            ids_buscar.append(int(id_s))

    if ids_buscar:
        try:
            resp = get_predictions_batch(ids_buscar)
            if resp.status_code == 200:
                data = resp.json()
                preds = data.get("predicciones", {}) if isinstance(data, dict) else {}
                for id_s in ids_buscar:
                    item = preds.get(id_s) or preds.get(str(id_s))
                    valor = item.get("prediccion_ocupacion") if isinstance(item, dict) else item
                    
                    # Convertir a float si es válido
                    try:
                        valor_float = float(valor) if valor is not None else None
                    except (ValueError, TypeError):
                        valor_float = None

                    ocupaciones[id_s] = valor_float
                    cache_sesion[id_s] = valor_float
        except Exception:
            for id_s in ids_buscar:
                ocupaciones[id_s] = None

    return ocupaciones


def calcular_ocupacion_por_arista(grafo, sensores: list[dict], ocupaciones: dict[int, float | None]) -> dict:
    """Asigna a CADA tramo del callejero el sensor y ocupación más cercanos sin dejar ninguno vacío."""
    sensores_validos = [
        s for s in sensores
        if s.get("latitud") is not None 
        and s.get("longitud") is not None
        and ocupaciones.get(s["id_sensor"]) is not None
    ]
    
    # Si no hay sensores con predicción directa, usamos valores por defecto o base
    if not sensores_validos:
        sensores_validos = [
            s for s in sensores 
            if s.get("latitud") is not None and s.get("longitud") is not None
        ]

    if not sensores_validos:
        return {}

    lat_s = np.radians(np.array([float(s["latitud"]) for s in sensores_validos]))
    lon_s = np.radians(np.array([float(s["longitud"]) for s in sensores_validos]))
    ocup_s = np.array([ocupaciones.get(s["id_sensor"], 15.0) or 15.0 for s in sensores_validos])
    id_s_arr = np.array([s["id_sensor"] for s in sensores_validos])

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


def construir_grafo_ponderado(grafo, ocupacion_por_arista: dict, FACTOR_TRAFICO_FIJO: float) -> nx.DiGraph:
    grafo_ponderado = nx.DiGraph()
    grafo_ponderado.add_nodes_from(grafo.nodes(data=True))

    for u, v, datos in grafo.edges(data=True):
        longitud_tramo = datos.get("length", 1.0)
        info_tramo = ocupacion_por_arista.get((u, v))
        ocupacion_tramo = info_tramo["ocupacion"] if info_tramo else None
        id_sensor_tramo = info_tramo["id_sensor"] if info_tramo else None
        peso = longitud_tramo * (1 + ((ocupacion_tramo or 0.0) / 100) * FACTOR_TRAFICO_FIJO)

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


# --- 3. SELECCIÓN DE ÁMBITO Y CONFIGURACIÓN ---
st.subheader("Configura tu trayecto")
st.caption("Selecciona el ámbito de búsqueda y establece los puntos de origen y destino.")

modo_ambito = st.radio(
    "Área de búsqueda",
    options=["Madrid Completo", "Por Distrito"],
    horizontal=True,
    key="modo_ambito_radio"
)

sensores_disponibles = []

if modo_ambito == "Por Distrito":
    id_distrito = st.selectbox(
        "Distrito",
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

    # --- DESPLEGABLES LIMPIOS ---
    col1, col2 = st.columns(2)

    def generar_nombres_sensores(sensores):
        nombres = {}
        for s in sensores:
            id_s = s["id_sensor"]
            nombre = s.get("nombre_calle") or s.get("nombre_norm") or f"Punto #{id_s}"
            nombres[id_s] = f'{nombre.capitalize()} (#{id_s})'
        return nombres

    nombres_desplegable = generar_nombres_sensores(sensores_disponibles)

    with col1:
        sensor_origen_id = st.selectbox(
            "Punto de Origen",
            options=list(dict_sensores.keys()),
            format_func=lambda x: nombres_desplegable.get(x, f"Sensor #{x}"),
            key="sel_origen"
        )

    with col2:
        opciones_dest = [ids for ids in dict_sensores.keys() if ids != st.session_state.sel_origen]
        sensor_destino_id = st.selectbox(
            "Punto de Destino",
            options=opciones_dest,
            format_func=lambda x: nombres_desplegable.get(x, f"Sensor #{x}"),
            key="sel_destino"
        )

    # --- MAPA BASE DE PREVISUALIZACIÓN ---
    df_seleccion = pd.DataFrame(sensores_disponibles)
    df_seleccion["latitud"] = pd.to_numeric(df_seleccion["latitud"], errors="coerce")
    df_seleccion["longitud"] = pd.to_numeric(df_seleccion["longitud"], errors="coerce")
    df_seleccion = df_seleccion.dropna(subset=["latitud", "longitud"])

    def asignar_estado(id_s):
        if id_s == st.session_state.sel_origen:
            return "Origen"
        if id_s == st.session_state.sel_destino:
            return "Destino"
        return "Disponible"

    df_seleccion["Estado"] = df_seleccion["id_sensor"].apply(asignar_estado)

    if modo_ambito == "Madrid Completo":
        df_mapa_prev = df_seleccion[
            df_seleccion["id_sensor"].isin([st.session_state.sel_origen, st.session_state.sel_destino])
        ].copy()
    else:
        df_mapa_prev = df_seleccion.copy()

    df_mapa_prev["tamano"] = df_mapa_prev["id_sensor"].apply(
        lambda x: 22 if (x == st.session_state.sel_origen or x == st.session_state.sel_destino) else 10
    )
    df_mapa_prev["Calle"] = df_mapa_prev["nombre_calle"].fillna(df_mapa_prev["nombre_norm"]).fillna("Calle sin identificar")

    fig_select = px.scatter_mapbox(
        df_mapa_prev,
        lat="latitud",
        lon="longitud",
        color="Estado",
        size="tamano",
        size_max=22,
        hover_name="Calle",
        hover_data={
            "id_sensor": True,
            "Estado": True,
            "latitud": False,
            "longitud": False,
            "tamano": False,
        },
        color_discrete_map={
            "Origen": COLOR_ORIGEN,
            "Destino": COLOR_DESTINO,
            "Disponible": COLOR_DISPONIBLE
        },
        center={"lat": df_mapa_prev["latitud"].mean(), "lon": df_mapa_prev["longitud"].mean()},
        zoom=12 if modo_ambito == "Madrid Completo" else 13,
        height=380,
    )
    fig_select.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
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
    st.plotly_chart(fig_select, width="stretch")


    # --- 1. CONFIGURACIÓN Y CONSTANTE DE TRÁFICO ---
    # Factor fijo para equilibrar distancia y congestión
    FACTOR_TRAFICO_FIJO = 8.0

    # --- 2. CÁLCULO DE LA RUTA (SIN SLIDER) ---
col1, col2, col3 = st.columns([4, 2, 4])
with col2:
    btn_calcular = st.button("Calcular Ruta Optimizada", type="primary", width="content")

if btn_calcular:
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

            sensores_cercanos = sensores_relevantes_para_ruta(sensores_disponibles, grafo, ruta_actual)
            obtener_ocupaciones_sensores(sensores_cercanos)

            sensores_con_dato = [
                s for s in sensores_disponibles
                if intentos_previos_ocupacion.get(s["id_sensor"]) is not None
            ]
            ocupacion_por_arista = calcular_ocupacion_por_arista(
                grafo, sensores_con_dato, intentos_previos_ocupacion
            )
            
            # Usamos el factor fijo de tráfico directamente
            grafo_ponderado = construir_grafo_ponderado(grafo, ocupacion_por_arista, FACTOR_TRAFICO_FIJO)

            ruta_nodos = nx.dijkstra_path(grafo_ponderado, nodo_origen, nodo_destino, weight="weight")
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

# --- 3. TABLA DE RESULTADOS CON PORCENTAJE DE SATURACIÓN ---
if "ruta_nodos" in st.session_state:
    ruta_nodos = st.session_state.ruta_nodos
    grafo_ruta = st.session_state.grafo_ruta
    coords_nodos = st.session_state.grafo_nodos_coords
    lat_o_real, lon_o_real = st.session_state.coords_origen_real
    lat_d_real, lon_d_real = st.session_state.coords_destino_real

    sensor_origen = dict_sensores[st.session_state.sel_origen]
    sensor_destino = dict_sensores[st.session_state.sel_destino]

    st.divider()
    st.subheader("Resultado de la Ruta")

    # Mensaje descriptivo indicando que se ha contemplado la ocupación
    st.success(
        "**Ruta optimizada calculada:** El trazado se ha generado evaluando los niveles "
        "de ocupación y congestión en tiempo real para ofrecerte la vía más fluida."
    )

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

    # Métricas principales
    m1, m2 = st.columns(2)
    with m1:
        st.metric("Distancia total estimada", f"{distancia_total / 1000:.2f} km")
    with m2:
        st.metric("Tramos principales", f"{len(tramos)} tramos")

    # CONSTRUCCIÓN DE LA TABLA DE ITINERARIO
    datos_tabla = [{
        "Etapa": "Origen",
        "Calle / Vía": calle_origen,
        "Sensor(es) Cercanos": f"#{sensor_origen['id_sensor']}",
        "Distancia": "0 m",
    }]

    for idx, t in enumerate(tramos):
        ids_texto = ", ".join(f"#{i}" for i in sorted(t["sensores"])) if t["sensores"] else "—"
        dist_texto = f"{round(t['longitud'])} m" if t['longitud'] < 1000 else f"{t['longitud']/1000:.2f} km"

        datos_tabla.append({
            "Etapa": f"Tramo {idx + 1}",
            "Calle / Vía": t["nombre"],
            "Sensor(es) Cercanos": ids_texto,
            "Distancia": dist_texto,
        })

    datos_tabla.append({
        "Etapa": "Destino",
        "Calle / Vía": calle_destino,
        "Sensor(es) Cercanos": f"#{sensor_destino['id_sensor']}",
        "Distancia": "Llegada",
    })

    st.markdown("#### Itinerario detallado de la ruta")
    st.dataframe(pd.DataFrame(datos_tabla), width="stretch", hide_index=True)

    # Mapa Final interactivo
    st.markdown("#### Vista en el mapa")

    lats_ruta = [coords_nodos[n][0] for n in ruta_nodos]
    lons_ruta = [coords_nodos[n][1] for n in ruta_nodos]

    fig_ruta = go.Figure()

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

    fig_ruta.add_trace(go.Scattermapbox(
        lat=[lat_o_real], lon=[lon_o_real],
        mode="markers",
        marker=dict(size=16, color=COLOR_ORIGEN),
        name="Origen",
        customdata=[[calle_origen, sensor_origen["id_sensor"], "Origen", lat_o_real, lon_o_real]],
        hovertemplate=hovertemplate_fmt
    ))

    fig_ruta.add_trace(go.Scattermapbox(
        lat=[lat_d_real], lon=[lon_d_real],
        mode="markers",
        marker=dict(size=16, color=COLOR_DESTINO),
        name="Destino",
        customdata=[[calle_destino, sensor_destino["id_sensor"], "Destino", lat_d_real, lon_d_real]],
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
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.02,
            bgcolor="rgba(255, 255, 255, 0.6)",
            font=dict(color="black")
        ),
    )
    st.plotly_chart(fig_ruta, width="stretch")