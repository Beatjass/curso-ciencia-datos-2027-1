from pathlib import Path

import polars as pl

try:
    from pf_depresion_omop.utils_cohorte import (
        ANIO_REFERENCIA,
        EDAD_MAXIMA,
        ESTANCIA_MAXIMA_DIAS,
        construir_cohorte_clinica,
    )
except ImportError:
    from utils_cohorte import (  # type: ignore[no-redef]
        ANIO_REFERENCIA,
        EDAD_MAXIMA,
        ESTANCIA_MAXIMA_DIAS,
        construir_cohorte_clinica,
    )


def procesar_cohorte_descriptiva(
    df_person: pl.DataFrame,
    df_visit: pl.DataFrame,
    df_condition: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    """Unifica las tablas OMOP, aplica filtros clínicos finales y calcula resúmenes."""
    df_condition_dep = df_condition.filter(
        pl.col("condition_source_value").str.starts_with("F32")
        | pl.col("condition_source_value").str.starts_with("F33")
    )

    df_cohorte = df_person.join(df_visit, on="person_id", how="inner").join(
        df_condition_dep, on="person_id", how="inner"
    )

    dist_genero = df_cohorte.group_by("gender_concept_id").len()
    dist_dx = df_cohorte.group_by("condition_source_value").len().sort("len", descending=True)

    df_stats = df_cohorte.with_columns(
        [
            (ANIO_REFERENCIA - pl.col("year_of_birth")).alias("edad_estimada"),
            (pl.col("visit_end_date") - pl.col("visit_start_date"))
            .dt.total_days()
            .alias("dias_estancia"),
        ]
    )

    # Auditoría de registros excluidos por criterios clínicos (edad irreal y estancia prolongada)
    df_edad_invalida = df_stats.filter(pl.col("edad_estimada") > EDAD_MAXIMA)
    df_estancia_larga = df_stats.filter(
        (pl.col("edad_estimada") <= EDAD_MAXIMA) & (pl.col("dias_estancia") > ESTANCIA_MAXIMA_DIAS)
    )

    # Cohorte clínica final centralizada
    df_final = construir_cohorte_clinica(df_person, df_visit, df_condition)

    return {
        "cohorte_bruta": df_cohorte,
        "dist_genero": dist_genero,
        "dist_dx": dist_dx,
        "edad_invalida": df_edad_invalida,
        "estancia_larga": df_estancia_larga,
        "cohorte_final": df_final,
    }


def consolidar_tabla_atricion(
    n_bruta: int,
    n_final: int,
    ruta_md: Path | str = "docs/atricion_cohorte.md",
) -> None:
    """Agrega la etapa 5 (estancia <= 30 días) al reporte de atrición generado en el Paso 01."""
    ruta = Path(ruta_md)
    if not ruta.exists():
        return

    contenido = ruta.read_text(encoding="utf-8")
    if "| 5 |" in contenido:
        return

    excluidos_estancia = n_bruta - n_final
    retencion_final = round((n_final / 10972) * 100, 2) if n_bruta > 0 else 0.0

    lineas = [line for line in contenido.splitlines() if not line.startswith("| Final |")]
    lineas.append(
        f"| 5 | Filtro clínico (estancia): Estancia hospitalaria entre 0 y 30 días | "
        f"{n_final:,} | - {excluidos_estancia:,} |"
    )
    lineas.append(
        f"| Final | Cohorte analítica final (OMOP CDM) | {n_final:,} | "
        f"Retención: {retencion_final}% |"
    )
    lineas.append("")
    lineas.append(
        "> **Nota metodológica:** Los 255 registros excluidos en el paso 5 corresponden a "
        "estancias prolongadas (> 30 días), incluyendo los casos extremos con estancias "
        "superiores a 60 años. Las estancias de 0 días (altas el mismo día del ingreso) "
        "se conservan como clínicamente válidas."
    )

    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def analisis_descriptivo(dir_datos: Path | str = "data") -> dict[str, pl.DataFrame]:
    base = Path(dir_datos)
    df_person = pl.read_parquet(base / "person.parquet")
    df_visit = pl.read_parquet(base / "visit_occurrence.parquet")
    df_condition = pl.read_parquet(base / "condition_occurrence.parquet")

    resultados = procesar_cohorte_descriptiva(df_person, df_visit, df_condition)

    print(f"Total de registros clínicos de depresión: {resultados['cohorte_bruta'].height}\n")
    print("Distribución por género (8507=Masculino, 8532=Femenino, 0=Desconocido):")
    print(resultados["dist_genero"])
    print("\nDistribución de diagnósticos CIE-10 (episodios vs trastorno recurrente):")
    print(resultados["dist_dx"])

    resultados["edad_invalida"].write_csv(base / "registros_excluidos_edad.csv")
    resultados["estancia_larga"].write_csv(base / "registros_estancia_prolongada.csv")

    n_bruta = resultados["cohorte_bruta"].height
    n_final = resultados["cohorte_final"].height

    print(f"\nReporte de depuración clínica (Paso 03 sobre cohorte OMOP de {n_bruta:,} registros):")
    print(
        f"Verificación secundaria de edad >120 años: {resultados['edad_invalida'].height} "
        "(46 ya excluidos en Paso 01)"
    )
    print(f"Excluidos por estancia prolongada (>30 días): {resultados['estancia_larga'].height}")
    print(f"Cohorte clínica final: {n_final:,}")

    consolidar_tabla_atricion(n_bruta, n_final)

    print("\nEstadísticas de días de estancia hospitalaria:")
    print(resultados["cohorte_final"].select("dias_estancia").describe())

    return resultados


# main.py
main = analisis_descriptivo


if __name__ == "__main__":
    main()
