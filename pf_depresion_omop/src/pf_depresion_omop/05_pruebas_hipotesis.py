from pathlib import Path

import polars as pl
from scipy import stats

try:
    from pf_depresion_omop.utils_cohorte import construir_cohorte_clinica
except ImportError:
    from utils_cohorte import construir_cohorte_clinica  # type: ignore[no-redef]


def calcular_mann_whitney_estancia(
    df_person: pl.DataFrame,
    df_visit: pl.DataFrame,
    df_condition: pl.DataFrame,
) -> dict[str, float | int | bool]:
    """Reconstruye la cohorte depurada y ejecuta la prueba U de Mann-Whitney por género."""
    df_final = construir_cohorte_clinica(df_person, df_visit, df_condition)

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
            "\nConclusión: No se rechaza H0. No hay diferencia "
            "estadísticamente significativa entre géneros."
        )

    return res


# main.py
main = prueba_hipotesis_estancia


if __name__ == "__main__":
    main()
