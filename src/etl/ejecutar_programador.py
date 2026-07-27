import time
import schedule
import logging
from pathlib import Path

# Importamos las funciones de tus scripts
from recolector_crudo import consultar_y_guardar_crudo
from agregador_horario import agregar_ultima_hora

# Configuración de logs
ROOT = Path(__file__).resolve().parents[2] if "src" in str(Path(__file__)) else Path(__file__).resolve().parent
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOGS_DIR / "programador_local.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def tarea_recolector():
    logging.info("Iniciando ejecución de recolector_crudo...")
    try:
        consultar_y_guardar_crudo()
        logging.info("recolector_crudo completado con éxito.")
    except Exception as e:
        logging.error(f"Error en recolector_crudo: {e}")

def tarea_agregador():
    logging.info("Iniciando ejecución de agregador_horario...")
    try:
        agregar_ultima_hora()
        logging.info("agregador_horario completado con éxito.")
    except Exception as e:
        logging.error(f"Error en agregador_horario: {e}")

# --- PROGRAMACIÓN DE TAREAS ---
# Recolector cada 5 minutos
schedule.every(5).minutes.do(tarea_recolector)

# Agregador cada hora (al minuto 05 de cada hora)
schedule.every().hour.at(":05").do(tarea_agregador)

if __name__ == "__main__":
    print("🚀 Programador local iniciado.")
    print("- Recolector: ejecutándose cada 5 minutos.")
    print("- Agregador: ejecutándose cada hora.")
    print("Presiona Ctrl + C para detener el proceso.\n")

    # Ejecución inicial al arrancar
    tarea_recolector()

    # Bucle infinito para mantener las tareas activas
    while True:
        schedule.run_pending()
        time.sleep(1)