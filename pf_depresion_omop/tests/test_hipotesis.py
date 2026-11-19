import datetime as dt
import importlib

import polars as pl
import pytest

mod_05 = importlib.import_module("pf_depresion_omop.05_pruebas_hipotesis")


def _construir_tablas(dias_hombres: list[int], dias_mujeres: list[int]):
    n_h, n_m = len(dias_hombres), len(dias_mujeres)
    total = n_h + n_m
    dias = dias_hombres + dias_mujeres

    df_person = pl.DataFrame(
        {
            "person_id": list(range(1, total + 1)),
            "gender_concept_id": [8507] * n_h + [8532] * n_m,
            "year_of_birth": [1990] * total,
        }
    )
    fin = dt.date(2024, 5, 28)
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
            "condition_source_value": ["F322"] * total,
        }
    )
    return df_person, df_visit, df_condition


@pytest.mark.parametrize(
    "dias_h,dias_m,espera_rechazo",
    [
        ([5, 6, 7, 6, 5, 6], [5, 6, 7, 6, 5, 6], False),  # Distribuciones idénticas
        ([2, 2, 3, 2, 3, 2], [12, 14, 15, 13, 14, 15], True),  # Diferencia clara
    ],
)
def test_mann_whitney_estancia_escenarios(dias_h, dias_m, espera_rechazo):
    df_p, df_v, df_c = _construir_tablas(dias_h, dias_m)
    res = mod_05.calcular_mann_whitney_estancia(df_p, df_v, df_c)

    assert res["n_hombres"] == len(dias_h)
    assert res["n_mujeres"] == len(dias_m)
    assert res["rechaza_h0"] is espera_rechazo


def test_mann_whitney_grupo_vacio_lanza_error():
    df_p, df_v, df_c = _construir_tablas([5, 6, 7], [])
    with pytest.raises(ValueError, match="ambos géneros"):
        mod_05.calcular_mann_whitney_estancia(df_p, df_v, df_c)
