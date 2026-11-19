from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

DICCIONARIO_EGRESOS: dict[str, str] = {
    "1": "Curación",
    "2": "Mejoría",
    "3": "Alta voluntaria",
    "4": "Traslado",
    "5": "Defunción",
    "6": "Fuga",
    "7": "Otro",
}


def calcular_motivos_egreso(
    df_person: pl.DataFrame,
    df_visit: pl.DataFrame,
    df_condition: pl.DataFrame,
) -> pl.DataFrame:
    """Agrupa los motivos de egreso clínico y calcula sus conteos y porcentajes."""
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

    df_egresos = (
        df_cohorte.with_columns(
            pl.col("discharge_to_source_value")
            .cast(pl.Utf8)
            .replace_strict(DICCIONARIO_EGRESOS, default="No especificado")
            .alias("motivo_clinico")
        )
        .group_by("motivo_clinico")
        .len()
        .sort("len", descending=True)
    )

    total = df_egresos["len"].sum()
    if total > 0:
        df_egresos = df_egresos.with_columns(
            ((pl.col("len") / total) * 100).round(2).alias("porcentaje")
        )
    else:
        df_egresos = df_egresos.with_columns(pl.lit(0.0).alias("porcentaje"))

    return df_egresos


def graficar_motivos_egreso(df_egresos: pl.DataFrame, ruta_salida: Path) -> Path:
    """Genera el gráfico de barras horizontales con conteos y porcentajes."""
    df_plot = df_egresos.sort("len", descending=False)
    motivos = df_plot["motivo_clinico"].to_list()
    conteos = df_plot["len"].to_list()
    porcentajes = df_plot["porcentaje"].to_list()

    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    bars = ax.barh(motivos, conteos, color="#1f4e78", height=0.6)

    max_val = max(conteos) if conteos else 10
    offset = max(max_val * 0.015, 0.2)

    for bar, c, p in zip(bars, conteos, porcentajes):
        ax.text(
            bar.get_width() + offset,
            bar.get_y() + bar.get_height() / 2,
            f"{c:,} ({p:.2f}%)",
            va="center",
            fontsize=9.5,
        )

    ax.set_title("Distribución de motivos de egreso hospitalario (F32/F33) - 2024", fontsize=12)
    ax.set_xlabel("Número de egresos (n)")
    ax.set_xlim(0, max_val * 1.22 if max_val > 0 else 10)
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=300)
    plt.close(fig)
    return ruta_salida


def analizar_motivos_egreso(dir_datos: Path | str = "data") -> pl.DataFrame:
    base = Path(dir_datos)
    df_person = pl.read_parquet(base / "person.parquet")
    df_visit = pl.read_parquet(base / "visit_occurrence.parquet")
    df_condition = pl.read_parquet(base / "condition_occurrence.parquet")

    df_egresos = calcular_motivos_egreso(df_person, df_visit, df_condition)

    print("Distribución de Motivos de Egreso (Cohorte F32/F33)")
    print(df_egresos)

    ruta_png = graficar_motivos_egreso(df_egresos, base / "motivos_egreso.png")
    print(f"Gráfica guardada exitosamente en {ruta_png}")
    return df_egresos


# main.py
main = analizar_motivos_egreso


if __name__ == "__main__":
    main()
