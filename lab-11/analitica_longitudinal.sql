-- -------------------------------------------------------------------------------
-- Actividad 1: De anidado a legible (Refactorización a CTEs)
-- Pregunta clínica: ¿Qué pacientes diagnosticados con diabetes no tienen un registro de prueba de HbA1c?

WITH pacientes_diabeticos AS (
    SELECT DISTINCT p.Id, p.FIRST, p.LAST
    FROM patients p
    JOIN conditions c ON p.Id = c.PATIENT
    WHERE LOWER(c.DESCRIPTION) LIKE '%diabetes%'
),
mediciones_hba1c AS (
    SELECT DISTINCT PATIENT 
    FROM observations 
    WHERE LOWER(DESCRIPTION) LIKE '%hba1c%' OR LOWER(DESCRIPTION) LIKE '%hemoglobin a1c%'
)
SELECT pd.*
FROM pacientes_diabeticos pd
LEFT JOIN mediciones_hba1c mh ON pd.Id = mh.PATIENT
WHERE mh.PATIENT IS NULL;


-- Pregunta clínica: ¿Cuál es el promedio histórico de días de seguimiento clínico por paciente?
WITH historia_pacientes AS (
    SELECT 
        PATIENT,
        DATEDIFF('day', MIN(START), MAX(START)) AS dias_seguimiento
    FROM encounters
    GROUP BY PATIENT
)
SELECT 
    ROUND(AVG(dias_seguimiento), 2) AS promedio_dias_historia
FROM historia_pacientes;


-- -------------------------------------------------------------------------------
-- Actividad 3: Primera y última visita por paciente
-- Pregunta clínica: Para cada paciente, ¿cuándo fue su primera y última visita, y cuántas tuvo en total?

-- Solución GROUP BY:
SELECT 
    PATIENT,
    MIN(START) AS primera_visita,
    MAX(START) AS ultima_visita,
    COUNT(Id) AS total_visitas
FROM encounters
GROUP BY PATIENT
ORDER BY PATIENT;

-- Solución con Window Functions:
SELECT DISTINCT
        PATIENT,
        FIRST_VALUE(START) OVER (PARTITION BY PATIENT ORDER BY START) AS primera_visita,
        -- LA TRAMPA: Si no ponemos la ventana completa, LAST_VALUE devuelve la fila actual
        LAST_VALUE(START) OVER (
            PARTITION BY PATIENT 
            ORDER BY START 
            RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS ultima_visita,
        COUNT(Id) OVER (PARTITION BY PATIENT) AS total_visitas
    FROM encounters
    ORDER BY PATIENT;


-- -------------------------------------------------------------------------------
-- Actividad 4: Días entre visitas consecutivas (LAG)
-- Pregunta clínica: ¿Cuántos días transcurren típicamente entre una visita y la siguiente para un mismo paciente?

-- Días entre visitas
WITH visitas_con_lag AS (
    SELECT 
        PATIENT,
        START AS fecha_visita,
        LAG(START) OVER (PARTITION BY PATIENT ORDER BY START) AS fecha_anterior,
        DATEDIFF('day', 
                    LAG(START) OVER (PARTITION BY PATIENT ORDER BY START), 
                    START) AS dias_transcurridos
    FROM encounters
)
SELECT * 
FROM visitas_con_lag
ORDER BY PATIENT, fecha_visita;

-- Mediana
WITH visitas_con_lag AS (
    SELECT 
        DATEDIFF('day', 
                 LAG(START) OVER (PARTITION BY PATIENT ORDER BY START), 
                 START) AS dias_transcurridos
    FROM encounters
)
SELECT MEDIAN(dias_transcurridos) AS mediana_dias
FROM visitas_con_lag;


-- -------------------------------------------------------------------------------
-- Actividad 5: Readmisión a 30 días
-- Pregunta clínica: ¿Cuál es la tasa de readmisión hospitalaria a 30 días (ingresos 'inpatient')?

WITH ingresos AS (
    SELECT 
        PATIENT,
        START AS fecha_ingreso,
        STOP AS fecha_alta
    FROM encounters
    WHERE LOWER(ENCOUNTERCLASS) = 'inpatient'
),
altas_con_futuro AS (
    SELECT 
        PATIENT,
        fecha_ingreso,
        fecha_alta,
        LEAD(fecha_ingreso) OVER (PARTITION BY PATIENT ORDER BY fecha_ingreso) AS siguiente_ingreso
    FROM ingresos
),
evaluacion_30d AS (
    SELECT 
        *,
        DATEDIFF('day', fecha_alta, siguiente_ingreso) AS dias_para_reingreso,
        CASE 
            WHEN DATEDIFF('day', fecha_alta, siguiente_ingreso) BETWEEN 0 AND 30 THEN 1 
            ELSE 0 
        END AS readmision_30d
    FROM altas_con_futuro
)
SELECT 
    COUNT(*) AS altas_elegibles,
    SUM(readmision_30d) AS total_readmisiones,
    ROUND((SUM(readmision_30d) * 100.0) / COUNT(*), 2) AS tasa_readmision_pct
FROM evaluacion_30d;


-- -------------------------------------------------------------------------------
-- Actividad 6: Episodios de tratamiento (Gaps and Islands)
-- Pregunta clínica: ¿Cuáles son los periodos continuos de tratamiento con Simvastatina (permitiendo un gap de 30 días)?

WITH med_data AS (
    SELECT 
        PATIENT, 
        START, 
        COALESCE(STOP, CURRENT_DATE) AS STOP
    FROM medications
    WHERE LOWER(DESCRIPTION) LIKE '%simvastatin%'
),
lagged AS (
    SELECT 
        PATIENT, 
        START, 
        STOP,
        LAG(STOP) OVER (PARTITION BY PATIENT ORDER BY START) AS prev_stop
    FROM med_data
),
islands AS (
    SELECT 
        PATIENT, 
        START, 
        STOP,
        CASE 
            WHEN prev_stop IS NULL 
                 OR DATEDIFF('day', prev_stop, START) > 30 THEN 1 
            ELSE 0 
        END AS is_new_episode
    FROM lagged
),
episodes_grouped AS (
    SELECT 
        PATIENT, 
        START, 
        STOP,
        SUM(is_new_episode) OVER (PARTITION BY PATIENT ORDER BY START) AS episode_id
    FROM islands
)
SELECT 
    PATIENT,
    episode_id,
    MIN(START) AS episode_start,
    MAX(STOP) AS episode_end,
    DATEDIFF('day', MIN(START), MAX(STOP)) AS duration_days
FROM episodes_grouped
GROUP BY PATIENT, episode_id
ORDER BY PATIENT, episode_start;


-- -------------------------------------------------------------------------------
-- Actividad 7: Deduplicar con ROW_NUMBER
-- Pregunta clínica: ¿Cuál es el valor basal más reciente de cada prueba de laboratorio (analito) por paciente?

WITH observaciones_rankeadas AS (
    SELECT 
        PATIENT,
        DATE,
        DESCRIPTION,
        VALUE,
        UNITS,
        ROW_NUMBER() OVER (
            PARTITION BY PATIENT, DESCRIPTION 
            ORDER BY DATE DESC
        ) AS rn
    FROM observations
)
SELECT PATIENT, DATE, DESCRIPTION, VALUE, UNITS
FROM observaciones_rankeadas
WHERE rn = 1
ORDER BY PATIENT, DATE DESC;


-- -------------------------------------------------------------------------------
-- Actividad 8: Media móvil y frames
-- Pregunta clínica: ¿Cómo cambia el peso corporal de un paciente suavizando los datos con una media móvil de 3 visitas vs una media acumulada histórica?

WITH paciente_ejemplo AS (
    SELECT PATIENT
    FROM observations
    WHERE DESCRIPTION = 'Body Weight'
    GROUP BY PATIENT
    HAVING COUNT(*) >= 5
    LIMIT 1
)
SELECT 
    DATE::DATE AS fecha_medicion,
    VALUE::FLOAT AS peso_actual,
    -- Acumulado
    ROUND(AVG(VALUE::FLOAT) OVER (
        PARTITION BY PATIENT 
        ORDER BY DATE
    ), 2) AS media_acumulada,
    -- Media móvil de 3
    ROUND(AVG(VALUE::FLOAT) OVER (
        PARTITION BY PATIENT 
        ORDER BY DATE 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS media_movil_3
FROM observations
WHERE DESCRIPTION = 'Body Weight' 
  AND PATIENT = (SELECT PATIENT FROM paciente_ejemplo)
ORDER BY fecha_medicion;


-- -------------------------------------------------------------------------------
-- Actividad 9: El valor más cercano a una fecha índice
-- Pregunta clínica: ¿Cuál es el valor de HbA1c más cercano antes del primer diagnóstico de diabetes (ventana de 0 a 90 días)?

WITH fecha_indice AS (
    SELECT 
        PATIENT,
        MIN(START) AS fecha_diagnostico
    FROM conditions
    WHERE LOWER(DESCRIPTION) LIKE '%diabetes%'
    GROUP BY PATIENT
),
mediciones_ventana AS (
    SELECT 
        fi.PATIENT,
        fi.fecha_diagnostico,
        o.DATE AS fecha_laboratorio,
        o.DESCRIPTION AS analito,
        o.VALUE AS resultado,
        DATEDIFF('day', o.DATE, fi.fecha_diagnostico) AS dias_antes_diagnostico
    FROM fecha_indice fi
    JOIN observations o ON fi.PATIENT = o.PATIENT
    WHERE (LOWER(o.DESCRIPTION) LIKE '%hba1c%' OR LOWER(o.DESCRIPTION) LIKE '%hemoglobin a1c%')
      AND DATEDIFF('day', o.DATE, fi.fecha_diagnostico) BETWEEN 0 AND 90
),
lab_mas_cercano AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY PATIENT 
            ORDER BY dias_antes_diagnostico ASC
        ) AS rn
    FROM mediciones_ventana
)
SELECT 
    PATIENT,
    fecha_diagnostico,
    fecha_laboratorio,
    analito,
    resultado,
    dias_antes_diagnostico
FROM lab_mas_cercano
WHERE rn = 1
ORDER BY dias_antes_diagnostico ASC;