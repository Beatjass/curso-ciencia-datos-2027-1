# Laboratorio 10: Análisis de Datos Clínicos con DuckDB y SQL

## Objetivo
Auditar y analizar una cohorte de registros médicos electrónicos (EHR) utilizando **DuckDB** como motor analítico columnar. Este laboratorio abarca desde la ingesta de datos sintéticos y el diseño relacional, hasta la resolución de consultas clínicas complejas, auditoría de integridad de datos y optimización de rendimiento (*profiling*) frente a Pandas.

## Stack Tecnológico
* **Motor Analítico:** DuckDB (OLAP columnar, ejecución vectorizada)
* **Lenguajes:** SQL (Dialecto DuckDB/PostgreSQL), Python 3
* **Procesamiento y Entorno:** Jupyter Notebooks, Pandas
* **Generación de Datos:** Synthea (Patient Population Simulator)
* **Control de Versiones:** Git / GitHub

## Estructura del Repositorio
```text
 lab-10/
 ┣  notebook/
 ┃ ┗  lab_10_duckdb.ipynb    #Bitácora unificada: Auditoría, profiling y comparativa Pandas
 ┣  sql/
 ┃ ┣  carga.sql              #Script de ingesta de CSVs a DuckDB
 ┃ ┗  consultas.sql          #15 consultas clínicas (básicas, intermedias y avanzadas)
 ┗  README.md                #Documentación del proyecto
```

## Generación de datos (Synthea)
Los archivos .csv crudos generados por Synthea han sido excluidos del repositorio vía .gitignore.
Para reproducir el conjunto de datos de este laboratorio, es necesario ejecutar Synthea localmente. El comando utilizado para generar la cohorte (1000 pacientes) base es:
```text
java -jar synthea-with-dependencies.jar -p 1000
```

## Principales hallazgos y actividades
- 1. Auditoría clínica:
Análisis demográfico, mapeo de comorbilidades (riesgo cardiometabólico por diabetes + hipertensión) y evaluación de guías de práctica clínica (identificación de brechas de medición de HbA1c mediante Anti-Joins).
- 2. Control de calidad de datos (trampas de JOINs):
Demostración y corrección de la explosión de cardinalidad en relaciones 1:N al promediar duraciones de encuentros mediante WHERE EXISTS.
LEFT JOIN Trap: Identificación de la pérdida silenciosa de registros al aplicar filtros de la tabla derecha en la cláusula WHERE en lugar de la cláusula ON.
- 3. Profiling y arquitectura (EXPLAIN ANALYZE):
Verificación del comportamiento del motor columnar de DuckDB, evidenciando cómo el Column Pruning y el Predicate Pushdown sustituyen la necesidad de índices B-Tree tradicionales.
- 4. Comparativa de Rendimiento (SQL vs Pandas):
Evaluación de tiempos de I/O y legibilidad de código, validando a DuckDB como herramienta superior para tareas relacionales y de agregación inicial en flujos de datos clínicos.
