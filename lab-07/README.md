#Laboratorio 07: Levantar un stack clínico completo

Este laboratorio tiene como objetivo escribir y diseñar un compose.yml que levante un entorno de análisis clínico (base de datos, pacientem, notebook) y que pueda ser levantado por otra persona-
El stack integra una base de datos relacional PostgreSQL, un entorno de análisis con Jupyter Notebook y Adminer como cliente web interactivo.

## Estructura del Proyecto

El laboratorio se organiza principalmente dentro de la carpeta `lab-07/`:

```text
.
├── lab-07/
    ├── compose.yml          #Definición del entorno
    ├── .env.example         #Plantilla de variables de entorno (sin credenciales reales)
    ├── initdb/              #Scripts de inicialización (.sql/.sh) para la base de datos
    ├── README.md            #Guía del laboratorio (este archivo)
    ├── notebooks/           #Cuadernos Jupyter con las pruebas de conexión Python-PostgreSQL
    └── bitacora.md          #Registro de depuración ps → logs → exec

```

##Despliegue
#Copiar la plantilla de variables de entorno:
cp .env.example .env

#Configurar tus credenciales locales:
Abre el archivo .env y asigna tus valores reales (ejemplo: POSTGRES_PASSWORD=contraseña_segura).

#Levantar la infraestructura:
docker compose up -d
Adicionalmente se puede ejecutar docker compose --profile actividad7 up -d pra habilitar la interfaz web de administración de la base de datos.

#Configuración y variables de Entorno (.env)

##El archivo compose.yml utiliza la sintaxis estricta de validación para garantizar que ninguna variable crítica quede vacía antes de inicializar los contenedores:
POSTGRES_PASSWORD: "${POSTGRES_PASSWORD:?Falta la contraseña en el archivo .env}"

##Variables configurables
POSTGRESS_USER, POSTGRES_PASSWORD, POSTGRES_DB, DB_PORT, JUPYTER_PORT, JUPYTER_TOKEN, ADMINER_PORT.

##Servicios e Infraestructura
1. db (PostgreSQL 15 Alpine):
- Base de datos relacional persistente mediante el volumen con nombre db_data.
- Incorpora un healthcheck con pg_isready para verificar disponibilidad real antes de permitir la conexión de dependientes.

2. jupyter (Jupyter SciPy Notebook):
- Entorno interactivo de análisis Python montado en la carpeta ./notebooks.
- Utiliza depends_on con la condición service_healthy para evitar intentos prematuros de conexión a la base de datos.

3. adminer (Gestor de Base de Datos Web):
- Cliente ligero accesible opcionalmente en el puerto 8080 mediante el perfil actividad7.

##Prueba de conexión en Jupyter
1. Accede a Jupyter en http://localhost:8888 e ingresa tu token (JUPYTER_TOKEN).
2. Abre el notebook almacenado en la carpeta notebooks/ y ejecuta el bloque de conexión:

from sqlalchemy import create_engine

motor = create_engine("postgresql://beatjass:clinlab07@db:5432/clindb")
with motor.connect() as conexion:
    print("Conexión interna exitosa")

##Limpieza y reset de volúmenes
Para destruir los contenedores y eliminar el volumen persistente de la base de datos (forzando una reinicialización desde cero):
docker compose down -v
