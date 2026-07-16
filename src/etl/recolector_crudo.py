import requests
import xml.etree.ElementTree as ET
import duckdb
import pandas as pd
from pathlib import Path

URL = "https://datos.madrid.es/dataset/202087-0-trafico-intensidad/resource/202087-0-trafico-intensidad/download/202087-0-trafico-intensidad.xml"
DB_PATH = Path("database/trafico.duckdb")

def consultar_y_guardar_crudo():
    respuesta = requests.get(URL)
    respuesta.raise_for_status()
    root = ET.fromstring(respuesta.content)

    fecha_hora_elem = root.find('.//fecha_hora')
    fecha = pd.to_datetime(fecha_hora_elem.text, format="%d/%m/%Y %H:%M:%S")

    registros = []
    for pm in root.findall('.//pm'):
        def get_val(tag):
            e = pm.find(tag)
            return e.text if e is not None else None

        velocidad_raw = get_val('velocidad')  # solo existe en interurbanos

        registros.append({
            "id_sensor": int(get_val('idelem')),
            "fecha": fecha,
            "intensidad": float(get_val('intensidad') or 0),
            "ocupacion": float(get_val('ocupacion') or 0),
            "carga": float(get_val('carga') or 0),
            "velocidad_media": float(velocidad_raw) if velocidad_raw is not None else None,
            "error": get_val('error'),
        })

    df = pd.DataFrame(registros)

    con = duckdb.connect(str(DB_PATH))
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw_live (
            id_sensor INTEGER, fecha TIMESTAMP, intensidad DOUBLE,
            ocupacion DOUBLE, carga DOUBLE, velocidad_media DOUBLE, error VARCHAR
        )
    """)

    filas_antes = con.execute("SELECT COUNT(*) FROM raw_live").fetchone()[0]

    con.execute("""
        INSERT INTO raw_live
        SELECT df.* FROM df
        WHERE NOT EXISTS (
            SELECT 1 FROM raw_live r
            WHERE r.id_sensor = df.id_sensor AND r.fecha = df.fecha
        )
    """)
    
    filas_despues = con.execute("SELECT COUNT(*) FROM raw_live").fetchone()[0]
    con.close()
    print(f"Insertados {filas_despues - filas_antes} registros nuevos de {len(df)} recibidos ({fecha})")

if __name__ == "__main__":
    consultar_y_guardar_crudo()