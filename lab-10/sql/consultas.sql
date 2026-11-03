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