import polars as pl


def test_calidad_fechas_visita():
    """Valida que la fecha de ingreso nunca sea posterior a la fecha de egreso."""
    df_visit = pl.read_parquet("data/visit_occurrence.parquet")

    fechas_invalidas = df_visit.filter(pl.col("visit_end_date") < pl.col("visit_start_date"))
    assert (
        fechas_invalidas.is_empty()
    ), f"Error: Se encontraron {fechas_invalidas.height} registros con fechas temporales ilógicas."


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

    assert (
        conceptos_distintos.is_empty()
    ), "Error: Hay identificadores de concepto de visita ajenos a 9201."
