# MadFlow: Análisis de Movilidad Urbana en Madrid

## Descripción

**MadFlow** es una plataforma integral de análisis de movilidad urbana centrada en la congestión del tráfico en la ciudad de Madrid. El proyecto utiliza datos provenientes de sensores de tráfico del Ayuntamiento de Madrid para visualizar, analizar y modelar los patrones de flujo, ocupación y velocidad en las vías urbanas y en la M-30.

El repositorio incluye un **dashboard interactivo** (desarrollado en Power BI para el análisis ejecutivo) y una **aplicación web** (desarrollada en Streamlit) que permite la exploración de datos modelados con un sistema de control de acceso (login).

## Características Principales
* **Análisis de Congestión:** Evaluación granular de intensidad, velocidad y ocupación de la vía por distrito, hora y tipo de sensor.
* **Dashboard Interactivo:** Visualizaciones detalladas en Power BI con mapas georreferenciados y segmentación temporal.
* **Aplicación Streamlit:** Interfaz web para consultar datos procesados con un sistema de autenticación de usuarios.
* **Procesamiento de Datos:** Pipeline robusto utilizando **DuckDB** y **Polars** para la transformación y consolidación de grandes volúmenes de datos en formato Parquet, optimizando el rendimiento.

##  Tecnologías y Dependencias
El proyecto hace uso de un amplio abanico de librerías especializadas en ciencia de datos, machine learning y sistemas de información geográfica. 

**Stack Principal:**
*   **Lenguaje:** `Python 3.12+`
*   **Tratamiento de Datos y ETL:** `pandas`, `polars`, `numpy`, `duckdb`, `SQLAlchemy`, `PyMySQL`.
*   **Machine Learning:** `scikit-learn`, `xgboost`, `lightgbm`.
*   **Análisis Geoespacial:** `geopandas`, `osmnx`, `shapely`, `pyproj`.
*   **Visualización de Datos:** `streamlit`, `plotly`, `seaborn`, `matplotlib`, `altair`, `pydeck`.
*   **Formato de Almacenamiento:** Apache Parquet
*   **Infraestructura y Despliegue:** Sistema contenerizado con Docker.

## Resultados Destacados
* **Dataset:** Análisis basado en una muestra representativa de 5,088 sensores.
* **Calidad:** 99.4% de calidad media en los datos procesados.
* **Insights:** Identificación de patrones de tráfico laboral (lunes-viernes) frente al fin de semana, con picos vespertinos sostenidos entre las 14:00h y las 20:00h en distritos clave como Retiro, Salamanca y Arganzuela.


## 📁 Estructura del Repositorio

El proyecto sigue una arquitectura de datos organizada y modular:

```text
├── .streamlit/               # Configuración específica de la aplicación Streamlit
├── .venv/                    # Entorno virtual de Python (local, excluido del repositorio)
├── .vscode/                  # Configuración del entorno de desarrollo
├── assets/                   # Recursos estáticos (imágenes, iconos, logos)
├── dashboard/                # Archivos del cuadro de mando interactivo (Power BI)
├── data/                     # Almacenamiento estructurado de datos
│   ├── gold/                 # Datos procesados, limpios y finales
│   ├── modeling/             # Datos específicos para el entrenamiento de algoritmos
│   └── raw/                  # Datos crudos extraídos directamente de las fuentes originales
├── database/                 # Archivos y configuraciones de la base de datos local
├── logs/                     # Registros de ejecución del sistema y pipeline ETL
├── models/                   # Modelos de Machine Learning entrenados y exportados
├── notebooks/                # Jupyter Notebooks con el EDA y pruebas de modelado
├── src/                      # Código fuente principal del proyecto
│   ├── backend/              # Lógica de negocio y conexiones a bases de datos
│   ├── etl/                  # Scripts del pipeline de Extracción, Transformación y Carga
│   └── frontend/             # Componentes visuales y de interfaz de usuario
│   └── trafico_madrid.py     # Script de ingesta continua (ETL) del XML del Ayuntamiento
├── .env                      # Variables de entorno locales (credenciales, tokens)
├── .env-example              # Plantilla de ejemplo para las variables de entorno
├── .gitignore                # Reglas de exclusión para el control de versiones
├── index.html                # Archivo de entrada web / presentación del proyecto
├── README.md                 # Documentación principal
└── requirements.txt          # Listado de dependencias y librerías del proyecto 
```

## ⚙️ Instalación y Uso Local

Para levantar este proyecto en tu entorno local, sigue estos pasos:

1. **Clona el repositorio y accede a la carpeta:**
   ```bash
   git clone [https://github.com/Bootcamp-DA-P2/Inteligencia-de-movilidad-urbana-de-Madrid.git](https://github.com/Bootcamp-DA-P2/Inteligencia-de-movilidad-urbana-de-Madrid.git)
   cd Inteligencia-de-movilidad-urbana-de-Madrid
   ```

2. **Crea y activa un entorno virtual:**
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # En Windows usa: .venv\Scripts\activate
   ```
   
3. **Instala las dependencias necesarias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura las credenciales:**
   * Duplica el archivo `.env-example` y renómbralo a `.env`, haz lo mismo con `.env.docker`.
   * Rellena las variables necesarias en su interior.

5. **Ejecuta Streamlit:**
   ```bash
   streamlit run src/frontend/main.py
   ```

### ⚙️ Despliegue con Docker

Si prefieres trabajar con contenedores y evitar configuraciones manuales del entorno, asegúrate de tener Docker instalado y ejecuta los siguientes comandos:

1. **Construye la imagen del proyecto:**
   ```bash
   docker compose build
   ```

2. **Levanta los contenedores:**
   ```bash
   docker compose up
   ```

## 🌿 Flujo de Trabajo y Ramas
El desarrollo se ha organizado de forma colaborativa mediante control de versiones activo:
* `main`: Rama de producción y versiones estables.
* `develop`: Rama principal para la integración continua de características.
* `feature/*`: Ramas secundarias para el desarrollo modular de componentes, ETL, interfaz y modelado.

## 👩‍💻 Equipo de Desarrollo
Proyecto desarrollado de forma colaborativa por el equipo MadFlow:
* **Ana Paula Montiel** 
* **Elena Suárez** 
* **Irene Condado** 
* **Jose Carlos de Santiago** 
* **Daniel Luque** 

---
*Desarrollado como proyecto pedagógico para el Bootcamp de Data Analytics.*


