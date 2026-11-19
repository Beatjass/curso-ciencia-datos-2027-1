import datetime as dt
import importlib

import polars as pl
import pytest

mod_01 = importlib.import_module("pf_depresion_omop.01_limpieza_y_atricion")
mod_02 = importlib.import_module("pf_depresion_omop.02_mapeo_omop")


@pytest.fixture
def muestra_egresos() -> pl.LazyFrame:
    return pl.DataFrame(
        {
            "AFECPRIN3": ["F32", "F33", "F20", "F32", "F33", "F32"],
            "AFECPRIN4": ["F322", "F331", "F200", "F329", "F332", "F320"],
            "CLAVE_EDAD": [1, 1, 1, 9, 1, 1],  # Fila 4 excluida por CLAVE_EDAD == 9
            "EDAD1": [25, 40, 30, 50, 135, 22],  # Fila 5 excluida por EDAD1 >= 120
            "MES": [3, 6, 4, 5, 7, 15],  # Fila 6 excluida por MES == 15
            "SEXO": [2, 1, 1, 2, 1, 2],
            "DIAS_ESTA": [6, 10, 4, 2, 5, 3],
            "MOTIVO_EGRESO": [1, 2, 1, 1, 1, 1],
        }
    ).lazy()


def test_limpiar_cohorte_filtros_y_atricion(muestra_egresos):
    df_limpio, metricas = mod_01.limpiar_cohorte(muestra_egresos)

    assert metricas["total_egresos"] == 6
    assert metricas["total_cohorte"] == 5  # Excluye F20
    assert metricas["excluidos_cohorte"] == 1
    assert metricas["total_edad"] == 3  # Excluye CLAVE_EDAD=9 y EDAD1=135
    assert metricas["total_limpio"] == 2  # Excluye MES=15
    assert metricas["retencion_porcentaje"] == 40.0
    assert df_limpio["AFECPRIN4"].to_list() == ["F322", "F331"]


def test_limpiar_cohorte_dataframe_vacio():
    lf_vacio = pl.DataFrame(
        schema={
            "AFECPRIN3": pl.Utf8,
            "CLAVE_EDAD": pl.Int64,
            "EDAD1": pl.Int64,
            "MES": pl.Int64,
            "SEXO": pl.Int64,
        }
    ).lazy()

    df_limpio, metricas = mod_01.limpiar_cohorte(lf_vacio)
    assert df_limpio.is_empty()
    assert metricas["retencion_porcentaje"] == 0.0


@pytest.mark.parametrize(
    "sexo_dgis,concepto_esperado",
    [
        (1, 8507),  # Male en OMOP
        (2, 8532),  # Female en OMOP
        (9, 0),  # Desconocido mapea a 0
    ],
)
def test_mapeo_person_genero_y_nacimiento(sexo_dgis, concepto_esperado):
    df = pl.DataFrame({"SEXO": [sexo_dgis], "EDAD1": [34]})
    person = mod_02.tabla_person(df)

    assert person["person_id"].to_list() == [1]
    assert person["gender_concept_id"].to_list() == [concepto_esperado]
    assert person["year_of_birth"].to_list() == [1990]


def test_integridad_relacional_omop_y_calculo_fechas(muestra_egresos):
    df_limpio, _ = mod_01.limpiar_cohorte(muestra_egresos)

    person = mod_02.tabla_person(df_limpio)
    visit = mod_02.tabla_visit_occurrence(df_limpio)
    condition = mod_02.tabla_condition_occurrence(df_limpio)

    # Integridad referencial 1:1 de person_id
    ids_person = set(person["person_id"].to_list())
    assert set(visit["person_id"].to_list()) == ids_person
    assert set(condition["person_id"].to_list()) == ids_person

    # Cálculo exacto de fecha de inicio (28 de marzo - 6 días = 22 de marzo)
    assert visit["visit_end_date"][0] == dt.date(2024, 3, 28)
    assert visit["visit_start_date"][0] == dt.date(2024, 3, 22)
    assert condition["condition_start_date"][0] == dt.date(2024, 3, 22)
