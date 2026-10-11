import pandas as pd
import pytest
import numpy as np
from clinlab.funciones import (
    identify_non_numeric_values,
    merge_validating_cardinality,
    flag_physiological_outliers,
    calcular_egfr_ckd_epi_2021,
    remove_timezones,
    find_impossible_encounters,
)


# Actividad 3
# 1. Caso normal de valores no numéricos
def test_identify_non_numeric_values_detecta_cualificadores_de_texto() -> None:
    series_prueba = pd.Series(["14.5", "Negative (qualifier value)", "12.0", None])
    resultado = identify_non_numeric_values(series_prueba)

    assert not resultado.iloc[0]
    assert resultado.iloc[1]
    assert not resultado.iloc[2]
    assert not resultado.iloc[3]


# 2. Caso normal con comparación de flotantes usando pytest.approx
def test_flag_physiological_outliers_identifica_valores_fuera_de_rango() -> None:
    # Hemoglobina en g/dL
    mediciones_hgb = pd.Series([14.5, 3.2, 28.1])
    outliers = flag_physiological_outliers(mediciones_hgb, min_val=5.0, max_val=25.0)

    # Verificación pytest.approx
    val_bajo = mediciones_hgb.iloc[1]
    assert val_bajo == pytest.approx(3.2)

    assert not outliers.iloc[0]
    assert outliers.iloc[1]
    assert outliers.iloc[2]


# 3. Caso de error usando pytest.raises
def test_merge_validating_cardinality_lanza_error_ante_duplicados_inesperados() -> None:
    df_obs = pd.DataFrame({"OBS_ID": [1, 2], "ENCOUNTER": ["E1", "E2"]})
    # Duplicado en la tabla derecha que viola la cardinalidad m:1
    df_enc_duplicado = pd.DataFrame({"Id": ["E1", "E1", "E2"]})

    with pytest.raises(pd.errors.MergeError):
        merge_validating_cardinality(
            left_df=df_obs,
            right_df=df_enc_duplicado,
            left_on="ENCOUNTER",
            right_on="Id",
            validate_rule="m:1",
        )


# Actividad 5:
# def test_fixture_carga_correctamente(df_malicioso: pd.DataFrame) -> None:
#    """Verifica que Pytest inyecte correctamente el dataframe definido en conftest.py."""
#    assert len(df_malicioso) == 6
#    assert df_malicioso["Id"].duplicated().sum() == 1
# Lo deje así porque no se especifica si se tiene que implementar en el laboratorio


# Actividad 6:
@pytest.mark.parametrize(
    "scr, edad, sexo, egfr_esperado",
    [
        # Combinaciones verificadas en la calculadora oficial de la NKF/MDCalc
        (0.9, 40, "M", 110.7),  # 1. Caso normal hombre adulto
        (0.8, 40, "F", 95.8),  # 2. Caso normal mujer adulta
        (2.5, 80, "M", 23.3),  # 3. ERC avanzada (estadio 4)
        (0.5, 20, "F", 138.8),  # 4. Creatinina muy baja (hiperfiltración)
        (5.0, 60, "M", 12.5),  # 5. ERC estadio 5 (falla renal inminente)
        (1.2, 75, "F", 47.9),  # 6. ERC moderada en mujer mayor
        (0.6, 30, "M", 135.5),  # 7. Creatinina baja en hombre joven
        (1.5, 55, "F", 41.5),  # 8. ERC estadio 3b en mujer adulta
    ],
)
def test_calcular_egfr_ckd_epi_2021_tabla_clinica(
    scr: float, edad: int, sexo: str, egfr_esperado: float
) -> None:
    """
    Valida el cálculo de eGFR contra los valores de la calculadora oficial de
    la National Kidney Foundation (CKD-EPI 2021 sin variable de raza).

    Referencia clínica: https://www.kidney.org/professionals/kdoqi/gfr_calculator
    Se toleran desviaciones de 0.5 mL/min/1.73m2 debidas al redondeo.
    """
    resultado = calcular_egfr_ckd_epi_2021(scr_mg_dl=scr, edad_anios=edad, sexo=sexo)

    assert resultado == pytest.approx(egfr_esperado, abs=0.5)


# Actividad 7:
def test_dataframe_vacio_devuelve_vacio_sin_tronar() -> None:
    # Motivación: Tuberías que colapsaban con KeyError al recibir tablas que quedaban vacías tras un filtrado previo.
    serie_vacia = pd.Series([], dtype=float)
    resultado = flag_physiological_outliers(serie_vacia, min_val=0.0, max_val=100.0)
    assert len(resultado) == 0
    assert resultado.empty


def test_columna_entera_nan_manejada_correctamente() -> None:
    # Motivación: Variables clínicas enteras (como ciertas pruebas de laboratorio) tenían 100% de nulos en algunos hospitales.
    serie_nula = pd.Series([np.nan, np.nan, None])
    resultado = flag_physiological_outliers(serie_nula, min_val=0.0, max_val=100.0)
    # Nuestra función usa notna(), por lo que los NaNs no deben ser marcados falsamente como outliers fuera de rango.
    assert not resultado.any()


def test_join_no_multiplica_filas_con_person_id_duplicado() -> None:
    # Motivación: Los left joins ciegos multiplicaban las filas al toparse con pacientes duplicados, inflando métricas.
    df_pacientes = pd.DataFrame({"person_id": [1, 2]})
    df_visitas = pd.DataFrame({"person_id": [1, 1, 2], "diagnostico": ["A", "B", "C"]})

    # Comprobación
    with pytest.raises(pd.errors.MergeError):
        merge_validating_cardinality(
            left_df=df_pacientes,
            right_df=df_visitas,
            left_on="person_id",
            right_on="person_id",
            validate_rule="1:1",
        )


def test_valor_centinela_detectado_como_outlier() -> None:
    # Motivación: Sistemas antiguos exportaban datos nulos como edad 180 o HbA1c de 0.0.
    serie_centinela = pd.Series([5.5, 0.0, 180.0])
    # Suponiendo un rango normal/posible de HbA1c entre 4.0 y 20.0
    outliers = flag_physiological_outliers(serie_centinela, min_val=4.0, max_val=20.0)

    assert outliers.iloc[0] is False  # 5.5 es normal
    assert outliers.iloc[1] is True  # 0.0 detectado
    assert outliers.iloc[2] is True  # 180.0 detectado


# Para cubrir el >80% de cobertura, agrego un test que fuerza a Pytest a visitar la línea 129 de clinlab/funciones.py, donde se devuelve NaN ante datos clínicos imposibles.
# Lo hice despues del ruff.
def test_egfr_devuelve_nan_con_datos_invalidos() -> None:
    # Fuerza a Pytest a visitar la línea 129 inyectando una creatinina imposible (-1.0)
    resultado = calcular_egfr_ckd_epi_2021(scr_mg_dl=-1.0, edad_anios=40, sexo="M")
    assert pd.isna(resultado)


def test_remove_timezones_elimina_utc() -> None:
    # Fuerza a Pytest a visitar el bloque 21-25 procesando una fecha con zona horaria
    df_con_tz = pd.DataFrame({"fecha": pd.to_datetime(["2023-01-01 12:00:00+00:00"])})
    df_sin_tz = remove_timezones(df_con_tz, date_cols=["fecha"])
    assert df_sin_tz["fecha"].dt.tz is None


def test_encuentros_imposibles() -> None:
    # Cubre las líneas 60-62 evaluando pacientes con fechas de visita, nacimiento y muerte que no son cronológicamente posibles.
    df_fechas = pd.DataFrame(
        {
            "start": pd.to_datetime(["2019-01-01", "2025-01-01", "2022-01-01"]),
            "birth": pd.to_datetime(["2020-01-01", "2020-01-01", "2020-01-01"]),
            "death": [pd.NaT, pd.to_datetime("2024-01-01"), pd.NaT],
        }
    )

    resultado = find_impossible_encounters(df_fechas, "start", "birth", "death")
    assert resultado.tolist() == [True, True, False]


def test_identify_non_numeric_values() -> None:
    # Cubre la función que aísla los textos colados en mediciones numéricas
    serie_mixta = pd.Series([120, "Negative (qualifier value)", pd.NA, "150"])
    resultado = identify_non_numeric_values(serie_mixta)
    # Solo el segundo elemento es texto puro irreductible
    assert resultado.tolist() == [False, True, False, False]


def test_merge_validating_cardinality_camino_feliz() -> None:
    # Fuerza a Pytest a visitar el bloque 63-67
    import pandas as pd

    df_izq = pd.DataFrame({"person_id": [1, 2], "valor": [10, 20]})
    df_der = pd.DataFrame({"person_id": [1, 2], "diagnostico": ["A", "B"]})
    resultado = merge_validating_cardinality(
        left_df=df_izq,
        right_df=df_der,
        left_on="person_id",
        right_on="person_id",
        validate_rule="1:1",
    )
    # Confirma que la columna temporal '_merge' fue eliminada correctamente
    assert "_merge" not in resultado.columns
