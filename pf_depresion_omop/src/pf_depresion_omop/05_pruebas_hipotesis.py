import polars as pl
from scipy import stats


def prueba_hipotesis_estancia():
    # Cargar datos
    df_person = pl.read_parquet("data/person.parquet")
    df_visit = pl.read_parquet("data/visit_occurrence.parquet")
    df_condition = pl.read_parquet("data/condition_occurrence.parquet")

    # Reconstruir cohorte clínica depurada
    df_final = (
        df_person.join(df_visit, on="person_id", how="inner")
        .join(df_visit, on="person_id", how="inner")
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

    # Extraer vectores de datos por género (8507=masculino, 8532=femenino)
    hombres = (
        df_final.filter(pl.col("gender_concept_id") == 8507).get_column("dias_estancia").to_numpy()
    )
    mujeres = (
        df_final.filter(pl.col("gender_concept_id") == 8532).get_column("dias_estancia").to_numpy()
    )

    # Ejecutar prueba U de Mann-Whitney
    stat, p_value = stats.mannwhitneyu(hombres, mujeres, alternative="two-sided")

    print("--- Prueba U de Mann-Whitney (Estancia Hospitalaria por Género) ---")
    print(
        "H0: No existe diferencia significativa en los días "
        "de internamiento entre hombres y mujeres."
    )
    print(f"Mediana Hombres: {pl.Series(hombres).median()} días (n={len(hombres)})")
    print(f"Mediana Mujeres: {pl.Series(mujeres).median()} días (n={len(mujeres)})\n")

    print(f"Estadístico U: {stat}")
    print(f"Valor p: {p_value:.8f}")

    if p_value < 0.05:
        print(
            "\nConclusión: Se rechaza H0. Existe diferencia estadísticamente "
            "significativa en el tiempo de internamiento entre géneros."
        )
    else:
        print(
            "\nConclusión: No se rechaza H0. No hay evidencia de "
            "diferencia estadísticamente significativa entre géneros."
        )


if __name__ == "__main__":
    prueba_hipotesis_estancia()
