import polars as pl


def analisis_descriptivo():
    # Cargar las tres tablas del modelo OMOP
    df_person = pl.read_parquet("data/person.parquet")
    df_visit = pl.read_parquet("data/visit_occurrence.parquet")
    df_condition = pl.read_parquet("data/condition_occurrence.parquet")

    # Filtrar los diagnósticos de depresión (F32 y F33)
    df_condition_dep = df_condition.filter(
        pl.col("condition_source_value").str.starts_with("F32")
        | pl.col("condition_source_value").str.starts_with("F33")
    )

    # Unificar la información clínica usando el person_id
    df_cohorte = df_person.join(df_visit, on="person_id", how="inner").join(
        df_condition_dep, on="person_id", how="inner"
    )

    print(f"Total de registros clínicos de depresión: {df_cohorte.height}\n")

    # Calcular distribución demográfica por género
    dist_genero = df_cohorte.group_by("gender_concept_id").len()
    print("Distribución por género (8507=Masculino, 8532=Femenino, 0=Desconocido):")
    print(dist_genero)

    # Calcular frecuencia de diagnósticos específicos
    dist_dx = df_cohorte.group_by("condition_source_value").len().sort("len", descending=True)
    print("\nDistribución de diagnósticos CIE-10 (Episodios vs Trastorno Recurrente):")
    print(dist_dx)

    # Estadísticas de edad y días de estancia
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
    df_final = df_edad_ok.filter(pl.col("dias_estancia") <= 30)

    # Exportar registros excluidos
    df_edad_invalida.write_csv("data/registros_excluidos_edad.csv")
    df_estancia_larga.write_csv("data/registros_estancia_prolongada.csv")

    print("\nReporte de atrición final:")
    print(f"Excluidos por edad irreal: {df_edad_invalida.height}")
    print(f"Excluidos por cuidado residencial (>30 días): {df_estancia_larga.height}")
    print(f"Cohorte clínica final: {df_final.height}")

    print("\nEstadísticas de días de estancia hospitalaria:")
    print(df_final.select("dias_estancia").describe())


if __name__ == "__main__":
    analisis_descriptivo()
