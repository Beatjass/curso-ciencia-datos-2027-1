Tabla de atrición
| Paso | Criterio de inclusión/exclusión | N (Retenidos) | Excluidos en este paso |
| 1 | Total de egresos DGIS 2024 | 5,877,537 | 0 |
| 2 | Filtro diagnóstico: Inclusión códigos F32 y F33 | 10,972 | - 5,866,565 |
| 3 | Filtro de calidad (edad): CLAVE_EDAD válida y EDAD1 < 120 | 10,926 | - 46 |
| 4 | Filtro de calidad (fechas y sexo): MES (1-12) y SEXO (1, 2) | 10,926 | - 0 |
| 5 | Filtro clínico (estancia): Estancia hospitalaria entre 0 y 30 días | 10,671 | - 255 |
| Final | Cohorte analítica final (OMOP CDM) | 10,671 | Retención: 97.26% |

> **Nota metodológica:** Los 255 registros excluidos en el paso 5 corresponden a estancias prolongadas (> 30 días), incluyendo los casos extremos con estancias superiores a 60 años. Las estancias de 0 días (altas el mismo día del ingreso) se conservan como clínicamente válidas.
