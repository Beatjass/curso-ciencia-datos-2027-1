import importlib

import polars as pl
import pytest

mod_09 = importlib.import_module("pf_depresion_omop.09_carga_postgres")


def test_construir_uri_desde_variables_postgres(monkeypatch):
    monkeypatch.setenv("POSTGRES_USER", "usuario_test")
    monkeypatch.setenv("POSTGRES_PASSWORD", "clave_123")
    monkeypatch.setenv("POSTGRES_DB", "omop_test")
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_PORT", "5433")

    uri = mod_09.construir_uri_conexion()
    assert uri == "postgresql://usuario_test:clave_123@127.0.0.1:5433/omop_test"


def test_cargar_tabla_archivo_inexistente_lanza_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        mod_09.cargar_tabla(
            tmp_path / "no_existe.parquet", "person", uri="postgresql://u:p@h:5432/db"
        )


def test_main_ingesta_omop_mockeada(tmp_path, monkeypatch):
    for nombre in ["person", "visit_occurrence", "condition_occurrence"]:
        pl.DataFrame({"id": [1, 2]}).write_parquet(tmp_path / f"{nombre}.parquet")

    llamadas = []

    def fake_write_database(self, table_name, connection, if_table_exists, engine):
        llamadas.append((table_name, connection, if_table_exists, engine, self.height))

    monkeypatch.setattr(pl.DataFrame, "write_database", fake_write_database)

    res = mod_09.main(dir_datos=tmp_path, uri="postgresql://user:pass@localhost:5432/omop_cdm")

    assert res == {"person": 2, "visit_occurrence": 2, "condition_occurrence": 2}
    assert [c[0] for c in llamadas] == ["person", "visit_occurrence", "condition_occurrence"]
    assert all(c[2] == "replace" for c in llamadas)
