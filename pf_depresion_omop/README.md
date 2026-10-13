#Estandarización clínica de Trastornos Depresivos en México a OMOP CDM

#Propuesta de proyecto
¿Cómo construir un pipeline automatizado para estandarizar y procesar a nivel poblacional los egresos hospitalarios por trastornos depresivos (F32, F33) en México?

*Modalidad: C, pipeline de datos en la nube.
*Fuente de datos: Ruta D, datos abiertos de México (DGIS - Egresos hospitalarios sectoriales).

#Avance 1: Definición de cohorte y tabla de atrición.
Se implemento un script de evaluación perezosa para extraer y filtrar la cohorte de pacientes diagnósticados primarios o secundarios de depresión (CIE-10: F32, F33) a partir de la base de datos nacional DGIS, aplicando filtros de calidad.

