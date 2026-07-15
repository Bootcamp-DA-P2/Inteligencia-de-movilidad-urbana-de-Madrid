import requests
import xml.etree.ElementTree as ET
import time
import sys

# Forzamos que la salida se vea al instante
sys.stdout.reconfigure(line_buffering=True)

# URL oficial del archivo XML del Ayuntamiento de Madrid
URL = "https://datos.madrid.es/dataset/202087-0-trafico-intensidad/resource/202087-0-trafico-intensidad/download/202087-0-trafico-intensidad.xml"

def consultar_datos():
    print(f"\n--- Consultando datos a las {time.strftime('%H:%M:%S')} ---")
    try:
        # Descargamos el contenido directamente a la memoria
        respuesta = requests.get(URL)
        respuesta.raise_for_status() 
        
        # Procesamos el XML
        root = ET.fromstring(respuesta.content)
        
        # Inicializamos un contador para limitar la salida
        contador = 0
        
        # Iteramos por cada punto de medida ('pm')
        for pm in root.findall('.//pm'):
            # Obtenemos los valores de forma segura
            codigo_elem = pm.find('codigo')
            codigo = codigo_elem.text if codigo_elem is not None else "Desconocido"
            
            intensidad_elem = pm.find('intensidad')
            intensidad = intensidad_elem.text if intensidad_elem is not None else "0"
            
            velocidad_elem = pm.find('velocidad')
            velocidad = velocidad_elem.text if velocidad_elem is not None else "0"
            
            # Imprimimos los datos
            print(f"Sensor ID: {codigo} | Velocidad: {velocidad} km/h | Intensidad: {intensidad} veh/5min")
            
            # Sumamos al contador y paramos tras 10 registros
            contador += 1
            if contador >= 10:
                break
                
        print("--- Actualización finalizada. Esperando 5 minutos... ---")
        
    except Exception as e:
        print(f"Ha ocurrido un error durante la descarga o procesamiento: {e}")

# Bucle infinito que mantiene el programa vivo
while True:
    consultar_datos()
    time.sleep(300) # 300 segundos = 5 minutos