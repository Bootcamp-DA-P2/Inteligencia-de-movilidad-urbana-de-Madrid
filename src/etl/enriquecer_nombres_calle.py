import duckdb
import requests
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "database" / "trafico.duckdb"

def obtener_calle(lat: float, lon: float) -> str | None:
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 17},
            headers={"User-Agent": "madflow-tfg/1.0 (tu_email@ejemplo.com)"},  # obligatorio en su política de uso
            timeout=10,
        )
        data = resp.json()
        return data.get("address", {}).get("road")
    except Exception:
        return None

def main():
    con = duckdb.connect(str(DB_PATH))

    # crea la columna si no existe
    con.execute("ALTER TABLE dim_sensor ADD COLUMN IF NOT EXISTS nombre_calle VARCHAR")

    sensores = con.execute(
        "SELECT id_sensor, latitud, longitud FROM dim_sensor WHERE nombre_calle IS NULL"
    ).fetchall()

    print(f"Sensores a procesar: {len(sensores)}")

    for id_sensor, lat, lon in sensores:
        calle = obtener_calle(lat, lon)
        con.execute(
            "UPDATE dim_sensor SET nombre_calle = ? WHERE id_sensor = ?",
            [calle, id_sensor]
        )
        print(id_sensor, "->", calle)
        time.sleep(1.1)  # respeta el límite de 1 req/seg de Nominatim

    con.close()

if __name__ == "__main__":
    main()