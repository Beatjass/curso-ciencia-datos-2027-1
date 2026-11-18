import matplotlib.pyplot as plt
import polars as pl


def analizar_estacionalidad():
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
                pl.col("visit_start_date").dt.month().alias("mes"),
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

    df_mensual = df_cohorte.group_by("mes").len().sort("mes")

    print("Estacionalidad: ingresos hospitalarios mensuales (2024)")
    with pl.Config(tbl_rows=12):
        print(df_mensual)


meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
conteos = [683, 805, 836, 1007, 1047, 943, 921, 861, 876, 1067, 847, 778]

plt.figure(figsize=(10, 4.5))
plt.plot(meses, conteos, marker="o", linewidth=2.2, color="#1f4e78")
plt.fill_between(meses, conteos, color="#1f4e78", alpha=0.1)
for i, v in enumerate(conteos):
    plt.text(i, v + 18, str(v), ha="center", fontsize=9)

plt.title("Estacionalidad de ingresos hospitalarios por depresión (F32/F33) - 2024")
plt.xlabel("Mes de ingreso (visit_start_date)")
plt.ylabel("Número de egresos")
plt.ylim(600, 1150)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("data/estacionalidad_mensual.png", dpi=300)

if __name__ == "__main__":
    analizar_estacionalidad()
