from pathlib import Path

import polars as pl
from scipy import stats


def calcular_mann_whitney_estancia(
    df_person: pl.DataFrame,
    df_visit: pl.DataFrame,
    df_condition: pl.DataFrame,
) -> dict[str, float | int | bool]:
    """Reconstruye la cohorte depurada y ejecuta la prueba U de Mann-Whitney por género."""
    df_final = (
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

    hombres = (
        df_final.filter(pl.col("gender_concept_id") == 8507).get_column("dias_estancia").to_numpy()
    )
    mujeres = (
        df_final.filter(pl.col("gender_concept_id") == 8532).get_column("dias_estancia").to_numpy()
    )

    if len(hombres) == 0 or len(mujeres) == 0:
        raise ValueError(
            "Se requieren observaciones en ambos géneros para ejecutar Mann-Whitney U."
        )

    stat, p_value = stats.mannwhitneyu(hombres, mujeres, alternative="two-sided")

    return {
        "n_hombres": int(len(hombres)),
        "n_mujeres": int(len(mujeres)),
        "mediana_hombres": float(pl.Series(hombres).median()),
        "mediana_mujeres": float(pl.Series(mujeres).median()),
        "estadistico_u": float(stat),
        "p_value": float(p_value),
        "rechaza_h0": bool(p_value < 0.05),
    }


def prueba_hipotesis_estancia(dir_datos: Path | str = "data") -> dict[str, float | int | bool]:
    base = Path(dir_datos)
    df_person = pl.read_parquet(base / "person.parquet")
    df_visit = pl.read_parquet(base / "visit_occurrence.parquet")
    df_condition = pl.read_parquet(base / "condition_occurrence.parquet")

    res = calcular_mann_whitney_estancia(df_person, df_visit, df_condition)

    print("--- Prueba U de Mann-Whitney (Estancia Hospitalaria por Género) ---")
    print(
        "H0: No existe diferencia significativa en los días "
        "de internamiento entre hombres y mujeres."
    )
    print(f"Mediana Hombres: {res['mediana_hombres']} días (n={res['n_hombres']})")
    print(f"Mediana Mujeres: {res['mediana_mujeres']} días (n={res['n_mujeres']})\n")

    print(f"Estadístico U: {res['estadistico_u']}")
    print(f"Valor p: {res['p_value']:.8f}")

    if res["rechaza_h0"]:
        print(
            "\nConclusión: Se rechaza H0. Existe diferencia estadísticamente "
            "significativa en el tiempo de internamiento entre géneros."
        )
    else:
        print(
            "\nConclusión: No se rechaza H0. No hay evidencia de "
            "diferencia estadísticamente significativa entre géneros."
        )

    return res


# ain.py
main = prueba_hipotesis_estancia


if __name__ == "__main__":
    main()
