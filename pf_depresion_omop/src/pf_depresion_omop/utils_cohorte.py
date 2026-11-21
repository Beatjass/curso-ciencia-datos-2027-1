from pathlib import Path

import polars as pl

ANIO_REFERENCIA = 2024
EDAD_MAXIMA = 120
ESTANCIA_MAXIMA_DIAS = 30


def construir_cohorte_clinica(
    df_person: pl.DataFrame,
    df_visit: pl.DataFrame,
    df_condition: pl.DataFrame,
    anio_referencia: int = ANIO_REFERENCIA,
    edad_maxima: int = EDAD_MAXIMA,
    estancia_maxima: int = ESTANCIA_MAXIMA_DIAS,
) -> pl.DataFrame:
    """Une las tablas OMOP y aplica los filtros clínicos estándar de la cohorte F32/F33."""
    return (
        df_person.join(df_visit, on="person_id", how="inner")
        .join(df_condition, on="person_id", how="inner")
        .with_columns(
            [
                (anio_referencia - pl.col("year_of_birth")).alias("edad_estimada"),
                (pl.col("visit_end_date") - pl.col("visit_start_date"))
                .dt.total_days()
                .alias("dias_estancia"),
            ]
        )
        .filter(
            (
                pl.col("condition_source_value").str.starts_with("F32")
                | pl.col("condition_source_value").str.starts_with("F33")
            )
            & (pl.col("edad_estimada") <= edad_maxima)
            & (pl.col("dias_estancia") >= 0)
            & (pl.col("dias_estancia") <= estancia_maxima)
        )
    )


def cargar_cohorte_desde_parquet(dir_datos: Path | str = "data") -> pl.DataFrame:
    """Lee las tablas OMOP desde disco y devuelve la cohorte clínica depurada."""
    base = Path(dir_datos)
    df_person = pl.read_parquet(base / "person.parquet")
    df_visit = pl.read_parquet(base / "visit_occurrence.parquet")
    df_condition = pl.read_parquet(base / "condition_occurrence.parquet")
    return construir_cohorte_clinica(df_person, df_visit, df_condition)
