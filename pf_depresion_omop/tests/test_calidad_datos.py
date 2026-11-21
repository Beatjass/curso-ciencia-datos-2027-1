from pathlib import Path

import polars as pl
import pytest

from pf_depresion_omop.utils_cohorte import construir_cohorte_clinica


def test_calidad_fechas_visita():
    """Valida que la fecha de ingreso nunca sea posterior a la fecha de egreso."""
    df_visit = pl.read_parquet("data/visit_occurrence.parquet")

    fechas_invalidas = df_visit.filter(pl.col("visit_end_date") < pl.col("visit_start_date"))
    assert fechas_invalidas.is_empty(), (
        f"Error: Se encontraron {fechas_invalidas.height} registros con fechas temporales ilógicas."
    )


def test_valores_nulos_criticos():
    """Verifica que las llaves primarias y foráneas no contengan valores nulos."""
    df_visit = pl.read_parquet("data/visit_occurrence.parquet")

    nulos_person = df_visit.filter(pl.col("person_id").is_null())
    nulos_visit = df_visit.filter(pl.col("visit_occurrence_id").is_null())

    assert nulos_person.is_empty(), "Error: Existen valores nulos en person_id."
    assert nulos_visit.is_empty(), "Error: Existen valores nulos en visit_occurrence_id."


def test_conceptos_estandar_omop():
    """Asegura que el tipo de visita esté estandarizado como Inpatient Visit (9201)."""
    df_visit = pl.read_parquet("data/visit_occurrence.parquet")

    conceptos_distintos = df_visit.filter(pl.col("visit_concept_id") != 9201)

    assert conceptos_distintos.is_empty(), (
        "Error: Hay identificadores de concepto de visita ajenos a 9201."
    )


def test_consulta_sql_cohorte_suma_10671():
    """Valida que 10_cohorte_depresion.sql aplique el límite de 30 días y sume 10,671."""
    sql_path = Path("src/pf_depresion_omop/10_cohorte_depresion.sql")
    assert sql_path.exists(), "Falta el archivo 10_cohorte_depresion.sql"

    sql_text = sql_path.read_text(encoding="utf-8")
    assert "JOIN visit_occurrence v ON c.person_id = v.person_id" in sql_text
    assert "<= 30" in sql_text
    assert "2024 - p.year_of_birth" in sql_text

    ruta_person = Path("data/person.parquet")
    if not ruta_person.exists():
        pytest.skip("Datos Parquet locales no disponibles en entorno CI.")

    df_person = pl.read_parquet("data/person.parquet")
    df_visit = pl.read_parquet("data/visit_occurrence.parquet")
    df_condition = pl.read_parquet("data/condition_occurrence.parquet")

    df_cohorte = construir_cohorte_clinica(df_person, df_visit, df_condition)
    df_sql_simulado = df_cohorte.group_by(["condition_source_value", "gender_concept_id"]).agg(
        pl.col("person_id").n_unique().alias("total_pacientes")
    )

    assert df_sql_simulado["total_pacientes"].sum() == 10671
    hombres = df_sql_simulado.filter(pl.col("gender_concept_id") == 8507)["total_pacientes"].sum()
    mujeres = df_sql_simulado.filter(pl.col("gender_concept_id") == 8532)["total_pacientes"].sum()
    assert hombres == 2757
    assert mujeres == 7914
