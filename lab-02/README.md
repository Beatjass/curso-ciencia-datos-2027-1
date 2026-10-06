#Laboratorio 02 - Análisis de un dataset de pacientes, con presupuesto de memoria
Este repositorio contiene el pipeline para el laboratorio 2.

Se generaron los archivos (Synthea) y se analizaron con Jupyter notebook de manera local, cumpliendo con todas las actividades.

Resultados clave:

- Integridad relacional: Los cruces usados evitaron la multiplicación de los datos.
- Media de medias: Se demostró la importancia clínica de utilizar la media de medias (tomando de ejemplo la hemoglobina) para evitar el sesgo poblacional causado por pacientes con múltiples mediciones.
- Anomalías: La reestructuración del formato ancho (pivot) expuso las mediciones repetidas el mismo día.
- Consumo de RAM: La lectura por lotes permitió el procesamiento del dataset completo usando una RAM limitada.
- Comparación entre motores: Lo anterior se aplicó con Polars y PySpark para una comparación entre el manejo de los recursos.

Requisitos: 
Jupyter notebook.
Python 3.0 instalado. Dependencias necesarias: pandas, numpy, pyarrow, polars, pyspark, psutil, os, tracemalloc y time. 
Archivos encounters.csv, observations.csv y patients.csv, proporcionados en este repositorio (generados con synthea).
