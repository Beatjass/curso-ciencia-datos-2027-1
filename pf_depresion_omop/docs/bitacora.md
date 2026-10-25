#Bitácora de análisis clínico: Depresión en OMOP CDM con los registros de DGIS 2024.

##Fase 1: Estandarización y depuración de cohorte
**Objetivo:** Transformar los registros crudos de la DGIS 2024 al modelo OMOP y aislar una cohorte clínicamente válida para episodios depresivos (F32, F33).
* **Mapeo ETL:** Se procesó el archivo fuente `Egresos_Sectorial_2024.txt` utilizando Polars. Se generaron y almacenaron en formato parquet las tablas `person`, `visit_occurrence` y `condition_occurrence`.
* **Filtros de calidad:** A partir de 10,972 registros iniciales, se aplicaron dos criterios de exclusión para eliminar sesgos:
  1. Edades biológicamente irreales (>120 años, derivados del código "999").
  2. Estancias hospitalarias atípicas (>30 días).
* **Resultado:** Cohorte final consolidada en 10,671 pacientes únicos.

##Fase 2: Análisis descriptivo
**Objetivo:** Explorar la distribución demográfica y validar la integridad del código fuente.
* **Estadística descriptiva:** La cohorte presenta una edad promedio de 31.9 años y una estancia mediana de 6 días, con predominancia de diagnósticos graves (F322, F332).
* **Visualización:** Se generó el panel `distribucion_demografica.png` (histograma de edad y diagrama de caja de estancia por género) utilizando seaborn y matplotlib.

##Fase 3: Pruebas de hipótesis (estancia hospitalaria)
**Objetivo:** Determinar si el género influye significativamente en la duración del internamiento psiquiátrico.
* **Metodología:** Al observar asimetría en los datos de estancia, se seleccionó la prueba no paramétrica U de Mann-Whitney.
* **Resultados:** 
  * Hombres (n=2,757): Mediana = 6.0 días.
  * Mujeres (n=7,914): Mediana = 6.0 días.
  * Estadístico U: 11,567,012.5
  * Valor p: 0.00000223
* **Conclusión:** Se rechaza la hipótesis nula. Existe una diferencia estadísticamente significativa en las distribuciones de los días de internamiento entre géneros, justificando un análisis segmentado en fases posteriores.

##Fase 3.1: Pruebas de hipótesis (subtipos clínicos: F32 vs F33)
**Objetivo:** Evaluar si si los pacientes con trastorno depresivo recurrente (F33) requieren tiempos de estabilización intrahospitalaria significativamente mayores que aquellos experimentando un primer episodio único (F32).
* **Resultados;**
  * Mediana F32: 5.0 días (n=5732)
  * Mediana F33: 7.0 días (n=4939)
  * Estadistico U: 13,161,433.0
  * Valor p: 0.0000000
* **Conclusión:** Se rechaza la hipótesis nula. Hay una diferencia estadisticamente significativa entre los subtipos clínicos de depresión, donde los pacientes con F33 requieren tiempo de internamiento más prolongados que los que presentan un episodio único (F32).

##Fase 4: Estacionalidad de ingresos hospitalarios
**Objetivo:** Identificar la distribución temporal mensual de las hospitalizaciones por depresión para detectar picos de demanda.
* **Metodología:** Agrupación y conteo de frecuencias utilizando el mes extraído de la variable `visit_start_date` del estándar OMOP.
* **Resultados:** Se observa un patrón estacional bimodal en la afluencia de pacientes.
  * Pico máximo: Octubre (1,067 ingresos).
  * Segundo pico de relevancia: Mayo (1,047 ingresos).
  * Menor volumen de ingresos: Enero (683) y Diciembre (778).
* **Conclusión:** La carga hospitalaria por episodios depresivos severos no se distribuye uniformemente, presentando concentraciones críticas hacia mediados de la primavera y mediados del otoño.

## Siguientes pasos (pendiente)
* Analizar los desenlaces clínicos mediante la variable de motivo de egreso para identificar patrones en altas, traslados o defunciones según género, edad y diagnóstico (F32 vs. F33).
