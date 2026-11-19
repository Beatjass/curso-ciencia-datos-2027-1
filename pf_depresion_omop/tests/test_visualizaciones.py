import datetime as dt
import importlib

import matplotlib
import polars as pl

matplotlib.use("Agg")
mod_04 = importlib.import_module("pf_depresion_omop.04_visualizaciones")


def test_preparar_datos_graficas_y_render(tmp_path):
    df_person = pl.DataFrame(
        {
            "person_id": [1, 2],
            "gender_concept_id": [8532, 8507],
            "year_of_birth": [1994, 1984],
        }
    )
    df_visit = pl.DataFrame(
        {
            "visit_occurrence_id": [1, 2],
            "person_id": [1, 2],
            "visit_start_date": [dt.date(2024, 4, 22), dt.date(2024, 6, 20)],
            "visit_end_date": [dt.date(2024, 4, 28), dt.date(2024, 6, 28)],
        }
    )
    df_condition = pl.DataFrame(
        {
            "condition_occurrence_id": [1, 2],
            "person_id": [1, 2],
            "condition_source_value": ["F322", "F331"],
        }
    )

    df_pd = mod_04.preparar_datos_graficas(df_person, df_visit, df_condition)
    assert df_pd["genero"].tolist() == ["Femenino", "Masculino"]
    assert df_pd["edad_estimada"].tolist() == [30, 40]

    # Verifica la generación física del archivo PNG en carpeta temporal
    df_person.write_parquet(tmp_path / "person.parquet")
    df_visit.write_parquet(tmp_path / "visit_occurrence.parquet")
    df_condition.write_parquet(tmp_path / "condition_occurrence.parquet")

    salida = mod_04.generar_graficas(dir_datos=tmp_path, mostrar=False)
    assert salida.exists()
    assert salida.stat().st_size > 0
