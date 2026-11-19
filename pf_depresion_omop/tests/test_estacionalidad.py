import datetime as dt
import importlib

import matplotlib
import polars as pl

matplotlib.use("Agg")
mod_07 = importlib.import_module("pf_depresion_omop.07_estacionalidad")


def test_calcular_estacionalidad_mensual_y_grafica(tmp_path):
    # 2 ingresos en enero y 1 ingreso en octubre (total = 3; resto de meses = 0)
    df_person = pl.DataFrame(
        {
            "person_id": [1, 2, 3],
            "gender_concept_id": [8532, 8507, 8532],
            "year_of_birth": [1995, 1988, 1990],
        }
    )
    df_visit = pl.DataFrame(
        {
            "visit_occurrence_id": [1, 2, 3],
            "person_id": [1, 2, 3],
            "visit_start_date": [
                dt.date(2024, 1, 10),
                dt.date(2024, 1, 22),
                dt.date(2024, 10, 15),
            ],
            "visit_end_date": [
                dt.date(2024, 1, 15),
                dt.date(2024, 1, 28),
                dt.date(2024, 10, 20),
            ],
        }
    )
    df_condition = pl.DataFrame(
        {
            "condition_occurrence_id": [1, 2, 3],
            "person_id": [1, 2, 3],
            "condition_source_value": ["F322", "F331", "F329"],
        }
    )

    df_mensual = mod_07.calcular_estacionalidad_mensual(df_person, df_visit, df_condition)

    assert df_mensual.height == 12
    assert df_mensual["len"].sum() == 3
    assert df_mensual.filter(pl.col("mes") == 1)["len"].item() == 2
    assert df_mensual.filter(pl.col("mes") == 10)["len"].item() == 1
    assert df_mensual.filter(pl.col("mes") == 6)["len"].item() == 0

    ruta_png = mod_07.graficar_estacionalidad(df_mensual, tmp_path / "estacionalidad.png")
    assert ruta_png.exists()
    assert ruta_png.stat().st_size > 0
