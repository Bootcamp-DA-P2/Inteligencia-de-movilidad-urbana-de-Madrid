# MadFlow: Análisis de Movilidad Urbana en Madrid

## Descripción

**MadFlow** es una plataforma integral de análisis de movilidad urbana centrada en la congestión del tráfico en la ciudad de Madrid. El proyecto utiliza datos provenientes de sensores de tráfico del Ayuntamiento de Madrid para visualizar, analizar y modelar los patrones de flujo, ocupación y velocidad en las vías urbanas y en la M-30.

El repositorio incluye un **dashboard interactivo** (desarrollado en Power BI para el análisis ejecutivo) y una **aplicación web** (desarrollada en Streamlit) que permite la exploración de datos modelados con un sistema de control de acceso (login).

## Características Principales
* **Análisis de Congestión:** Evaluación granular de intensidad, velocidad y ocupación de la vía por distrito, hora y tipo de sensor.
* **Dashboard Interactivo:** Visualizaciones detalladas en Power BI con mapas georreferenciados y segmentación temporal.
* **Aplicación Streamlit:** Interfaz web para consultar datos procesados con un sistema de autenticación de usuarios.
* **Procesamiento de Datos:** Pipeline robusto utilizando **DuckDB** y **Polars** para la transformación y consolidación de grandes volúmenes de datos en formato Parquet, optimizando el rendimiento.

## Tecnologías Utilizadas
* **Lenguaje:** Python 3.12+
* **Procesamiento de Datos:** Polars, DuckDB, Pandas
* **Visualización:** Power BI
* **Web Framework:** Streamlit
* **Formato de Almacenamiento:** Apache Parquet

## Resultados Destacados
* **Dataset:** Análisis basado en una muestra representativa de 5,088 sensores.
* **Calidad:** 99.4% de calidad media en los datos procesados.
* **Insights:** Identificación de patrones de tráfico laboral (lunes-viernes) frente al fin de semana, con picos vespertinos sostenidos entre las 14:00h y las 20:00h en distritos clave como Retiro, Salamanca y Arganzuela.

## Arquitectura del Proyecto

```text
├── data/
│   ├── raw/             # Archivos CSV originales de datos.madrid.es
│   ├── gold/            # Datos transformados (parquet) listos para análisis
│   └── modeling/        # Base final para el modelo y la app
├── notebooks/           # Scripts de limpieza y transformación (Python)
├── src/
│   └── app/             # Aplicación Streamlit (sistema de login)
├── reports/             # Informe ejecutivo en Power BI (.pbix)
├── README.md
└── requirements.txt


