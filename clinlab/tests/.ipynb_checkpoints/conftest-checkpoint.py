import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def df_malicioso() -> pd.DataFrame:
    """
    Fixture que provee un DataFrame con 6 registros pero múltiples trampas clínicas.
    Un buen dato de prueba no es realista, está lleno de casos límite.
    """
    data = {
        "Id": ["P1", "P2", "P3", "P1", "P4", "P5"],
        "BIRTHDATE": [
            "1980-05-15",  #P1: Normal
            "2015-08-20",  #P2: Menor de edad
            "1992-11-10",  #P3: Normal, pero con NaN
            "1980-05-15",  #P1: Duplicado (mismo Id)
            "2028-01-01",  #P4: Nacerá en 2028
            "1846-01-01"   #P5: Nació hace 180 años
        ],
        "DEATHDATE": [
            None,          #P1: Vivo
            None,          #P2: Vivo
            None,          #P3: Vivo
            None,          #P1: Vivo
            "2020-01-01",  #P4: Todavía no nace y ya murió en 2020
            None           #P5: Vivo
        ],
        "HbA1c": [
            5.5,           #Normal
            4.8,           #Normal
            np.nan,        #Faltante (NaN)
            6.2,           #Diferente medición para el duplicado
            5.1,           #Normal
            0.0            #Valor fisiológicamente imposible
        ]
    }
    
    df = pd.DataFrame(data)
    
    #Convertimos las fechas a datetime para que se comporten como datos reales
    df["BIRTHDATE"] = pd.to_datetime(df["BIRTHDATE"])
    df["DEATHDATE"] = pd.to_datetime(df["DEATHDATE"])
    
    return df