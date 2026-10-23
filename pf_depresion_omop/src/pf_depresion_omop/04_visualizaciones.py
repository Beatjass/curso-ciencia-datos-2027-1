import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns


def generar_graficas():
    # Cargar datos
    df_person = pl.read_parquet("data/person.parquet")
    df_visit = pl.read_parquet("data/visit_occurrence.parquet")
    df_condition = pl.read_parquet("data/condition_occurrence.parquet")

    df_cohorte = df_person.join(df_visit, on="person_id", how="inner").join(
        df_condition, on="person_id", how="inner"
    )

    # Filtrar depresión y aplicar cortes clínicos
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
        & (pl.col("dias_estancia") <= 30)
    )

    # Preparar datos para Seaborn
    df_pd = df_final.select(["edad_estimada", "dias_estancia", "gender_concept_id"]).to_pandas()
    df_pd["genero"] = df_pd["gender_concept_id"].map({8507: "Masculino", 8532: "Femenino"})

    # Configurar y renderizar gráficas
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.histplot(
        data=df_pd, x="edad_estimada", hue="genero", bins=30, kde=True, ax=axes[0], palette="muted"
    )
    axes[0].set_title("Distribución de Edad por Género")
    axes[0].set_xlabel("Edad (años)")
    axes[0].set_ylabel("Frecuencia")

    sns.boxplot(data=df_pd, x="genero", y="dias_estancia", ax=axes[1], palette="muted")
    axes[1].set_title("Días de Estancia Hospitalaria (≤ 30 días)")
    axes[1].set_xlabel("Género")
    axes[1].set_ylabel("Días de internamiento")

    plt.tight_layout()
    plt.savefig("data/distribucion_demografica.png", dpi=300)
    print("Gráfica guardada exitosamente en data/distribucion_demografica.png")
    plt.show()


if __name__ == "__main__":
    generar_graficas()
