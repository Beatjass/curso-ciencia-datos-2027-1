import datetime as dt
import importlib

import matplotlib
import polars as pl

matplotlib.use("Agg")
mod_08 = importlib.import_module("pf_depresion_omop.08_motivos_egreso")


def test_calcular_motivos_egreso_y_grafica(tmp_path):
    # 3 casos de mejoría ("2"), 1 de alta voluntaria ("3"), 1 código desconocido ("99")
    codigos = ["2", "2", "2", "3", "99"]
    n = len(codigos)

    df_person = pl.DataFrame(
        {
            "person_id": list(range(1, n + 1)),
            "gender_concept_id": [8532] * n,
            "year_of_birth": [1990] * n,
        }
    )
    df_visit = pl.DataFrame(
        {
            "visit_occurrence_id": list(range(1, n + 1)),
            "person_id": list(range(1, n + 1)),
            "visit_start_date": [dt.date(2024, 4, 20)] * n,
            "visit_end_date": [dt.date(2024, 4, 26)] * n,
            "discharge_to_source_value": codigos,
        }
    )
    df_condition = pl.DataFrame(
        {
            "condition_occurrence_id": list(range(1, n + 1)),
            "person_id": list(range(1, n + 1)),
            "condition_source_value": ["F322"] * n,
        }
    )

    df_egresos = mod_08.calcular_motivos_egreso(df_person, df_visit, df_condition)

    assert df_egresos["len"].sum() == 5
    assert round(df_egresos["porcentaje"].sum(), 2) == 100.0
    assert df_egresos["motivo_clinico"][0] == "Mejoría"
    assert df_egresos["len"][0] == 3
    assert "No especificado" in df_egresos["motivo_clinico"].to_list()

    ruta_png = mod_08.graficar_motivos_egreso(df_egresos, tmp_path / "motivos.png")
    assert ruta_png.exists()
    assert ruta_png.stat().st_size > 0
