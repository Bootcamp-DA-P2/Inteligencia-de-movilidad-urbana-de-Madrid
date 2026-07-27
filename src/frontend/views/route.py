import math
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import osmnx as ox
import networkx as nx
from pathlib import Path
from streamlit_lottie import st_lottie
import json
from services.traffic_service import get_predictions_batch, get_sensores_distrito, get_todos_los_sensores
from theme import apply_theme, header_banner

# CONFIGURACIÓN Y TEMA
# Ajustamos la página a lo ancho para que el mapa no parezca un sello de correos
st.set_page_config(page_title="MadFlow - Ruta Inteligente", layout="wide")
apply_theme()
header_banner("MadFlow: Ruta Optimizada", "Mejor recorrido según la ocupación")

# TARJETA EXPLICATIVA CABECERA
with st.container(border=True):
    st.markdown("### Planificador de Ruta Inteligente")
    st.markdown("""
Calcula el mejor recorrido entre dos puntos evitando los tramos con mayor congestión en tiempo real.

MadFlow analiza la red vial y combina datos de ocupación de sensores cercanos para sugerir la trayectoria óptima.
""")

# Mapeo hardcodeado de distritos para no tener que pedirlo a la base de datos a cada rato
DISTRITOS = {
    1: "Centro", 2: "Arganzuela", 3: "Retiro", 4: "Salamanca", 5: "Chamartín",
    6: "Tetuán", 7: "Chamberí", 8: "Fuencarral-El Pardo", 9: "Moncloa-Aravaca",
    10: "Latina", 11: "Carabanchel", 12: "Usera", 13: "Puente de Vallecas",
    14: "Moratalaz", 15: "Ciudad Lineal", 16: "Hortaleza", 17: "Villaverde",
    18: "Villa de Vallecas", 19: "Vicálvaro", 20: "San Blas-Canillejas",
    21: "Barajas",
}

# Constantes visuales de color
COLOR_ORIGEN = "#EF4444"      
COLOR_DESTINO = "#10B981"     
COLOR_DISPONIBLE = "#93C5FD"  
COLOR_RUTA = "#1D4ED8"        

# FUNCIONES AUXILIARES Y CÁLCULOS
def distancia_metros(lat1, lon1, lat2, lon2) -> float:
    """Distancia en metros entre dos puntos usando Haversine."""
    R = 6371000 # Radio de la Tierra en metros (aprox)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


@st.cache_data(ttl=1800, show_spinner=False)
def cargar_todos_los_sensores():
    """ Cacheamos esto 30 min (ttl=1800) porque si no Streamlit reejecuta todo el script
        al pulsar cualquier botón y la app se siente super lenta.
        Antes hacíamos 21 peticiones seguidas al backend (una por distrito) y petaba.
        Ahora llamamos a un solo endpoint global y listo. """
    try:
        resp = get_todos_los_sensores()
        if resp.status_code == 200:
            return resp.json().get("sensores", [])
    except Exception:
        # Si la API falla, devolvemos lista vacía para que no explote la interfaz
        pass
    return []


def cargar_grafo_calles(north: float, south: float, east: float, west: float):
    """Descarga/Construye las calles de OpenStreetMap en el rectángulo delimitado.    
    OSMnx hace la magia de bajarse los nodos y tramos de carretera.
    """
    return ox.graph_from_bbox(
        bbox=(west, south, east, north),
        network_type="drive",
        simplify=True,
    )


def calcular_bbox_corredor(lat1, lon1, lat2, lon2, factor_margen=0.4, margen_minimo_m=500):
    """Calcula un rectángulo alrededor del origen y destino para no bajarnos TODO el mapa de España.
       Un poco de margen a los lados por si el camino óptimo da un pequeño rodeo.
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


def obtener_ocupaciones_sensores(sensores: list[dict]) -> dict[int, float | None]:
    """Obtiene de golpe las ocupaciones de los sensores disponibles usando caché de sesión.
       Pide predicciones en batch para ahorrar requests HTTP.
    """
    ocupaciones = {}
    if not sensores:
        return ocupaciones

    # Guardamos en st.session_state las predicciones que ya pedimos en esta sesión para no re-pedirlas
    cache_sesion = st.session_state.setdefault("cache_predicciones_sensores", {})
    ids_buscar = []

    for s in sensores:
        id_s = s["id_sensor"]
        if id_s in cache_sesion:
            ocupaciones[id_s] = cache_sesion[id_s]
        else:
            ids_buscar.append(int(id_s))

    # Si hay sensores nuevos sin predecir, lanzamos la petición en lote
    if ids_buscar:
        try:
            resp = get_predictions_batch(ids_buscar)
            if resp.status_code == 200:
                data = resp.json()
                preds = data.get("predicciones", {}) if isinstance(data, dict) else {}
                for id_s in ids_buscar:
                    # La API a veces responde con llaves int y a veces str, cubrimos ambos casos por si acaso
                    item = preds.get(id_s) or preds.get(str(id_s))
                    valor = item.get("prediccion_ocupacion") if isinstance(item, dict) else item
                    
                    # Cliclo de parseo seguro a float
                    try:
                        valor_float = float(valor) if valor is not None else None
                    except (ValueError, TypeError):
                        valor_float = None

                    ocupaciones[id_s] = valor_float
                    cache_sesion[id_s] = valor_float
        except Exception:
            # Si el servidor de predicciones tira 500, rellenamos con None y tiramos de fallback
            for id_s in ids_buscar:
                ocupaciones[id_s] = None

    return ocupaciones


def calcular_ocupacion_por_arista(grafo, sensores: list[dict], ocupaciones: dict[int, float | None]) -> dict:
    """Asigna a CADA tramo del callejero el sensor y ocupación más cercanos sin dejar ninguno vacío.
        ATENCIÓN: Vectorización extrema con NumPy.
    Calcula distancias masivas entre todos los puntos medios de las calles y todos los sensores.
    """
    sensores_validos = [
        s for s in sensores
        if s.get("latitud") is not None 
        and s.get("longitud") is not None
        and ocupaciones.get(s["id_sensor"]) is not None
    ]
    
    # Si no hay sensores con predicción directa, usamos valores base
    if not sensores_validos:
        sensores_validos = [
            s for s in sensores 
            if s.get("latitud") is not None and s.get("longitud") is not None
        ]

    if not sensores_validos:
        return {}

    # Pasamos las coordenadas a radianes para los arrays de NumPy
    lat_s = np.radians(np.array([float(s["latitud"]) for s in sensores_validos]))
    lon_s = np.radians(np.array([float(s["longitud"]) for s in sensores_validos]))
    # Fallback por defecto a 15.0% de ocupación si viene None
    ocup_s = np.array([ocupaciones.get(s["id_sensor"], 15.0) or 15.0 for s in sensores_validos])
    id_s_arr = np.array([s["id_sensor"] for s in sensores_validos])

    # Sacamos el punto medio (lat, lon) de cada calle/tramo del grafo
    pares = list(dict.fromkeys(grafo.edges()))
    lat_mid = np.radians(np.array([(grafo.nodes[u]["y"] + grafo.nodes[v]["y"]) / 2 for u, v in pares]))
    lon_mid = np.radians(np.array([(grafo.nodes[u]["x"] + grafo.nodes[v]["x"]) / 2 for u, v in pares]))

    # Matriz de distancias (Calles x Sensores)
    R = 6371000
    dlat = lat_s[None, :] - lat_mid[:, None]
    dlon = lon_s[None, :] - lon_mid[:, None]
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat_mid[:, None]) * np.cos(lat_s[None, :]) * np.sin(dlon / 2) ** 2
    )
    distancias = 2 * R * np.arcsin(np.sqrt(a))

    # Para cada calle, sacamos el índice del sensor con la distancia mínima
    idx_min = np.argmin(distancias, axis=1)
    return {
        par: {"ocupacion": float(ocup_s[idx_min[i]]), "id_sensor": int(id_s_arr[idx_min[i]])}
        for i, par in enumerate(pares)
    }


def sensores_relevantes_para_ruta(sensores: list[dict], grafo, ruta_nodos: list, radio_m: float = 350) -> list[dict]:
    """Filtra solo los sensores que están a menos de X metros de los nodos del camino inicial."""
    sensores_validos = [
        s for s in sensores
        if s.get("latitud") is not None and s.get("longitud") is not None
    ]
    if not sensores_validos or not ruta_nodos:
        return []

    lat_s = np.radians(np.array([float(s["latitud"]) for s in sensores_validos]))
    lon_s = np.radians(np.array([float(s["longitud"]) for s in sensores_validos]))

    lat_r = np.radians(np.array([grafo.nodes[n]["y"] for n in ruta_nodos]))
    lon_r = np.radians(np.array([grafo.nodes[n]["x"] for n in ruta_nodos]))

    R = 6371000
    dlat = lat_r[None, :] - lat_s[:, None]
    dlon = lon_r[None, :] - lon_s[:, None]
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat_s[:, None]) * np.cos(lat_r[None, :]) * np.sin(dlon / 2) ** 2
    )
    distancias = 2 * R * np.arcsin(np.sqrt(a))

    # Booleano: ¿está a menos de radio_m (350m por defecto) de algún punto del camino?
    dentro_del_radio = distancias.min(axis=1) <= radio_m
    return [s for s, ok in zip(sensores_validos, dentro_del_radio) if ok]


def construir_grafo_ponderado(grafo, ocupacion_por_arista: dict, FACTOR_TRAFICO_FIJO: float) -> nx.DiGraph:
    """Crea un nuevo grafo recalculando el peso (weight) de cada calle según su nivel de tráfico.
       Fórmula de penalización: peso = longitud * (1 + (ocupacion / 100) * factor)
       A más atasco, más "larga" le parece la calle a Dijkstra para que intente esquivarla.
    """
    grafo_ponderado = nx.DiGraph()
    grafo_ponderado.add_nodes_from(grafo.nodes(data=True))

    for u, v, datos in grafo.edges(data=True):
        longitud_tramo = datos.get("length", 1.0)
        info_tramo = ocupacion_por_arista.get((u, v))
        ocupacion_tramo = info_tramo["ocupacion"] if info_tramo else None
        id_sensor_tramo = info_tramo["id_sensor"] if info_tramo else None

        # Le aplicamos el castigo de tiempo por congestión
        peso = longitud_tramo * (1 + ((ocupacion_tramo or 0.0) / 100) * FACTOR_TRAFICO_FIJO)

        nombre_calle = datos.get("name", "Calle sin nombre")
        if isinstance(nombre_calle, list):
            nombre_calle = nombre_calle[0] # A veces OSM devuelves varias etiquetas en una lista

        # Si hay conexiones duplicadas entre nodos, nos quedamos con el tramo de menor peso
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

# BÚSQUEDA AUTOMÁTICA DE ASSETS (Imágenes, Lotties, etc.)
def find_assets_dir() -> Path:
    """Busca la carpeta 'assets' subiendo por los directorios padres.    
       Util para que no falle el path si lanzamos streamlit desde distintas carpetas.
    """
    current = Path(__file__).resolve().parent

    for _ in range(5):
        candidate = current / "assets"
        if candidate.is_dir():
            return candidate
        current = current.parent

    return Path(__file__).resolve().parent


ASSETS_DIR = find_assets_dir()

def cargar_lottie(relative_path: str):
    """Carga un archivo JSON de animación Lottie desde assets/."""

    try:
        clean_path = relative_path.replace("assets/", "")
        full_path = ASSETS_DIR / clean_path

        if full_path.is_file():
            with open(full_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print(f"Animación no encontrada en: {full_path}")

    except Exception as e:
        print(f"Error cargando {relative_path}: {e}")

    return None

# Cargamos el icono animado del mapa
lottie_gps = cargar_lottie("assets/gps_map.json")


# SELECCIÓN DE ÁMBITO Y CONFIGURACIÓN EN LA INTERFAZ
st.subheader("Configura tu trayecto")
st.caption("Selecciona el ámbito de búsqueda y establece los puntos de origen y destino.")

modo_ambito = st.radio(
    "Área de búsqueda",
    options=["Madrid Completo", "Por Distrito"],
    horizontal=True,
    key="modo_ambito_radio"
)

sensores_disponibles = []

# Lógica del selector de modo
if modo_ambito == "Por Distrito":
    id_distrito = st.selectbox(
        "Distrito",
        options=list(DISTRITOS.keys()),
        format_func=lambda x: f"{x} - {DISTRITOS[x]}",
        key="ruta_distrito_selectbox"
    )
    # Limpiamos el estado si el usuario cambia de distrito para evitar inconsistencias de IDs
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

    # Valores por defecto para origen y destino si no existen en el estado
    if st.session_state.get("sel_origen") not in dict_sensores:
        st.session_state.sel_origen = sensores_disponibles[0]["id_sensor"]
    if st.session_state.get("sel_destino") not in dict_sensores:
        st.session_state.sel_destino = sensores_disponibles[min(1, len(sensores_disponibles)-1)]["id_sensor"]

    # DESPLEGABLES LIMPIOS EN DOS COLUMNAS
    col1, col2 = st.columns([3, 3])

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
        # Filtramos para no dejar seleccionar la misma calle como origen y destino a la vez
        opciones_dest = [ids for ids in dict_sensores.keys() if ids != st.session_state.sel_origen]
        sensor_destino_id = st.selectbox(
            "Punto de Destino",
            options=opciones_dest,
            format_func=lambda x: nombres_desplegable.get(x, f"Sensor #{x}"),
            key="sel_destino"
        )

    # MAPA BASE DE PREVISUALIZACIÓN DE PUNTOS
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

    # Si es Madrid completo solo mostramos los pines de Origen y Destino para no petar la GPU del navegador
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

    # Render del mapa interactivo con Plotly Express
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

    st.divider()

    st.subheader("Cálculo de ruta")

    # CONFIGURACIÓN Y CONSTANTE DE PENALIZACIÓN POR TRÁFICO
    FACTOR_TRAFICO_FIJO = 8.0 # Multiplicador para castigar tramos congestionados en el algoritmo

    # CÁLCULO DE LA RUTA
    st.write("")

    col_r1, col_espacio, col_r2 = st.columns([2, 5, 2])

    with col_r1:
        btn_calcular = st.button("Calcular Ruta", type="primary", use_container_width=True)

    with col_r2:
        # Botón para resetear todo el estado de la búsqueda
        if st.button("Limpiar búsqueda", type="secondary", use_container_width=True):
            st.session_state.pop("ruta_nodos", None)
            st.session_state.pop("grafo_ruta", None)
            st.session_state.pop("grafo_nodos_coords", None)
            st.session_state.pop("coords_origen_real", None)
            st.session_state.pop("coords_destino_real", None)
            st.session_state.pop("ruta_sin_camino", None)
            st.rerun()
        

    if btn_calcular:
        sensor_origen = dict_sensores[st.session_state.sel_origen]
        sensor_destino = dict_sensores[st.session_state.sel_destino]

        lat_o, lon_o = float(sensor_origen["latitud"]), float(sensor_origen["longitud"])
        lat_d, lon_d = float(sensor_destino["latitud"]), float(sensor_destino["longitud"])

        ruta_nodos = None
        grafo = None
        grafo_ponderado = None

        # Mostrar animación mientras se calcula el grafo
        placeholder = st.empty()

        with placeholder.container():
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                st_lottie(
                    lottie_gps,
                    height=180,
                    key="loading_route"
                )
                st.markdown(
                    "<p style='text-align:center'>Calculando la trayectoria óptima...</p>",
                    unsafe_allow_html=True                    
                )


        # Estrategia de reintentos aumentando el Bounding Box por si no encuentra camino a la primera
        for factor_margen in (0.4, 0.8, 1.5):

            north, south, east, west = calcular_bbox_corredor(
                lat_o, lon_o, lat_d, lon_d, factor_margen=factor_margen
            )

            grafo = cargar_grafo_calles(north, south, east, west)

            # Buscamos el nodo de la carretera más cercano a las coordenadas de origen/destino
            nodo_origen = ox.distance.nearest_nodes(grafo, lon_o, lat_o)
            nodo_destino = ox.distance.nearest_nodes(grafo, lon_d, lat_d)

            # Calculamos primero la ruta geográfica más corta (sin tener en cuenta tráfico)
            try:
                ruta_actual = nx.dijkstra_path(
                    grafo,
                    nodo_origen,
                    nodo_destino,
                    weight="length"
                )
            except nx.NetworkXNoPath:
                ruta_actual = None

            if ruta_actual is None:
                continue # Si no hay camino, ampliamos el BBox en el siguiente ciclo

            # Obtenemos solo los sensores pegados a esa ruta para no consultar de más
            sensores_cercanos = sensores_relevantes_para_ruta(
                sensores_disponibles,
                grafo,
                ruta_actual
            )

            # Traemos predicciones de esos sensores
            ocupaciones_dict = obtener_ocupaciones_sensores(sensores_cercanos)

            # Asignamos la ocupación predicha a cada arista del grafo
            ocupacion_por_arista = calcular_ocupacion_por_arista(
                grafo,
                sensores_disponibles,
                ocupaciones_dict
            )

            # Ponderamos los pesos de la red de carreteras con los atascos
            grafo_ponderado = construir_grafo_ponderado(
                grafo,
                ocupacion_por_arista,
                FACTOR_TRAFICO_FIJO
            )

            # Volvemos a lanzar Dijkstra pero esta vez sobre el grafo ponderado por atascos
            ruta_nodos = nx.dijkstra_path(
                grafo_ponderado,
                nodo_origen,
                nodo_destino,
                weight="weight"
            )

            break # Salimos del loop de reintentos

        # Guardamos en sesión el resultado para mantenerlo al refrescar componentes
        placeholder.empty()

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

# TABLA DE RESULTADOS E ITINERARIO
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

    # Agrupamos los nodos consecutivos para formar "Tramos por nombre de calle"
    tramos = []
    distancia_total = 0.0
    for u, v in zip(ruta_nodos[:-1], ruta_nodos[1:]):
        datos = grafo_ruta[u][v]
        nombre = datos.get("name") or "Calle sin nombre"
        longitud = datos.get("length", 0.0)
        ocupacion = datos.get("ocupacion")
        id_sensor_edge = datos.get("id_sensor")
        distancia_total += longitud

        # Si el tramo actual es la misma calle que el anterior, los agrupamos para la tabla
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

    # Métricas principales en la cabecera del resultado
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

    # MAPA FINAL INTERACTIVO CON PLOTLY GRAPH OBJECTS
    st.markdown("#### Vista en el mapa")

    lats_ruta = [coords_nodos[n][0] for n in ruta_nodos]
    lons_ruta = [coords_nodos[n][1] for n in ruta_nodos]

    fig_ruta = go.Figure()

    # Trazado azul de la linea del recorrido
    fig_ruta.add_trace(go.Scattermapbox(
        lat=[lat_o_real] + lats_ruta + [lat_d_real],
        lon=[lon_o_real] + lons_ruta + [lon_d_real],
        mode="lines",
        line=dict(width=5, color=COLOR_RUTA),
        name="Ruta calculada",
        hoverinfo="skip"
    ))

    # Formato custom del tooltip al pasar el ratón por los puntos
    hovertemplate_fmt = (
        "<b>%{customdata[0]}</b><br><br>"
        "<b>ID Sensor:</b> %{customdata[1]}<br>"
        "<b>Estado:</b> %{customdata[2]}<br>"
        "<b>Latitud:</b> %{customdata[3]:.5f}<br>"
        "<b>Longitud:</b> %{customdata[4]:.5f}<extra></extra>"
    )

    # Marcador de Origen (Rojo)
    fig_ruta.add_trace(go.Scattermapbox(
        lat=[lat_o_real], lon=[lon_o_real],
        mode="markers",
        marker=dict(size=16, color=COLOR_ORIGEN),
        name="Origen",
        customdata=[[calle_origen, sensor_origen["id_sensor"], "Origen", lat_o_real, lon_o_real]],
        hovertemplate=hovertemplate_fmt
    ))

    # Marcador de Destino (Verde)
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