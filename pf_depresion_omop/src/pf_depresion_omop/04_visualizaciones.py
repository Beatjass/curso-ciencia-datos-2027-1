from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import polars as pl
import seaborn as sns


def preparar_datos_graficas(
    df_person: pl.DataFrame,
    df_visit: pl.DataFrame,
    df_condition: pl.DataFrame,
) -> pd.DataFrame:
    """Filtra la cohorte clínica final y prepara el DataFrame para visualización."""
    df_cohorte = df_person.join(df_visit, on="person_id", how="inner").join(
        df_condition, on="person_id", how="inner"
    )

    df_final = df_cohorte.with_columns(
        [
            (2024 - pl.col("year_of_birth")).alias("edad_estimada"),
            (pl.col("visit_end_date") - pl.col("visit_start_date"))
            .dt.total_days()
            .alias("dias_estancia"),
        ]
    ).filter(
        (
            pl.col("condition_source_value").str.starts_with("F32")
            | pl.col("condition_source_value").str.starts_with("F33")
        )
        & (pl.col("edad_estimada") <= 120)
        & (pl.col("dias_estancia") >= 0)
        & (pl.col("dias_estancia") <= 30)
    )

    df_pd = df_final.select(["edad_estimada", "dias_estancia", "gender_concept_id"]).to_pandas()
    df_pd["genero"] = df_pd["gender_concept_id"].map({8507: "Masculino", 8532: "Femenino"})
    return df_pd


def generar_graficas(
    dir_datos: Path | str = "data",
    mostrar: bool = False,
) -> Path:
    base = Path(dir_datos)
    df_person = pl.read_parquet(base / "person.parquet")
    df_visit = pl.read_parquet(base / "visit_occurrence.parquet")
    df_condition = pl.read_parquet(base / "condition_occurrence.parquet")

    df_pd = preparar_datos_graficas(df_person, df_visit, df_condition)

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.histplot(
        data=df_pd, x="edad_estimada", hue="genero", bins=30, kde=True, ax=axes[0], palette="muted"
    )
    axes[0].set_title("Distribución de edad por género")
    axes[0].set_xlabel("Edad (años)")
    axes[0].set_ylabel("Frecuencia")

    sns.boxplot(
        data=df_pd,
        x="genero",
        y="dias_estancia",
        hue="genero",
        legend=False,
        ax=axes[1],
        palette="muted",
    )
    axes[1].set_title("Días de estancia hospitalaria (≤ 30 días)")
    axes[1].set_xlabel("Género")
    axes[1].set_ylabel("Días de internamiento")

    ruta_salida = base / "distribucion_demografica.png"
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=300)
    print(f"Gráfica guardada exitosamente en {ruta_salida}")

    if mostrar:
        plt.show()
    else:
        plt.close(fig)

    return ruta_salida


# main.py
main = generar_graficas


if __name__ == "__main__":
    generar_graficas(mostrar=True)
