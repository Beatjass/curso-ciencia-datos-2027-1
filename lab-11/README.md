# Laboratorio 11: Analítica longitudinal

Este repositorio contiene el desarrollo, código reproducible y análisis metodológico del **Laboratorio 11**.
## Entorno
* **Base de datos:** DuckDB
* **Lenguajes:** SQL
* **Entorno de Trabajo:** Jupyter Notebook (`lab_11_longitudinal.ipynb`)

# Estructura del Proyecto

* * **lab_11_longitudinal.ipynb:** Bitácora técnica completa. Incluye la ejecución en vivo del código SQL a través de Python, validaciones analíticas, histogramas de episodios y pruebas de rendimiento.
* * **analitica_longitudinal.sql:** Archivo SQL entregable con las consultas finales refactorizadas, optimizadas mediante CTEs y categorizadas por su pregunta clínica.


## Principales hallazgos
* Refactorización modular de consultas: Migración de estructuras anidadas complejas a CTEs (Common Table Expressions) para garantizar la auditabilidad y legibilidad de las cohortes clínicas.
* Cronologías y eventos extremos: Extracción de la primera y última visita histórica por paciente mediante agregaciones y manejo seguro de valores nulos, evitando sesgos en los cálculos de seguimiento.
* Intervalos entre visitas y mediana global: Aplicación de la función analítica LAG para evaluar los días transcurridos entre encuentros consecutivos, obteniendo la mediana global de la cohorte (~20 días) omitiendo correctamente los nulos iniciales.
* Readmisión hospitalaria a 30 días: Evaluación de reingresos de tipo inpatient empleando LEAD, estableciendo un umbral inclusivo estricto y obteniendo una tasa de readmisión de cohorte del 15.03%.
* Episodios de tratamiento (Gaps and Islands): Simulación de periodos de persistencia terapéutica para Simvastatina con umbrales de 30, 60 y 90 días. Se documentó un hallazgo clave sobre los datos sintéticos de Synthea: los tratamientos crónicos se registran como bloques continuos sin dispensaciones mensuales fraccionadas (refills), evidenciando una adherencia simulada del 100%.
* Deduplicación de laboratorios con ROW_NUMBER(): Filtrado eficiente de series temporales masivas de observaciones (~409k a ~33k registros), conservando exclusivamente el valor basal o más reciente por paciente y analito.
* Media móvil frente a frames acumulados: Contraste dinámico entre un promedio histórico sin acotar y una media móvil estricta de 3 visitas (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) sobre el peso corporal (Body Weight), demostrando cómo se elimina la inercia temporal del pasado remoto.
* Análisis de fecha índice y prevención de fuga de información: Extracción del valor de laboratorio más cercano (HbA1c) previo al primer diagnóstico de diabetes en una ventana estricta de 0 a 90 días, prohibiendo valores posteriores para prevenir la fuga de datos (target leakage).
* Optimización de rendimiento (EXPLAIN ANALYZE): Comparación empírica entre el uso nativo de LAG y un SELF-JOIN con condiciones de desigualdad para calcular días entre visitas. El informe de ejecución evidenció que el Self-Join genera una explosión combinatoria transitoria (más de 2.3 millones de filas intermedias) y un costo computacional ~25 veces superior frente a la pasada lineal optimizada de las funciones de ventana.

## Estructura del Repositorio
```text
 lab-11/
 ┣  lab_11_analitica_longitudinal.ipynb    #Cuaderno principal con todo el código ejecutable, tablas y gráficos.
 ┣  analitica_longitudinal.sql             #Script SQL consolidado con consultas comentadas y preguntas clínicas
 ┗  README.md                              #Documentación del proyecto
