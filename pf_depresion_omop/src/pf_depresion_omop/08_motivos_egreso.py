import matplotlib.pyplot as plt
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

    print("Distribución de Motivos de Egreso (Cohorte F32/F33)")
    print(df_egresos)


motivos = [
    "Defunción",
    "Fuga",
    "Curación",
    "Traslado",
    "Otro",
    "Alta voluntaria",
    "Mejoría",
]
conteos = [4, 17, 37, 167, 422, 719, 9305]
total = sum(conteos)
porcentajes = [(c / total) * 100 for c in conteos]

fig, ax = plt.subplots(figsize=(9.5, 4.8))
bars = ax.barh(motivos, conteos, color="#1f4e78", height=0.6)

for bar, c, p in zip(bars, conteos, porcentajes):
    ax.text(
        bar.get_width() + 140,
        bar.get_y() + bar.get_height() / 2,
        f"{c:,} ({p:.2f}%)",
        va="center",
        fontsize=9.5,
    )

ax.set_title("Distribución de motivos de egreso hospitalario (F32/F33) - 2024", fontsize=12)
ax.set_xlabel("Número de egresos (n)")
ax.set_xlim(0, 11000)
ax.grid(axis="x", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("data/motivos_egreso.png", dpi=300)

if __name__ == "__main__":
    analizar_motivos_egreso()
