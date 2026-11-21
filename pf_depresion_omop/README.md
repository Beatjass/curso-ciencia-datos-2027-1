# Pipeline de estandarización y análisis de egresos hospitalarios por depresión en México (OMOP CDM)

Repositorio para el proyecto final enfocado en la ingesta, depuración, estandarización y análisis de los registros de egresos hospitalarios por trastornos depresivos en México (CIE-10: F32 y F33), adoptando el estándar internacional OMOP CDM (Observational Medical Outcomes Partnership Common Data Model).

## 1. Arquitectura del sistema e infraestructura

El proyecto está diseñado bajo una arquitectura modular y reproducible contenerizada mediante Docker. El ecosistema técnico integra:

- **Procesamiento de datos:** Ingeniería de datos optimizada en memoria utilizando `Polars` en Python para el manejo de más de 5.8 millones de registros nacionales.
- **Motor relacional:** PostgreSQL configurado con el esquema estandarizado OMOP CDM (`omop_cdm`).
- **Administración visual:** PgAdmin4 para la supervisión y ejecución de consultas analíticas directas sobre la base de datos.
- **Control de calidad (CI/CD):** Pruebas unitarias y de integridad automatizadas mediante `pytest`.

## 2. Estructura del Repositorio

```text
pf_depresion_omop/
├── data/                             #Datos crudos (Egresos_Sectorial_2024.txt), tablas Parquet, CSVs de exclusión y gráficas (PNG)
│   ├── Egresos_Sectorial_2024.txt
│   ├── person.parquet
│   ├── visit_occurrence.parquet
│   ├── condition_occurrence.parquet
│   ├── registros_excluidos_edad.csv
│   ├── registros_estancia_prolongada.csv
│   ├── distribucion_demografica.png
│   ├── estacionalidad_mensual.png
│   └── motivos_egreso.png
├── docs/                             #Documentación clínica y bitácora del proyecto
│   ├── atricion_cohorte.md
│   └── bitacora.md
├── notebooks/                        #Exploración inicial y reporte del proyecto
│   ├── exploración.py
│   └── pf_dep_omop.docx
├── src/
│   └── pf_depresion_omop/
│       ├── 01_limpieza_y_atricion.py #Filtrado CIE-10 (F32/F33), calidad demográfica y tabla de atrición
│       ├── 02_mapeo_omop.py          #Mapeo relacional a tablas person, visit_occurrence y condition_occurrence
│       ├── 03_analisis_descriptivo.py#Estadísticas descriptivas y depuración clínica (estancia <= 30 días)
│       ├── 04_visualizaciones.py     #Distribución demográfica por edad y género
│       ├── 05_pruebas_hipotesis.py   #Prueba U de Mann-Whitney de estancia hospitalaria por género
│       ├── 06_comparativa_subtipos.py#Comparativa de estancia entre episodio único (F32) y recurrente (F33)
│       ├── 07_estacionalidad.py      #Serie temporal mensual de ingresos hospitalarios (2024)
│       ├── 08_motivos_egreso.py      #Distribución de desenlaces y motivos clínicos de egreso
│       ├── 09_carga_postgres.py      #Ingesta de tablas OMOP Parquet hacia PostgreSQL
│       ├── 10_cohorte_depresion.sql  #Consultas SQL analíticas sobre la cohorte OMOP en PostgreSQL
│       └── utils_cohorte.py          #Funciones compartidas de unión y filtrado clínico de la cohorte (DRY)
├── tests/                            #Suite de 23 pruebas unitarias y de integración con Pytest
│   ├── test_calidad_datos.py
│   ├── test_carga_postgres.py
│   ├── test_descriptivo.py
│   ├── test_estacionalidad.py
│   ├── test_etl_omop.py
│   ├── test_fechas.py
│   ├── test_hipotesis.py
│   ├── test_motivos_egreso.py
│   ├── test_subtipos.py
│   └── test_visualizaciones.py
├── main.py                           #Orquestador CLI para ejecutar el pipeline completo o por etapas
├── docker-compose.yml                #Servicios de PostgreSQL y PgAdmin4 con volúmenes persistentes
└── pyproject.toml                    #Dependencias, configuración de Pytest y reglas de Ruff
```

## 3. Guía de instalación y ejecución

### Requisitos previos:
- Python 3.14.
- Docker instalado en el sistema local.

### Paso 1: Configurar el entorno virtual e instalar dependencias

```bash
# 1. Clonar únicamente la carpeta del proyecto
git clone --filter=blob:none --no-checkout --depth 1 https://github.com/Beatjass/curso-ciencia-datos-2027-1.git
cd curso-ciencia-datos-2027-1
git sparse-checkout set pf_depresion_omop
git checkout main

# 2. Entrar a la carpeta del proyecto (donde está el pyproject.toml)
cd pf_depresion_omop

# 3. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate  #En Windows: .venv\Scripts\activate

# 4. Instalar el proyecto en modo editable y sus dependencias
pip install -e .
```

### Paso 2: Levantar la infraestructura en Docker

Este proyecto utiliza Docker Compose para orquestar PostgreSQL (con el modelo OMOP CDM) y PgAdmin4.

Configuración de variables de entorno
Crea un archivo `.env` en la raíz del proyecto basándote en la plantilla `.env.example`:
```bash
cp .env.example .env
```

Ejecución de Contenedores

Levanta los servicios en segundo plano:

```bash
docker compose up -d
```

El motor de PostgreSQL estará disponible en el puerto `5432` y PgAdmin4 en `http://localhost:5050`.

### Paso 3: Configuración del servidor en PgAdmin 4

Una vez que los contenedores estén activos, abre tu navegador e ingresa a:
http://localhost:5050/browser/

Inicia sesión con el correo y contraseña definidos en tu archivo .env. Para registrar y visualizar la base de datos de la cohorte, añade un nuevo servidor con los siguientes parámetros:

Agregar nuevo servidor

```bash
    Pestaña General:
        Name: OMOP CDM PostgreSQL

    Pestaña Connection:
        Host name/address: omop_db
        Port: 5432
        Maintenance database: omop_cdm
        Username: (el valor de tu POSTGRES_USER)
        Password: (la contraseña definida en tu POSTGRES_PASSWORD)
```


### Paso 4: Ejecutar el Pipeline ETL (`main.py`)

El proyecto cuenta con un orquestador CLI (`main.py`) que permite ejecutar todo el flujo ETL y analítico de manera secuencial o parametrizada sin necesidad de invocar cada script manualmente:

```bash
#Ver los pasos disponibles y sus alias
python main.py --listar

#Ejecutar el pipeline completo (pasos 01 al 09)
python main.py

#Ejecutar pasos específicos por número o alias
python main.py --pasos 01 02 09
python main.py --pasos limpieza mapeo egresos

#Ejecutar un rango continuo de pasos
python main.py --desde 03 --hasta 08

```


## 4. Control de calidad y pruebas unitarias

Para verificar la integridad de las transformaciones, el mapeo relacional OMOP CDM, la consistencia temporal, los cálculos estadísticos y la ingesta a PostgreSQL sin depender de archivos externos ni de una conexión activa a base de datos, el proyecto incluye una suite de pruebas automatizadas:

```bash
pytest -v
```

**Resultado esperado:** 23 pruebas unitarias y de integración exitosas verificando reglas de atrición, manejo de valores nulos, rangos temporales, integridad referencial OMOP, pruebas de hipótesis, generación de visualizaciones y carga de datos.

## 5. Caracterización de la Cohorte de Depresión (F32 y F33)

La extracción final sobre la base relacional OMOP CDM (`10_cohorte_depresion.sql`) tras un control de calidad (eliminando edades irreales y estancias mayores a 30 días) consolidó una cohorte clínica final de 10,671 pacientes.

**Principales hallazgos**:
- Subtipos predominantes: Concentración notable en episodios depresivos graves sin síntomas psicóticos (`F32.2` y `F33.2`).
- Estancias hospitalarias: Estabilidad metodológica con una mediana de 6 días de internamiento intrahospitalario.
- Distribución demográfica: Mayor frecuencia de ingresos en población femenina y en adultos jóvenes (18-35 años), destacando que los códigos inespecíficos (F32.9 y F33.9) agrupan a pacientes de edad avanzada (6ª y 7ª década).

## 6. Licencia y créditos

Desarrollado como proyecto aplicada en ingeniería de datos en salud y modelos observacionales estandarizados (OMOP CDM).
