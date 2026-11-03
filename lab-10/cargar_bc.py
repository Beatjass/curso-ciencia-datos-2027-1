import os
import duckdb

DATA_DIR = "./data"
DB_FILE = "base_clinica.duckdb"

#Conectar a la base de datos DuckDB
conn = duckdb.connect(DB_FILE)

#Tablas a procesar y asignación explícita de tipos de datos de fecha
TABLE_TYPES = {
    "patients": "{'BIRTHDATE': 'DATE', 'DEATHDATE': 'DATE'}",
    "encounters": "{'START': 'TIMESTAMP', 'STOP': 'TIMESTAMP'}",
    "conditions": "{'START': 'DATE', 'STOP': 'DATE'}",
    "observations": "{'DATE': 'TIMESTAMP'}",
    "medications": "{'START': 'TIMESTAMP', 'STOP': 'TIMESTAMP'}"
}

print("Iniciando creación de tablas e ingesta de CSVs...")

for table, types_dict in TABLE_TYPES.items():
    csv_path = os.path.join(DATA_DIR, f"{table}.csv")
    
    if os.path.exists(csv_path):
        try:
            # Creación e ingesta nativa con lectura tolerante a errores
            query = f"""
                CREATE OR REPLACE TABLE {table} AS 
                SELECT * FROM read_csv_auto(
                    '{csv_path}', 
                    types={types_dict}, 
                    ignore_errors=true, 
                    header=true
                );
            """
            conn.execute(query)
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"✓ Tabla '{table}' cargada exitosamente ({count:,} filas).")
        except Exception as e:
            print(f"✗ Error al procesar '{table}': {e}")
    else:
        print(f"⚠️ Archivo no encontrado: {csv_path}")

print("\n" + "="*45)
print("Conteo de filas por tabla cargada:")
print("="*45)

#Consulta de conteo directo de registros en las tablas creadas
existing_tables = [t for t in TABLE_TYPES.keys() if os.path.exists(os.path.join(DATA_DIR, f"{t}.csv"))]

if existing_tables:
    union_query = " UNION ALL ".join([f"SELECT '{t}' AS tabla, COUNT(*) AS filas FROM {t}" for t in existing_tables])
    df_counts = conn.execute(union_query).df()
    print(df_counts.to_string(index=False))
else:
    print("No se encontraron tablas cargadas.")

conn.close()