import importlib.util
import sys

import polars as pl

# Importación dinámica para esquivar la restricción de Python con nombres numéricos
spec = importlib.util.spec_from_file_location("mapeo", "src/pf_depresion_omop/02_mapeo_omop.py")
mapeo = importlib.util.module_from_spec(spec)
sys.modules["mapeo"] = mapeo
spec.loader.exec_module(mapeo)


def test_fechas_logicas():
    # Preparar datos con casos límite (incluyendo 0 días de estancia)
    df_prueba = pl.DataFrame(
        {"SEXO": [1, 2], "EDAD1": [35, 42], "MES": [1, 12], "DIAS_ESTA": [5, 0]}
    )

    # Ejecutar transformación
    df_visit = mapeo.tabla_visit_occurrence(df_prueba)

    # Aserción: El inicio nunca debe ser mayor al fin temporal
    fechas_invalidas = df_visit.filter(pl.col("visit_start_date") > pl.col("visit_end_date"))

    assert len(fechas_invalidas) == 0, (
        f"Error: Se generaron {len(fechas_invalidas)} " "registros con fechas ilógicas."
    )
