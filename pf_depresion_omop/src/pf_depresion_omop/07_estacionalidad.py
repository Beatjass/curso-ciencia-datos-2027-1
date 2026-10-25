import polars as pl


def analizar_estacionalidad():
    df_person = pl.read_parquet("data/person.parquet")
    df_visit = pl.read_parquet("data/visit_occurrence.parquet")
    df_condition = pl.read_parquet("data/condition_occurrence.parquet")

    df_cohorte = (
        df_person.join(df_visit, on="person_id", how="inner")
        .join(df_condition, on="person_id", how="inner")
        .with_columns(
            [
                (2024 - pl.col("year_of_birth")).alias("edad_estimada"),
                (pl.col("visit_end_date") - pl.col("visit_start_date"))
                .dt.total_days()
                .alias("dias_estancia"),
                pl.col("visit_start_date").dt.month().alias("mes"),
            ]
        )
        .filter(
            (
                pl.col("condition_source_value").str.starts_with("F32")
                | pl.col("condition_source_value").str.starts_with("F33")
            )
            & (pl.col("edad_estimada") <= 120)
            & (pl.col("dias_estancia") <= 30)
        )
    )

    df_mensual = df_cohorte.group_by("mes").len().sort("mes")

    print("--- Estacionalidad: Ingresos Hospitalarios Mensuales (2024) ---")
    with pl.Config(tbl_rows=12):
        print(df_mensual)


if __name__ == "__main__":
    analizar_estacionalidad()
