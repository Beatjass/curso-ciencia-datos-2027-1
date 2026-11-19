import datetime as dt
import importlib

import polars as pl
import pytest

mod_06 = importlib.import_module("pf_depresion_omop.06_comparativa_subtipos")


def _crear_cohortes_subtipos(dias_f32: list[int], dias_f33: list[int]):
    n_32, n_33 = len(dias_f32), len(dias_f33)
    total = n_32 + n_33
    dias = dias_f32 + dias_f33
    codigos = ["F322"] * n_32 + ["F331"] * n_33

    df_person = pl.DataFrame(
        {
            "person_id": list(range(1, total + 1)),
            "gender_concept_id": [8532] * total,
            "year_of_birth": [1992] * total,
        }
    )
    fin = dt.date(2024, 6, 28)
    df_visit = pl.DataFrame(
        {
            "visit_occurrence_id": list(range(1, total + 1)),
            "person_id": list(range(1, total + 1)),
            "visit_start_date": [fin - dt.timedelta(days=d) for d in dias],
            "visit_end_date": [fin] * total,
        }
    )
    df_condition = pl.DataFrame(
        {
            "condition_occurrence_id": list(range(1, total + 1)),
            "person_id": list(range(1, total + 1)),
            "condition_source_value": codigos,
        }
    )
    return df_person, df_visit, df_condition


@pytest.mark.parametrize(
    "dias_f32,dias_f33,espera_rechazo",
    [
        ([6, 7, 5, 6, 7], [6, 5, 7, 6, 6], False),
        ([3, 4, 3, 2, 3], [14, 15, 16, 13, 15], True),
    ],
)
def test_comparativa_subtipos_mann_whitney(dias_f32, dias_f33, espera_rechazo):
    df_p, df_v, df_c = _crear_cohortes_subtipos(dias_f32, dias_f33)
    res = mod_06.calcular_comparativa_subtipos(df_p, df_v, df_c)

    assert res["n_f32"] == len(dias_f32)
    assert res["n_f33"] == len(dias_f33)
    assert res["rechaza_h0"] is espera_rechazo


def test_comparativa_subtipos_sin_f33_lanza_error():
    df_p, df_v, df_c = _crear_cohortes_subtipos([5, 6, 7], [])
    with pytest.raises(ValueError, match="F32 como en F33"):
        mod_06.calcular_comparativa_subtipos(df_p, df_v, df_c)
