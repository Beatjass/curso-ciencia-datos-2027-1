from pathlib import Path

import polars as pl


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
            (2024 - pl.col("year_of_birth")).alias("edad_estimada"),
            (pl.col("visit_end_date") - pl.col("visit_start_date"))
            .dt.total_days()
            .alias("dias_estancia"),
        ]
    )

    # Filtro 1: edad irreal (<= 120 años)
    df_edad_invalida = df_stats.filter(pl.col("edad_estimada") > 120)
    df_edad_ok = df_stats.filter(pl.col("edad_estimada") <= 120)

    # Filtro 2: estancia clínica (<= 30 días)
    df_estancia_larga = df_edad_ok.filter(pl.col("dias_estancia") > 30)
    df_final = df_edad_ok.filter((pl.col("dias_estancia") >= 0) & (pl.col("dias_estancia") <= 30))

    return {
        "cohorte_bruta": df_cohorte,
        "dist_genero": dist_genero,
        "dist_dx": dist_dx,
        "edad_invalida": df_edad_invalida,
        "estancia_larga": df_estancia_larga,
        "cohorte_final": df_final,
    }


def analisis_descriptivo(dir_datos: Path | str = "data") -> dict[str, pl.DataFrame]:
    base = Path(dir_datos)
    df_person = pl.read_parquet(base / "person.parquet")
    df_visit = pl.read_parquet(base / "visit_occurrence.parquet")
    df_condition = pl.read_parquet(base / "condition_occurrence.parquet")

    resultados = procesar_cohorte_descriptiva(df_person, df_visit, df_condition)

    print(f"Total de registros clínicos de depresión: {resultados['cohorte_bruta'].height}\n")
    print("Distribución por género (8507=Masculino, 8532=Femenino, 0=Desconocido):")
    print(resultados["dist_genero"])
    print("\nDistribución de diagnósticos CIE-10 (Episodios vs Trastorno Recurrente):")
    print(resultados["dist_dx"])

    resultados["edad_invalida"].write_csv(base / "registros_excluidos_edad.csv")
    resultados["estancia_larga"].write_csv(base / "registros_estancia_prolongada.csv")

    print("\nReporte de atrición final:")
    print(f"Excluidos por edad irreal: {resultados['edad_invalida'].height}")
    print(f"Excluidos por cuidado residencial (>30 días): {resultados['estancia_larga'].height}")
    print(f"Cohorte clínica final: {resultados['cohorte_final'].height}")

    print("\nEstadísticas de días de estancia hospitalaria:")
    print(resultados["cohorte_final"].select("dias_estancia").describe())

    return resultados


# main.py
main = analisis_descriptivo


if __name__ == "__main__":
    main()
