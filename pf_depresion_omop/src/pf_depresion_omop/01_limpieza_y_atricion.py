import polars as pl

ruta_archivo = (
    "/home/jassiel/Documentos/Labs/repo-principal/pf_depresion_omop/data/Egresos_Sectorial_2024.txt"
)

# 1. Total inicial
query_total = pl.scan_csv(ruta_archivo, separator="|", ignore_errors=True, infer_schema_length=1000)
# Contamos el total de egresos en la base nacional
total_egresos = query_total.select(pl.len()).collect().item()

# 2. Filtro de Cohorte (F32/F33) con collect()
df_cohorte = query_total.filter(
    pl.col("AFECPRIN3").str.starts_with("F32") | pl.col("AFECPRIN3").str.starts_with("F33")
).collect()
total_cohorte = df_cohorte.height
excluidos_cohorte = total_egresos - total_cohorte

# 3. Filtro de edad
df_edad = df_cohorte.filter(
    (pl.col("CLAVE_EDAD") != 9)  #!= 9 (No especificado)
    & (pl.col("EDAD1").is_not_null())
    & (pl.col("EDAD1") < 120)  # EDAD1 menor a 120 para evitar atípicos
)
total_edad = df_edad.height
excluidos_edad = total_cohorte - total_edad

# 4. Filtro de fechas y sexo
df_limpio = df_edad.filter(
    (pl.col("MES") >= 1)
    & (pl.col("MES") <= 12)  # Mes valido (1-12)
    & (pl.col("SEXO").is_in([1, 2]))  # Sexo valido (1 o 2)
)
total_limpio = df_limpio.height
excluidos_limpio = total_edad - total_limpio

# 5. Tabla de atrición
retencion_porcentaje = round((total_limpio / total_cohorte) * 100, 2) if total_cohorte > 0 else 0

print("Tabla de atrición")
print("| Paso | Criterio de inclusión/exclusión | N (Retenidos) | Excluidos en este paso |")
print(f"| 1 | otal de egresos DGIS 2024 | {total_egresos:,} | 0 |")
print(
    f"| 2 | Filtro diagnóstico: Inclusión códigos F32 y F33 | "
    f"{total_cohorte:,} | - {excluidos_cohorte:,} |"
)
print(
    f"| 3 | Filtro de calidad (edad): CLAVE_EDAD válida y EDAD1 < 120 | "
    f"{total_edad:,} | - {excluidos_edad:,} |"
)
print(
    f"| 4 | Filtro de calidad (fechas y sexo): MES (1-12) y SEXO (1, 2) | "
    f"{total_limpio:,} | - {excluidos_limpio:,} |"
)
print(
    f"| Final | Cohorte para mapeo OMOP | {total_limpio:,} | "
    f"Retención: {retencion_porcentaje}% |"
)

contenido_md = (
    "Tabla de atrición\n"
    "| Paso | Criterio de inclusión/exclusión | N (Retenidos) | Excluidos en este paso |\n"
    f"| 1 | Total de egresos DGIS 2024 | {total_egresos:,} | 0 |\n"
    f"| 2 | Filtro diagnóstico: Inclusión códigos F32 y F33 | "
    f"{total_cohorte:,} | - {excluidos_cohorte:,} |\n"
    f"| 3 | Filtro de calidad (edad): CLAVE_EDAD válida y EDAD1 < 120 | "
    f"{total_edad:,} | - {excluidos_edad:,} |\n"
    f"| 4 | Filtro de calidad (fechas y sexo): MES (1-12) y SEXO (1, 2) | "
    f"{total_limpio:,} | - {excluidos_limpio:,} |\n"
    f"| Final | Cohorte para mapeo OMOP | {total_limpio:,} | "
    f"Retención: {retencion_porcentaje}% |\n"
)

# Guardar tabla
with open("atricion_cohorte.md", "w", encoding="utf-8") as f:
    f.write(contenido_md)
