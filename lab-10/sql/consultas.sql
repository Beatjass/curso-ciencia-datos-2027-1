%%sql
#Duplicados en patients
SELECT Id AS patient_id, COUNT(*) AS repeticiones
FROM patients
GROUP BY Id
HAVING COUNT(*) > 1;

%%sql
#Encuentros con fecha anerior al nacimiento
SELECT e.Id AS encounter_id, e.PATIENT, p.BIRTHDATE, e.START AS fecha_encuentro
FROM encounters e
JOIN patients p ON e.PATIENT = p.Id
WHERE e.START < p.BIRTHDATE;

%%sql
#Porcentajes de valores nulos en observations
SELECT 
    COUNT(*) AS total_observaciones,
    COUNT(*) - COUNT(VALUE) AS nulos_value,
    ROUND(100.0 * (COUNT(*) - COUNT(VALUE)) / COUNT(*), 2) AS porcentaje_nulos
FROM observations;

%%sql
#Pacientes inexistentes
SELECT COUNT(*) AS encuentros_sin_paciente
FROM encounters e
LEFT JOIN patients p ON e.PATIENT = p.Id
WHERE p.Id IS NULL;


-- Actividad 6: Quince preguntas, dificultad creciente
-- Bloque 1: Preguntas básicas
-- 1. ¿Cuántos pacientes hay? ¿Cuántos siguen vivos?
SELECT 
    COUNT(*) AS total_pacientes,
    COUNT(*) FILTER (WHERE DEATHDATE IS NULL) AS pacientes_vivos,
    COUNT(DEATHDATE) AS pacientes_fallecidos
FROM patients;

-- 2. Distribución por sexo
SELECT 
    GENDER AS sexo,
    COUNT(*) AS total_pacientes,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS porcentaje
FROM patients
GROUP BY GENDER;

-- 3. Los 10 diagnósticos más frecuentes
SELECT 
    DESCRIPTION AS diagnostico,
    CODE AS codigo_icd,
    COUNT(*) AS total_casos
FROM conditions
GROUP BY DESCRIPTION, CODE
ORDER BY total_casos DESC
LIMIT 10;

-- 4. Pacientes nacidos antes de 1960
SELECT 
    Id AS patient_id,
    FIRST AS nombre,
    LAST AS apellido,
    BIRTHDATE AS fecha_nacimiento
FROM patients
WHERE BIRTHDATE < '1960-01-01'
ORDER BY BIRTHDATE ASC;

-- 5. Encuentros por año
SELECT 
    EXTRACT(YEAR FROM START) AS anio,
    COUNT(*) AS total_encuentros
FROM encounters
GROUP BY anio
ORDER BY anio ASC;

-- Bloque 2: Preguntas intermedias
-- 6. Número medio y mediano de encuentros por paciente
WITH encuentros_por_paciente AS (
    SELECT 
        PATIENT,
        COUNT(*) AS total_encuentros
    FROM encounters
    GROUP BY PATIENT
)
SELECT 
    ROUND(AVG(total_encuentros), 2) AS promedio_encuentros,
    MEDIAN(total_encuentros) AS mediana_encuentros
FROM encuentros_por_paciente;

-- 7. Edad media al primer diagnóstico de una condición (ej. hipertensión)
WITH primer_diagnostico AS (
    SELECT 
        c.PATIENT,
        MIN(c.START) AS fecha_primer_diag
    FROM conditions c
    WHERE LOWER(c.DESCRIPTION) LIKE '%hypertension%'
    GROUP BY c.PATIENT
)
SELECT 
    ROUND(AVG(DATEDIFF('year', p.BIRTHDATE, pd.fecha_primer_diag)), 2) AS edad_media_primer_diagnostico
FROM primer_diagnostico pd
JOIN patients p ON pd.PATIENT = p.Id;

-- 8. Diagnósticos con más de 50 pacientes distintos
SELECT 
    DESCRIPTION AS diagnostico,
    COUNT(DISTINCT PATIENT) AS pacientes_unicos
FROM conditions
GROUP BY DESCRIPTION
HAVING COUNT(DISTINCT PATIENT) > 50
ORDER BY pacientes_unicos DESC;

-- 9. Distribución de un analito: Glucosa (media, mediana, p10, p90)
SELECT 
    DESCRIPTION AS analito,
    ROUND(AVG(TRY_CAST(VALUE AS DOUBLE)), 2) AS media,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY TRY_CAST(VALUE AS DOUBLE)) AS mediana,
    PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY TRY_CAST(VALUE AS DOUBLE)) AS p10,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY TRY_CAST(VALUE AS DOUBLE)) AS p90
FROM observations
WHERE LOWER(DESCRIPTION) LIKE '%glucose%'
  AND TRY_CAST(VALUE AS DOUBLE) IS NOT NULL
GROUP BY DESCRIPTION;

-- 10. Pacientes por grupo etario y sexo
WITH edad_pacientes AS (
    SELECT 
        GENDER,
        DATEDIFF('year', BIRTHDATE, COALESCE(DEATHDATE, CURRENT_DATE)) AS edad
    FROM patients
)
SELECT 
    CASE 
        WHEN edad < 18 THEN '0-17 años'
        WHEN edad BETWEEN 18 AND 39 THEN '18-39 años'
        WHEN edad BETWEEN 40 AND 64 THEN '40-64 años'
        ELSE '65+ años'
    END AS grupo_etario,
    GENDER AS sexo,
    COUNT(*) AS total_pacientes
FROM edad_pacientes
GROUP BY grupo_etario, GENDER
ORDER BY grupo_etario, GENDER;


-- Bloque 3: Preguntas avanzadas
-- 11. Pacientes con comorbilidad: diabetes e hipertensión
SELECT 
    p.Id AS patient_id,
    p.FIRST AS nombre,
    p.LAST AS apellido
FROM patients p
JOIN conditions c1 ON p.Id = c1.PATIENT AND LOWER(c1.DESCRIPTION) LIKE '%diabetes%'
JOIN conditions c2 ON p.Id = c2.PATIENT AND LOWER(c2.DESCRIPTION) LIKE '%hypertension%'
GROUP BY p.Id, p.FIRST, p.LAST;

-- 12. Pacientes con diabetes sin ninguna medición de HbA1c (Anti-Join con NOT EXISTS)
SELECT DISTINCT
    p.Id AS patient_id,
    p.FIRST AS nombre,
    p.LAST AS apellido
FROM patients p
JOIN conditions c ON p.Id = c.PATIENT
WHERE LOWER(c.DESCRIPTION) LIKE '%diabetes%'
  AND NOT EXISTS (
      SELECT 1 
      FROM observations o 
      WHERE o.PATIENT = p.Id 
        AND (LOWER(o.DESCRIPTION) LIKE '%hba1c%' OR LOWER(o.DESCRIPTION) LIKE '%hemoglobin a1c%')
  );

-- 13. Para cada paciente: su primer y su último encuentro
SELECT 
    PATIENT AS patient_id,
    MIN(START) AS primer_encuentro,
    MAX(START) AS ultimo_encuentro,
    DATEDIFF('day', MIN(START), MAX(START)) AS dias_entre_primer_y_ultimo
FROM encounters
GROUP BY PATIENT;

-- 14. Medicamento más frecuente entre los pacientes con diabetes
SELECT 
    m.DESCRIPTION AS medicamento,
    COUNT(DISTINCT m.PATIENT) AS pacientes_prescritos,
    COUNT(*) AS total_prescripciones
FROM medications m
JOIN conditions c ON m.PATIENT = c.PATIENT
WHERE LOWER(c.DESCRIPTION) LIKE '%diabetes%'
GROUP BY m.DESCRIPTION
ORDER BY total_prescripciones DESC
LIMIT 1;

-- 15. Pacientes que tuvieron un encuentro de urgencias sin diagnóstico registrado (Anti-Join)
SELECT DISTINCT
    e.PATIENT AS patient_id,
    e.Id AS encounter_id,
    e.START AS fecha_urgencia,
    e.ENCOUNTERCLASS AS clase_encuentro
FROM encounters e
LEFT JOIN conditions c ON e.Id = c.ENCOUNTER
WHERE LOWER(e.ENCOUNTERCLASS) IN ('emergency', 'urgentcare')
  AND c.CODE IS NULL;
