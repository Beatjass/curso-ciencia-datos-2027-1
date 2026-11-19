from pathlib import Path

import polars as pl
from scipy import stats


def calcular_comparativa_subtipos(
    df_person: pl.DataFrame,
    df_visit: pl.DataFrame,
    df_condition: pl.DataFrame,
) -> dict[str, float | int | bool]:
    """Compara los días de estancia entre episodio único (F32) y recurrente (F33)."""
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
            & (pl.col("dias_estancia") >= 0)
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

    if len(f32_estancias) == 0 or len(f33_estancias) == 0:
        raise ValueError("Se requieren observaciones tanto en F32 como en F33 para comparar.")

    stat, p_value = stats.mannwhitneyu(f32_estancias, f33_estancias, alternative="two-sided")

    return {
        "n_f32": int(len(f32_estancias)),
        "n_f33": int(len(f33_estancias)),
        "mediana_f32": float(pl.Series(f32_estancias).median()),
        "mediana_f33": float(pl.Series(f33_estancias).median()),
        "estadistico_u": float(stat),
        "p_value": float(p_value),
        "rechaza_h0": bool(p_value < 0.05),
    }


def comparar_subtipos_depresion(dir_datos: Path | str = "data") -> dict[str, float | int | bool]:
    base = Path(dir_datos)
    df_person = pl.read_parquet(base / "person.parquet")
    df_visit = pl.read_parquet(base / "visit_occurrence.parquet")
    df_condition = pl.read_parquet(base / "condition_occurrence.parquet")

    res = calcular_comparativa_subtipos(df_person, df_visit, df_condition)

    print("--- Comparativa: Episodio Único (F32) vs. Recurrente (F33) ---")
    print(f"Mediana F32: {res['mediana_f32']} días (n={res['n_f32']})")
    print(f"Mediana F33: {res['mediana_f33']} días (n={res['n_f33']})\n")
    print(f"Estadístico U: {res['estadistico_u']}")
    print(f"Valor p: {res['p_value']:.8f}")

    if res["rechaza_h0"]:
        print("\nConclusión: Se rechaza H0. Existe diferencia significativa en estancias.")
    else:
        print("\nConclusión: No se rechaza H0. No hay diferencia significativa en estancias.")

    return res


# main.py
main = comparar_subtipos_depresion


if __name__ == "__main__":
    main()
