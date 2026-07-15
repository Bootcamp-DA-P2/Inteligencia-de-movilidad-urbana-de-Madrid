import requests
import xml.etree.ElementTree as ET
import time
import sys

# Forzamos que la salida se vea al instante
sys.stdout.reconfigure(line_buffering=True)

URL = "https://datos.madrid.es/dataset/202087-0-trafico-intensidad/resource/202087-0-trafico-intensidad/download/202087-0-trafico-intensidad.xml"

def consultar_datos():
    print(f"\n--- Consultando datos a las {time.strftime('%H:%M:%S')} ---")
    try:
        respuesta = requests.get(URL)
        respuesta.raise_for_status() 
        
        root = ET.fromstring(respuesta.content)
        contador = 0
        
        for pm in root.findall('.//pm'):
            # Función auxiliar para obtener texto de forma segura
            def get_val(tag):
                elem = pm.find(tag)
                return elem.text if elem is not None else "N/A"
            
            # Obtenemos los nuevos campos
            idelem = get_val('idelem')
            descripcion = get_val('descripcion')
            intensidad = get_val('intensidad')
            ocupacion = get_val('ocupacion')
            carga = get_val('carga')
            nivel = get_val('nivelServicio')
            
            # Imprimimos los datos estructurados
            print(f"ID: {idelem} | {descripcion}")
            print(f"   -> Intensidad: {intensidad} | Ocupación: {ocupacion}% | Carga: {carga}% | Nivel Servicio: {nivel}")
            print("-" * 50)
            
            contador += 1
            if contador >= 10:
                break
                
        print("--- Actualización finalizada. Esperando 5 minutos... ---")
        
    except Exception as e:
        print(f"Ha ocurrido un error: {e}")

while True:
    consultar_datos()
    time.sleep(300)