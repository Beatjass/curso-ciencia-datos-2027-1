-- =================================================================
-- Script: 10_cohorte_depresion.sql
-- Objetivo: Extracción, control de calidad y caracterización de la 
-- cohorte de depresión (CIE-10: F32 y F33) en el modelo OMOP CDM.
-- =================================================================

WITH CohorteDepresion AS (
    SELECT 
        p.person_id,
        p.gender_concept_id,
        p.year_of_birth,
        v.visit_start_date,
        v.visit_end_date,
        -- Cálculo de la duración de la estancia en días
        (v.visit_end_date - v.visit_start_date) AS dias_estancia,
        c.condition_source_value AS codigo_cie10
    FROM condition_occurrence c
    JOIN person p ON c.person_id = p.person_id
    -- Vinculamos visit_occurrence mediante person_id y la fecha de inicio del evento
    JOIN visit_occurrence v ON c.person_id = v.person_id AND c.condition_start_date = v.visit_start_date
    WHERE (c.condition_source_value LIKE 'F32%' OR c.condition_source_value LIKE 'F33%')
      -- Control de calidad: excluir estancias negativas o errores absurdos de captura (> 1 año)
      AND (v.visit_end_date - v.visit_start_date) >= 0
      AND (v.visit_end_date - v.visit_start_date) <= 365
)
SELECT 
    codigo_cie10,
    gender_concept_id AS genero,
    COUNT(DISTINCT person_id) AS total_pacientes,
    ROUND(AVG(dias_estancia), 2) AS promedio_dias_estancia,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dias_estancia) AS mediana_dias_estancia,
    ROUND(AVG(2026 - year_of_birth), 1) AS edad_promedio_estimada
FROM CohorteDepresion
GROUP BY codigo_cie10, gender_concept_id
ORDER BY total_pacientes DESC;