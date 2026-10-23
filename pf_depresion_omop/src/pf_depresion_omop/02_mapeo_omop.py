import polars as pl


# Crear tabla person
def tabla_person(df_limpio: pl.DataFrame) -> pl.DataFrame:
    """Mapea los datos demográficos a la tabla person de OMOP CDM."""
    person = df_limpio.select(
        [
            # Llave primaria secuencial
            pl.int_range(1, pl.len() + 1).alias("person_id"),
            # Mapeo de género según catálogos DGIS (1=Hombre, 2=Mujer) a OMOP
            pl.when(pl.col("SEXO") == 1)
            .then(8507)
            .when(pl.col("SEXO") == 2)
            .then(8532)
            .otherwise(0)
            .alias("gender_concept_id"),
            # Cálculo de año de nacimiento (Año del dataset 2024 - Edad)
            (2024 - pl.col("EDAD1")).alias("year_of_birth"),
            # Campos obligatorios sin información equivalente en la fuente
            pl.lit(0).alias("race_concept_id"),
            pl.lit(0).alias("ethnicity_concept_id"),
            # Trazabilidad del dato original
            pl.col("SEXO").cast(pl.Utf8).alias("gender_source_value"),
        ]
    )

    return person


# Crear tabla visit_occurrence
def tabla_visit_occurrence(df_limpio: pl.DataFrame) -> pl.DataFrame:
    """Imputa fechas y genera la tabla visit_occurrence de OMOP-CDM"""
    visit = (
        df_limpio.with_columns(
            [
                # Asignamos el mismo person_id secuencial para mantener la relación 1:1
                pl.int_range(1, pl.len() + 1).alias("person_id"),
                # Fijamos la fecha de egreso al día 28 del mes reportado
                pl.date(2024, pl.col("MES"), 28).alias("visit_end_date"),
            ]
        )
        .with_columns(
            [
                # Calculamos el ingreso restando los días de estancia
                (pl.col("visit_end_date") - pl.duration(days=pl.col("DIAS_ESTA"))).alias(
                    "visit_start_date"
                )
            ]
        )
        .select(
            [
                pl.int_range(1, pl.len() + 1).alias("visit_occurrence_id"),
                pl.col("person_id"),
                pl.lit(9201).alias("visit_concept_id"),  # 9201 = Inpatient Visit (Hospitalización)
                pl.col("visit_start_date"),
                pl.col("visit_end_date"),
                pl.lit(32009).alias("visit_type_concept_id"),  # 32009 = EHR encounter record
                pl.col("DIAS_ESTA").cast(pl.Utf8).alias("visit_source_value"),
            ]
        )
    )

    return visit


# Tabla condition_occurrence
def tabla_condition_occurrence(df_limpio: pl.DataFrame) -> pl.DataFrame:
    """Genera la tabla condition_occurrence con los diagnósticos de OMOP-CDM."""
    condition = (
        df_limpio.with_columns(
            [
                pl.int_range(1, pl.len() + 1).alias("person_id"),
                pl.date(2024, pl.col("MES"), 28).alias("visit_end_date"),
            ]
        )
        .with_columns(
            [
                (pl.col("visit_end_date") - pl.duration(days=pl.col("DIAS_ESTA"))).alias(
                    "condition_start_date"
                )
            ]
        )
        .select(
            [
                pl.int_range(1, pl.len() + 1).alias("condition_occurrence_id"),
                pl.col("person_id"),
                pl.lit(0).alias("condition_concept_id"),
                pl.col("condition_start_date"),
                pl.lit(32020).alias("condition_type_concept_id"),
                pl.col("AFECPRIN4").cast(pl.Utf8).alias("condition_source_value"),
            ]
        )
    )

    return condition


if __name__ == "__main__":
    df_raw = pl.read_csv("data/Egresos_Sectorial_2024.txt", separator="|")

    df_person = tabla_person(df_raw)
    df_visit = tabla_visit_occurrence(df_raw)
    df_condition = tabla_condition_occurrence(df_raw)

    df_person.write_parquet("data/person.parquet")
    df_visit.write_parquet("data/visit_occurrence.parquet")
    df_condition.write_parquet("data/condition_occurrence.parquet")

    print("Tablas OMOP guardadas exitosamente en la carpeta data/")
