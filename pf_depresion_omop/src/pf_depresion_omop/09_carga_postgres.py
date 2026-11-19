import os
from pathlib import Path

import polars as pl


def cargar_env_local(ruta_env: Path | str = ".env") -> None:
    """Carga variables desde .env si no están ya definidas en el entorno."""
    archivo = Path(ruta_env)
    if not archivo.exists():
        return
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip())


def construir_uri_conexion() -> str:
    """Construye la URI de PostgreSQL soportando variables POSTGRES_* o DB_*."""
    cargar_env_local()
    user = os.getenv("POSTGRES_USER") or os.getenv("DB_USER", "admin_dep_omop")
    password = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD", "proyecto_final_26")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME", "omop_cdm")
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def cargar_tabla(ruta_parquet: Path | str, nombre_tabla: str, uri: str | None = None) -> int:
    """Lee un archivo Parquet y lo vuelca en la tabla PostgreSQL correspondiente."""
    ruta = Path(ruta_parquet)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo fuente: {ruta}")

    conexion = uri or construir_uri_conexion()
    print(f"Iniciando carga de {ruta} hacia la tabla '{nombre_tabla}'")

    df = pl.read_parquet(ruta)
    df.write_database(
        table_name=nombre_tabla,
        connection=conexion,
        if_table_exists="replace",
        engine="sqlalchemy",
    )
    print(f"Éxito: {len(df)} registros cargados en la tabla '{nombre_tabla}'.")
    return len(df)


def main(dir_datos: Path | str = "data", uri: str | None = None) -> dict[str, int]:
    print("Iniciando proceso de ingesta hacia PostgreSQL")
    base = Path(dir_datos)
    conexion = uri or construir_uri_conexion()

    archivos_omop = {
        base / "person.parquet": "person",
        base / "visit_occurrence.parquet": "visit_occurrence",
        base / "condition_occurrence.parquet": "condition_occurrence",
    }

    conteos: dict[str, int] = {}
    for ruta, tabla in archivos_omop.items():
        if ruta.exists():
            conteos[tabla] = cargar_tabla(ruta, tabla, uri=conexion)
        else:
            print(f"Advertencia: No se encontró el archivo {ruta}.")

    print("Proceso finalizado.")
    return conteos


if __name__ == "__main__":
    main()
