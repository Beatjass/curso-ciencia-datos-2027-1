import datetime as dt
import importlib

import polars as pl

mod_03 = importlib.import_module("pf_depresion_omop.03_analisis_descriptivo")


def test_procesar_cohorte_descriptiva_filtros():
    df_person = pl.DataFrame(
        {
            "person_id": [1, 2, 3, 4],
            "gender_concept_id": [8532, 8507, 8532, 8507],
            "year_of_birth": [1995, 1890, 1985, 2000],  # person 2 -> 134 años (inválida)
        }
    )
    df_visit = pl.DataFrame(
        {
            "visit_occurrence_id": [1, 2, 3, 4],
            "person_id": [1, 2, 3, 4],
            "visit_start_date": [
                dt.date(2024, 3, 22),  # 6 días -> válido
                dt.date(2024, 3, 25),  # 3 días -> excluido por edad
                dt.date(2024, 2, 10),  # 47 días -> excluido por estancia > 30
                dt.date(2024, 5, 20),  # 8 días -> excluido por diagnóstico F200
            ],
            "visit_end_date": [
                dt.date(2024, 3, 28),
                dt.date(2024, 3, 28),
                dt.date(2024, 3, 28),
                dt.date(2024, 5, 28),
            ],
        }
    )
    df_condition = pl.DataFrame(
        {
            "condition_occurrence_id": [1, 2, 3, 4],
            "person_id": [1, 2, 3, 4],
            "condition_source_value": ["F322", "F331", "F329", "F200"],
        }
    )

    res = mod_03.procesar_cohorte_descriptiva(df_person, df_visit, df_condition)

    assert res["cohorte_bruta"].height == 3
    assert res["edad_invalida"].height == 1
    assert res["estancia_larga"].height == 1
    assert res["cohorte_final"].height == 1
    assert res["cohorte_final"]["person_id"].to_list() == [1]
    assert res["cohorte_final"]["dias_estancia"].to_list() == [6]
