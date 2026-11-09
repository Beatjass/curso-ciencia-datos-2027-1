import os

import polars as pl

# Configuración de la cadena de conexión a PostgreSQL
DB_USER = os.getenv("DB_USER", "admin_dep_omop")
DB_PASSWORD = os.getenv("DB_PASSWORD", "proyecto_final_26")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "omop_cdm")

URI_CONEXION = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def cargar_tabla(ruta_parquet: str, nombre_tabla: str) -> None:
    """Lee un archivo Parquet y lo vuelca en la tabla PostgreSQL correspondiente."""
    print(f"Iniciando carga de {ruta_parquet} hacia la tabla '{nombre_tabla}'")
    try:
        df = pl.read_parquet(ruta_parquet)

        # if_table_exists='replace' sobrescribe la tabla si ya existe; usa 'append' para agregar
        df.write_database(
            table_name=nombre_tabla,
            connection=URI_CONEXION,
            if_table_exists="replace",
            engine="sqlalchemy",
        )
        print(f"Éxito: {len(df)} registros cargados en la tabla '{nombre_tabla}'.")
    except Exception as e:
        print(f"Error al cargar la tabla '{nombre_tabla}': {e}")


def main():
    print("Iniciando proceso de ingesta hacia PostgreSQL")

    archivos_omop = {
        "data/person.parquet": "person",
        "data/visit_occurrence.parquet": "visit_occurrence",
        "data/condition_occurrence.parquet": "condition_occurrence",
    }

    for ruta, tabla in archivos_omop.items():
        if os.path.exists(ruta):
            cargar_tabla(ruta, tabla)
        else:
            print(f"Advertencia: No se encontró el archivo {ruta}.")

    print("Proceso finalizado.")


if __name__ == "__main__":
    main()
