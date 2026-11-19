from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

NOMBRES_MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def calcular_estacionalidad_mensual(
    df_person: pl.DataFrame,
    df_visit: pl.DataFrame,
    df_condition: pl.DataFrame,
) -> pl.DataFrame:
    """Calcula el conteo de ingresos hospitalarios por mes (1 a 12) sobre la cohorte depurada."""
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
            & (pl.col("dias_estancia") >= 0)
            & (pl.col("dias_estancia") <= 30)
        )
    )

    conteos_mes = df_cohorte.group_by("mes").len()
    base_meses = pl.DataFrame(
        {
            "mes": list(range(1, 13)),
            "nombre_mes": NOMBRES_MESES,
        }
    )

    return (
        base_meses.join(conteos_mes, on="mes", how="left")
        .with_columns(pl.col("len").fill_null(0).cast(pl.Int64))
        .sort("mes")
    )


def graficar_estacionalidad(df_mensual: pl.DataFrame, ruta_salida: Path) -> Path:
    """Genera y guarda el gráfico de serie temporal mensual."""
    meses = df_mensual["nombre_mes"].to_list()
    conteos = df_mensual["len"].to_list()

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(meses, conteos, marker="o", linewidth=2.2, color="#1f4e78")
    ax.fill_between(meses, conteos, color="#1f4e78", alpha=0.1)

    max_val = max(conteos) if conteos else 10
    min_val = min(conteos) if conteos else 0
    margen = max(int((max_val - min_val) * 0.15), 2)

    for i, v in enumerate(conteos):
        ax.text(i, v + max(margen * 0.25, 0.5), str(v), ha="center", fontsize=9)

    ax.set_title("Estacionalidad de ingresos hospitalarios por depresión (F32/F33) - 2024")
    ax.set_xlabel("Mes de ingreso (visit_start_date)")
    ax.set_ylabel("Número de egresos")
    ax.set_ylim(max(0, min_val - margen), max_val + margen * 1.5)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=300)
    plt.close(fig)
    return ruta_salida


def analizar_estacionalidad(dir_datos: Path | str = "data") -> pl.DataFrame:
    base = Path(dir_datos)
    df_person = pl.read_parquet(base / "person.parquet")
    df_visit = pl.read_parquet(base / "visit_occurrence.parquet")
    df_condition = pl.read_parquet(base / "condition_occurrence.parquet")

    df_mensual = calcular_estacionalidad_mensual(df_person, df_visit, df_condition)

    print("Estacionalidad: ingresos hospitalarios mensuales (2024)")
    with pl.Config(tbl_rows=12):
        print(df_mensual)

    ruta_png = graficar_estacionalidad(df_mensual, base / "estacionalidad_mensual.png")
    print(f"Gráfica guardada exitosamente en {ruta_png}")
    return df_mensual


# main.py
main = analizar_estacionalidad


if __name__ == "__main__":
    main()
