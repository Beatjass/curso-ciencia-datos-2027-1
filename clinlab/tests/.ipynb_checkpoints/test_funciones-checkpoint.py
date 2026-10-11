import pandas as pd
import pytest
import numpy as np
from clinlab.funciones import (
    identify_non_numeric_values,
    merge_validating_cardinality,
    flag_physiological_outliers,
    calcular_egfr_ckd_epi_2021
)

#Actividad 3
#1. Caso normal de valores no numéricos
def test_identify_non_numeric_values_detecta_cualificadores_de_texto() -> None:
    series_prueba = pd.Series(["14.5", "Negative (qualifier value)", "12.0", None])
    resultado = identify_non_numeric_values(series_prueba)

    assert resultado.iloc[0] is False or resultado.iloc[0] == False
    assert resultado.iloc[1] is True or resultado.iloc[1] == True
    assert resultado.iloc[2] is False or resultado.iloc[2] == False
    assert resultado.iloc[3] is False or resultado.iloc[3] == False


# 2. Caso normal con comparación de flotantes usando pytest.approx
def test_flag_physiological_outliers_identifica_valores_fuera_de_rango() -> None:
    # Hemoglobina en g/dL
    mediciones_hgb = pd.Series([14.5, 3.2, 28.1])
    outliers = flag_physiological_outliers(mediciones_hgb, min_val=5.0, max_val=25.0)

    #Verificación pytest.approx
    val_bajo = mediciones_hgb.iloc[1]
    assert val_bajo == pytest.approx(3.2)

    assert outliers.iloc[0] is False or outliers.iloc[0] == False
    assert outliers.iloc[1] is True or outliers.iloc[1] == True
    assert outliers.iloc[2] is True or outliers.iloc[2] == True


#3. Caso de error usando pytest.raises
def test_merge_validating_cardinality_lanza_error_ante_duplicados_inesperados() -> None:
    df_obs = pd.DataFrame({"OBS_ID": [1, 2], "ENCOUNTER": ["E1", "E2"]})
    #Duplicado en la tabla derecha que viola la cardinalidad m:1
    df_enc_duplicado = pd.DataFrame({"Id": ["E1", "E1", "E2"]})

    with pytest.raises(pd.errors.MergeError):
        merge_validating_cardinality(
            left_df=df_obs,
            right_df=df_enc_duplicado,
            left_on="ENCOUNTER",
            right_on="Id",
            validate_rule="m:1",
        )

#Actividad 5:
#def test_fixture_carga_correctamente(df_malicioso: pd.DataFrame) -> None:
#    """Verifica que Pytest inyecte correctamente el dataframe definido en conftest.py."""
#    assert len(df_malicioso) == 6
#    assert df_malicioso["Id"].duplicated().sum() == 1
#Lo deje así porque no se especifica si se tiene que implementar en el laboratorio

#Actividad 6:
@pytest.mark.parametrize(
    "scr, edad, sexo, egfr_esperado",
    [
        #Combinaciones verificadas en la calculadora oficial de la NKF/MDCalc
        (0.9, 40, "M", 110.7),  #1. Caso normal hombre adulto
        (0.8, 40, "F", 95.8),   #2. Caso normal mujer adulta
        (2.5, 80, "M", 23.3),   #3. ERC avanzada (estadio 4)
        (0.5, 20, "F", 138.8),  #4. Creatinina muy baja (hiperfiltración)
        (5.0, 60, "M", 12.5),   #5. ERC estadio 5 (falla renal inminente)
        (1.2, 75, "F", 47.9),   #6. ERC moderada en mujer mayor
        (0.6, 30, "M", 135.5),  #7. Creatinina baja en hombre joven
        (1.5, 55, "F", 41.5),   #8. ERC estadio 3b en mujer adulta
    ]
)
def test_calcular_egfr_ckd_epi_2021_tabla_clinica(scr: float, edad: int, sexo: str, egfr_esperado: float) -> None:
    """
    Valida el cálculo de eGFR contra los valores de la calculadora oficial de 
    la National Kidney Foundation (CKD-EPI 2021 sin variable de raza).
    
    Referencia clínica: https://www.kidney.org/professionals/kdoqi/gfr_calculator
    Se toleran desviaciones de 0.5 mL/min/1.73m2 debidas al redondeo.
    """
    resultado = calcular_egfr_ckd_epi_2021(scr_mg_dl=scr, edad_anios=edad, sexo=sexo)
    
    assert resultado == pytest.approx(egfr_esperado, abs=0.5)

#Actividad 7:
def test_dataframe_vacio_devuelve_vacio_sin_tronar() -> None:
    #Motivación: Tuberías que colapsaban con KeyError al recibir tablas que quedaban vacías tras un filtrado previo.
    serie_vacia = pd.Series([], dtype=float)
    resultado = flag_physiological_outliers(serie_vacia, min_val=0.0, max_val=100.0)
    assert len(resultado) == 0
    assert resultado.empty


def test_columna_entera_nan_manejada_correctamente() -> None:
    #Motivación: Variables clínicas enteras (como ciertas pruebas de laboratorio) tenían 100% de nulos en algunos hospitales.
    serie_nula = pd.Series([np.nan, np.nan, None])
    resultado = flag_physiological_outliers(serie_nula, min_val=0.0, max_val=100.0)
    #Nuestra función usa notna(), por lo que los NaNs no deben ser marcados falsamente como outliers fuera de rango.
    assert not resultado.any()


def test_join_no_multiplica_filas_con_person_id_duplicado() -> None:
    #Motivación: Los left joins ciegos multiplicaban las filas al toparse con pacientes duplicados, inflando métricas.
    df_pacientes = pd.DataFrame({"person_id": [1, 2]})
    df_visitas = pd.DataFrame({"person_id": [1, 1, 2], "diagnostico": ["A", "B", "C"]})
    
    #Comprobación
    with pytest.raises(pd.errors.MergeError):
        merge_validating_cardinality(
            left_df=df_pacientes, 
            right_df=df_visitas, 
            left_on="person_id", 
            right_on="person_id", 
            validate_rule="1:1"
        )


def test_valor_centinela_detectado_como_outlier() -> None:
    #Motivación: Sistemas antiguos exportaban datos nulos como edad 180 o HbA1c de 0.0.
    serie_centinela = pd.Series([5.5, 0.0, 180.0])
    #Suponiendo un rango normal/posible de HbA1c entre 4.0 y 20.0
    outliers = flag_physiological_outliers(serie_centinela, min_val=4.0, max_val=20.0)
    
    assert outliers.iloc[0] is False #5.5 es normal
    assert outliers.iloc[1] is True  #0.0 detectado
    assert outliers.iloc[2] is True  #180.0 detectado