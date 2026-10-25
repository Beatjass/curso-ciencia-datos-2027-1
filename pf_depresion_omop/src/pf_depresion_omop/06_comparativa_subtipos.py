import polars as pl
from scipy import stats


def comparar_subtipos_depresion():
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

    f32_estancias = (
        df_cohorte.filter(pl.col("condition_source_value").str.starts_with("F32"))
        .get_column("dias_estancia")
        .to_numpy()
    )

    f33_estancias = (
        df_cohorte.filter(pl.col("condition_source_value").str.starts_with("F33"))
        .get_column("dias_estancia")
        .to_numpy()
    )

    stat, p_value = stats.mannwhitneyu(f32_estancias, f33_estancias, alternative="two-sided")

    print("--- Comparativa: Episodio Único (F32) vs. Recurrente (F33) ---")
    print(f"Mediana F32: {pl.Series(f32_estancias).median()} días (n={len(f32_estancias)})")
    print(f"Mediana F33: {pl.Series(f33_estancias).median()} días (n={len(f33_estancias)})\n")
    print(f"Estadístico U: {stat}")
    print(f"Valor p: {p_value:.8f}")

    if p_value < 0.05:
        print("\nConclusión: Se rechaza H0. Existe diferencia significativa en estancias.")
    else:
        print("\nConclusión: No se rechaza H0. No hay diferencia significativa en estancias.")


if __name__ == "__main__":
    comparar_subtipos_depresion()
