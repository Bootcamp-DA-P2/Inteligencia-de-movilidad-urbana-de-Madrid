import os
import base64
import streamlit as st
from streamlit_carousel import carousel

def cargar_imagen_local(ruta_imagen):
    if os.path.exists(ruta_imagen):
        ext = os.path.splitext(ruta_imagen)[1].replace(".", "")
        mime_type = "jpeg" if ext == "jpg" else ext
        
        with open(ruta_imagen, "rb") as archivo_imagen:
            contenido = archivo_imagen.read()
            codificado = base64.b64encode(contenido).decode()
            return f"data:image/{mime_type};base64,{codificado}"
    else:
        st.error(f"⚠️ No se encontró la imagen en: {ruta_imagen}")
        return ""

st.title("Inteligencia de movilidad urbana de Madrid")
st.write("Bienvenido a la aplicación de inteligencia de movilidad urbana de Madrid.")
st.write("Esta aplicación proporciona información y análisis sobre la movilidad urbana en la ciudad de Madrid, utilizando datos de transporte público, tráfico y otros factores relevantes.")
st.write("Navega por las diferentes secciones de la aplicación utilizando el menú de navegación en la parte superior.")

ruta_img1 = cargar_imagen_local("src/frontend/public/imagen1.png")
ruta_img2 = cargar_imagen_local("src/frontend/public/imagen2.png")
ruta_img3 = cargar_imagen_local("src/frontend/public/imagen3.png")
ruta_img4 = cargar_imagen_local("src/frontend/public/imagen4.png")

items_carrusel = [
    {
        "title": "Madrid 1",
        "text": "Madrid 1",
        "img": ruta_img1,
    },
    {
        "title": "Madrid 2",
        "text": "Madrid 2",
        "img": ruta_img2,
    },
    {
        "title": "Madrid 3",
        "text": "Madrid 3",
        "img": ruta_img1,
    },
    {
        "title": "Madrid 4",
        "text": "Madrid 4",
        "img": ruta_img4,
    }
]

# Renderizar el carrusel
if all([ruta_img1, ruta_img2, ruta_img3, ruta_img4]):
    carousel(items=items_carrusel, width=1.0)
else:
    st.warning("Verifica las rutas de las imágenes en la carpeta 'public'.")
