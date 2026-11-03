import polars as pl


def analizar_motivos_egreso():
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

    diccionario_egresos = {
        "1": "Curación",
        "2": "Mejoría",
        "3": "Alta voluntaria",
        "4": "Traslado",
        "5": "Defunción",
        "6": "Fuga",
        "7": "Otro",
    }

    # Agrupamos por el campo OMOP correspondiente al motivo de egreso
    df_egresos = (
        df_cohorte.with_columns(
            pl.col("discharge_to_source_value").replace(diccionario_egresos).alias("motivo_clinico")
        )
        .group_by("motivo_clinico")
        .len()
        .sort("len", descending=True)
    )

    print("--- Distribución de Motivos de Egreso (Cohorte F32/F33) ---")
    print(df_egresos)


if __name__ == "__main__":
    analizar_motivos_egreso()
