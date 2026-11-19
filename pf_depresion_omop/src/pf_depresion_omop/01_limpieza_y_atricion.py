from pathlib import Path

import polars as pl

RUTA_DEFECTO = Path("data/Egresos_Sectorial_2024.txt")


def limpiar_cohorte(lf: pl.LazyFrame) -> tuple[pl.DataFrame, dict[str, int | float]]:
    """Aplica los criterios de inclusión y calidad sobre los egresos hospitalarios."""
    total_egresos = lf.select(pl.len()).collect().item()

    # 1. Filtro de Cohorte (F32/F33)
    df_cohorte = lf.filter(
        pl.col("AFECPRIN3").str.starts_with("F32") | pl.col("AFECPRIN3").str.starts_with("F33")
    ).collect()
    total_cohorte = df_cohorte.height

    # 2. Filtro de edad
    df_edad = df_cohorte.filter(
        (pl.col("CLAVE_EDAD") != 9)
        & (pl.col("EDAD1").is_not_null())
        & (pl.col("EDAD1") >= 0)
        & (pl.col("EDAD1") < 120)
    )
    total_edad = df_edad.height

    # 3. Filtro de fechas y sexo
    df_limpio = df_edad.filter(
        (pl.col("MES") >= 1) & (pl.col("MES") <= 12) & (pl.col("SEXO").is_in([1, 2]))
    )
    total_limpio = df_limpio.height

    retencion = round((total_limpio / total_cohorte) * 100, 2) if total_cohorte > 0 else 0.0

    metricas = {
        "total_egresos": total_egresos,
        "total_cohorte": total_cohorte,
        "excluidos_cohorte": total_egresos - total_cohorte,
        "total_edad": total_edad,
        "excluidos_edad": total_cohorte - total_edad,
        "total_limpio": total_limpio,
        "excluidos_limpio": total_edad - total_limpio,
        "retencion_porcentaje": retencion,
    }
    return df_limpio, metricas


def generar_tabla_atricion_md(metricas: dict[str, int | float]) -> str:
    """Construye el reporte Markdown con el conteo de atrición."""
    return (
        "Tabla de atrición\n"
        "| Paso | Criterio de inclusión/exclusión | N (Retenidos) | Excluidos en este paso |\n"
        f"| 1 | Total de egresos DGIS 2024 | {metricas['total_egresos']:,} | 0 |\n"
        f"| 2 | Filtro diagnóstico: Inclusión códigos F32 y F33 | "
        f"{metricas['total_cohorte']:,} | - {metricas['excluidos_cohorte']:,} |\n"
        f"| 3 | Filtro de calidad (edad): CLAVE_EDAD válida y EDAD1 < 120 | "
        f"{metricas['total_edad']:,} | - {metricas['excluidos_edad']:,} |\n"
        f"| 4 | Filtro de calidad (fechas y sexo): MES (1-12) y SEXO (1, 2) | "
        f"{metricas['total_limpio']:,} | - {metricas['excluidos_limpio']:,} |\n"
        f"| Final | Cohorte para mapeo OMOP | {metricas['total_limpio']:,} | "
        f"Retención: {metricas['retencion_porcentaje']}% |\n"
    )


def main(
    ruta_archivo: Path | str = RUTA_DEFECTO, ruta_salida_md: Path | str = "docs/atricion_cohorte.md"
) -> pl.DataFrame:
    lf = pl.scan_csv(ruta_archivo, separator="|", ignore_errors=True, infer_schema_length=1000)
    df_limpio, metricas = limpiar_cohorte(lf)

    contenido_md = generar_tabla_atricion_md(metricas)
    print(contenido_md)

    Path(ruta_salida_md).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta_salida_md).write_text(contenido_md, encoding="utf-8")
    return df_limpio


if __name__ == "__main__":
    main()
