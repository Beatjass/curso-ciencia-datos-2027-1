import polars as pl

# Ruta al archivo
ruta_archivo = (
    "/home/jassiel/Documentos/Labs/repo-principal/pf_depresion_omop/data/Egresos_Sectorial_2024.txt"
)

# 1. Evaluación perezosa
query = pl.scan_csv(ruta_archivo, separator="|", ignore_errors=True, infer_schema_length=1000)

# 2. Imprimir las columnas disponibles para mapear contra OMOP
columnas = query.columns
print("columnas en el dataset:", columnas)

# 3. Filtrar la cohorte (F32 y F33)
query_depresion = query.filter(
    pl.col("AFECPRIN3").str.starts_with("F32") | pl.col("AFECPRIN3").str.starts_with("F33")
)

# 4. Computar el resultado
df_cohorte = query_depresion.collect()

print(f"\nTotal de pacientes en la cohorte F32/F33: {df_cohorte.height}")
print("\nPrimeros 5 registros:")
print(df_cohorte.head(5))
