import glob
import os
import pandas as pd
from pathlib import Path

CHUNK_SIZE = 500_000

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

files = list((DATA / "historico-trafico").glob("*.csv"))

print(f"Se han encontrado {len(files)} archivos.\n")

columnas_metricas = ["intensidad", "ocupacion", "carga", "vmed"]

for num_archivo, file in enumerate(files, start=1):

    nombre = os.path.splitext(os.path.basename(file))[0]

    print("=" * 60)
    print(f"[{num_archivo}/{len(files)}] Procesando: {nombre}")

    resultados = []

    for num_chunk, chunk in enumerate(
        pd.read_csv(file, sep=";", chunksize=CHUNK_SIZE),
        start=1
    ):

        print(f"  → Chunk {num_chunk}: {len(chunk):,} filas")

        # Fecha
        chunk["fecha"] = pd.to_datetime(chunk["fecha"])

        chunk["dia"] = chunk["fecha"].dt.date
        chunk["hora"] = chunk["fecha"].dt.hour

        # Eliminar registros con errores graves
        chunk = chunk[chunk["error"] != "S"]

        # Valores negativos = ausencia de datos
        for c in columnas_metricas:
            chunk[c] = pd.to_numeric(chunk[c], errors="coerce")
            chunk.loc[chunk[c] < 0, c] = pd.NA

        chunk["periodo_integracion"] = pd.to_numeric(
            chunk["periodo_integracion"],
            errors="coerce"
        )

        # Resumen horario por día
        agrupado = (
            chunk.groupby(["id", "tipo_elem", "dia", "hora"], as_index=False)
            .agg(
                intensidad_media=("intensidad", "mean"),
                intensidad_maxima=("intensidad", "max"),

                ocupacion_media=("ocupacion", "mean"),
                ocupacion_maxima=("ocupacion", "max"),

                carga_media=("carga", "mean"),
                carga_maxima=("carga", "max"),

                vmed_media=("vmed", "mean"),

                periodo_integracion_media=("periodo_integracion", "mean"),
                periodo_integracion_min=("periodo_integracion", "min")
            )
        )

        print(f"     Resumen generado: {len(agrupado):,} filas")

        resultados.append(agrupado)

    print("  → Uniendo chunks...")

    df = pd.concat(resultados, ignore_index=True)

    print(f"     Filas tras unir: {len(df):,}")

    print("  → Calculando patrón horario del mes...")

    df_final = (
        df.groupby(["id", "tipo_elem", "hora"], as_index=False)
        .agg(
            intensidad_media=("intensidad_media", "mean"),
            intensidad_maxima=("intensidad_maxima", "max"),

            ocupacion_media=("ocupacion_media", "mean"),
            ocupacion_maxima=("ocupacion_maxima", "max"),

            carga_media=("carga_media", "mean"),
            carga_maxima=("carga_maxima", "max"),

            vmed_media=("vmed_media", "mean"),

            periodo_integracion_media=("periodo_integracion_media", "mean"),
            periodo_integracion_min=("periodo_integracion_min", "min")
        )
    )

    print(f"     Filas finales: {len(df_final):,}")

    # Redondear decimales
    columnas_decimales = [
        "intensidad_media",
        "ocupacion_media",
        "carga_media",
        "vmed_media",
        "periodo_integracion_media"
    ]

    df_final[columnas_decimales] = df_final[columnas_decimales].round(2)

    # Guardar
    salida = DATA / "historico-trafico" / f"{nombre}-resumido.csv"

    print(f"  → Guardando: {salida}")

    df_final.to_csv(
        salida,
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )

    print(f"✓ {nombre} procesado correctamente.\n")

print("=" * 60)
print("Proceso completado. Todos los archivos han sido resumidos.")