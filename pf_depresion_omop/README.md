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
├── docker-compose.yml                #Orquestación de contenedores (PostgreSQL y PgAdmin4)
├── docs/                             #Documentación técnica y trazabilidad
│   ├── atricion_cohorte.md           #Registro de criterios de exclusión
│   └── bitacora.md                   #Bitácora metodológica por fases
├── notebooks/                        #Exploración inicial y reporte
│   ├── exploración.py                #Análisis exploratorio preliminar
│   └── pf_dep_omop.docx              #Reporte académico
├── pyproject.toml                    #Configuración de dependencias y pruebas con pytest
├── README.md                         #Documentación principal del proyecto
├── src/
│   └── pf_depresion_omop/            #Pipeline modular ETL y scripts analíticos
│       ├── 01_limpieza_y_atricion.py
│       ├── 02_mapeo_omop.py
│       ├── 03_analisis_descriptivo.py
│       ├── 04_visualizaciones.py
│       ├── 05_pruebas_hipotesis.py
│       ├── 06_comparativa_subtipos.py
│       ├── 07_estacionalidad.py
│       ├── 08_motivos_egreso.py
│       ├── 09_carga_postgres.py
│       └── 10_cohorte_depresion.sql
└── tests/                            #Pruebas automatizadas (calidad y validación de fechas)
    ├── test_calidad_datos.py
    └── test_fechas.py
```

## 3. Guía de instalación y ejecución

### Requisitos previos:
- Python 3.10 o superior.
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

```bash
docker compose up -d
```

El motor de PostgreSQL estará disponible en el puerto `5432` y PgAdmin4 en `http://localhost:5050`.

## Paso 3: Ejecutar el Pipeline ETL (Scripts 01 al 09)
Ejecuta secuencialmente los scripts de procesamiento y carga:

```bash
python src/pf_depresion_omop/01_limpieza_y_atricion.py
python src/pf_depresion_omop/02_mapeo_omop.py
python src/pf_depresion_omop/03_analisis_descriptivo.py
python src/pf_depresion_omop/04_visualizaciones.py
python src/pf_depresion_omop/05_pruebas_hipotesis.py
python src/pf_depresion_omop/06_comparativa_subtipos.py
python src/pf_depresion_omop/07_estacionalidad.py
python src/pf_depresion_omop/08_motivos_egreso.py
python src/pf_depresion_omop/09_carga_postgres.py
```


## 4. Control de calidad y pruebas unitarias

Para verificar la integridad de las transformaciones y la consistencia temporal de los registros antes de la persistencia relacional, el proyecto incluye pruebas automatizadas:

```bash
pytest
```

**Resultado esperado:** 4 pruebas exitosas verificando la limpieza de atípicos y validación de rangos temporales.

## 5. Caracterización de la Cohorte de Depresión (F32 y F33)

La extracción final sobre la base relacional OMOP CDM (`10_cohorte_depresion.sql`) tras un control de calidad (eliminando edades irreales y estancias mayores a 30 días) consolidó una cohorte clínica final de 10,671 pacientes.

**Principales hallazgos**:
- Subtipos predominantes: Concentración notable en episodios depresivos graves sin síntomas psicóticos (`F32.2` y `F33.2`).
- Estancias hospitalarias: Estabilidad metodológica con una mediana de 6 días de internamiento intrahospitalario.
- Distribución demográfica: Mayor frecuencia de ingresos en población femenina y en adultos jóvenes (18-35 años), destacando que los códigos inespecíficos (F32.9 y F33.9) agrupan a pacientes de edad avanzada (6ª y 7ª década).

## 6. Licencia y créditos

Desarrollado como proyecto aplicada en ingeniería de datos en salud y modelos observacionales estandarizados (OMOP CDM).
