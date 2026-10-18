from typing import Literal
import pandas as pd


def remove_timezones(df: pd.DataFrame, date_cols: list[str]) -> pd.DataFrame:
    """
    Elimina la zona horaria (UTC) de columnas datetime especificadas.

    Útil para estandarizar fechas de eventos clínicos (medidas en formato
    estándar AAAA-MM-DD HH:MM:SS) y permitir comparaciones directas de tiempo
    sin conflictos de offset horario.

    Args:
        df (pd.DataFrame): DataFrame original.
        date_cols (list[str]): Nombres de las columnas con fechas.

    Returns:
        pd.DataFrame: DataFrame con las zonas horarias eliminadas.
    """
    df_clean = df.copy()
    for col in date_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], utc=True).dt.tz_localize(None)
    return df_clean


def identify_non_numeric_values(series: pd.Series) -> pd.Series:
    """
    Detecta valores en una serie clínica que no se pueden convertir a número y no son nulos.

    Ideal para aislar calificadores de texto (ej. 'Negative (qualifier value)')
    en mediciones cuantitativas que rigurosamente deberían estar en unidades
    específicas, como g/dL (Hemoglobina) o mmHg (Presión arterial).

    Args:
        series (pd.Series): Serie de pandas con los valores a evaluar.

    Returns:
        pd.Series: Máscara booleana (True para valores que son texto puro).
    """
    values_numeric = pd.to_numeric(series, errors="coerce")
    es_nulo_original = series.isnull()
    return values_numeric.isnull() & (~es_nulo_original)


def find_impossible_encounters(
    df_merged: pd.DataFrame, start_col: str, birth_col: str, death_col: str
) -> pd.Series:
    """
    Detecta encuentros registrados antes de nacer o después de morir.

    Las comparaciones cronológicas se realizan a nivel de días exactos (fecha).

    Args:
        df_merged (pd.DataFrame): DataFrame con las fechas combinadas.
        start_col (str): Columna de inicio del encuentro (fecha).
        birth_col (str): Columna de nacimiento (fecha).
        death_col (str): Columna de defunción (fecha).

    Returns:
        pd.Series: Máscara booleana (True para encuentros cronológicamente imposibles).
    """
    antes_nacimiento = df_merged[start_col] < df_merged[birth_col]
    post_muerte = df_merged[death_col].notnull() & (
        df_merged[start_col] > df_merged[death_col]
    )
    return antes_nacimiento | post_muerte


def merge_validating_cardinality(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    left_on: str,
    right_on: str,
    validate_rule: Literal[
        "one_to_one",
        "1:1",
        "one_to_many",
        "1:m",
        "many_to_one",
        "m:1",
        "many_to_many",
        "m:m",
    ] = "m:1",
) -> pd.DataFrame:
    """
    Une dos tablas validando la cardinalidad estricta y limpiando columnas auxiliares.

    Args:
        left_df (pd.DataFrame): DataFrame izquierdo (ej. observaciones).
        right_df (pd.DataFrame): DataFrame derecho (ej. encuentros o pacientes).
        left_on (str): Llave de cruce izquierda.
        right_on (str): Llave de cruce derecha.
        validate_rule (str): Regla de cardinalidad de pandas (ej. 'm:1', '1:1').

    Returns:
        pd.DataFrame: DataFrame resultante del cruce.
    """
    df_merged = left_df.merge(
        right_df,
        left_on=left_on,
        right_on=right_on,
        how="left",
        validate=validate_rule,
        indicator=True,
        suffixes=("", "_aux"),
    )
    if "_merge" in df_merged.columns:
        df_merged = df_merged.drop(columns=["_merge"])
    return df_merged


def flag_physiological_outliers(
    series: pd.Series, min_val: float, max_val: float
) -> pd.Series:
    """
    Identifica valores numéricos que caen fuera de un rango biológico plausible.

    IMPORTANTE: Los límites `min_val` y `max_val` deben corresponder a la unidad
    clínica correcta del analito. Por ejemplo:
    - Hemoglobina: 5.0 a 25.0 (unidades en g/dL).
    - Frecuencia Cardíaca: 0.0 a 300.0 (unidades en latidos por minuto o lpm).
    - Edad: 0.0 a 120.0 (unidades en años).

    Args:
        series (pd.Series): Serie con los valores numéricos a evaluar.
        min_val (float): Límite inferior biológicamente posible (en la unidad correspondiente).
        max_val (float): Límite superior biológicamente posible (en la unidad correspondiente).

    Returns:
        pd.Series: Máscara booleana (True para valores fuera del rango fisiológico).
    """
    numeric_series = pd.to_numeric(series, errors="coerce")
    return ~numeric_series.between(min_val, max_val) & numeric_series.notna()


def calcular_egfr_ckd_epi_2021(scr_mg_dl: float, edad_anios: int, sexo: str) -> float:
    """
    Calcula la tasa de filtración glomerular estimada (eGFR) utilizando la
    ecuación CKD-EPI 2021.

    Args:
        scr_mg_dl (float): Creatinina sérica en mg/dL.
        edad_anios (int): Edad del paciente en años.
        sexo (str): Sexo biológico ('M' o 'F').

    Returns:
        float: eGFR en mL/min/1.73 m². Si los datos son inválidos, devuelve NaN.
    """
    if (
        pd.isna(scr_mg_dl)
        or scr_mg_dl <= 0
        or edad_anios <= 0
        or sexo not in ["M", "F"]
    ):
        return float("nan")

    is_female = sexo == "F"
    kappa = 0.7 if is_female else 0.9
    alpha = -0.241 if is_female else -0.302

    scr_kappa = scr_mg_dl / kappa
    min_term = min(scr_kappa, 1.0) ** alpha
    max_term = max(scr_kappa, 1.0) ** -1.200
    age_term = 0.9938**edad_anios
    sex_multiplier = 1.012 if is_female else 1.0

    egfr = 142 * min_term * max_term * age_term * sex_multiplier
    return egfr
