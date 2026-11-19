import argparse
import importlib
import logging
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pf_depresion_omop")

PASOS = {
    "01": ("limpieza", "pf_depresion_omop.01_limpieza_y_atricion"),
    "02": ("mapeo", "pf_depresion_omop.02_mapeo_omop"),
    "03": ("descriptivo", "pf_depresion_omop.03_analisis_descriptivo"),
    "04": ("visualizaciones", "pf_depresion_omop.04_visualizaciones"),
    "05": ("hipotesis", "pf_depresion_omop.05_pruebas_hipotesis"),
    "06": ("subtipos", "pf_depresion_omop.06_comparativa_subtipos"),
    "07": ("estacionalidad", "pf_depresion_omop.07_estacionalidad"),
    "08": ("egresos", "pf_depresion_omop.08_motivos_egreso"),
    "09": ("carga", "pf_depresion_omop.09_carga_postgres"),
}

ALIAS = {
    **{k: k for k in PASOS},
    **{alias: k for k, (alias, _) in PASOS.items()},
}


def resolver_pasos(seleccion: list[str] | None, desde: str | None, hasta: str | None) -> list[str]:
    claves = list(PASOS.keys())

    if seleccion:
        resueltos = []
        for item in seleccion:
            clave = ALIAS.get(item.strip().lower())
            if not clave:
                raise ValueError(f"Paso no válido: '{item}'. Opciones: {list(ALIAS.keys())}")
            if clave not in resueltos:
                resueltos.append(clave)
        return sorted(resueltos)

    inicio = claves.index(ALIAS[desde.lower()]) if desde else 0
    fin = claves.index(ALIAS[hasta.lower()]) if hasta else len(claves) - 1

    if inicio > fin:
        raise ValueError(f"Rango inválido: '--desde {desde}' es posterior a '--hasta {hasta}'.")

    return claves[inicio : fin + 1]


def ejecutar_modulo(nombre_modulo: str) -> None:
    modulo = importlib.import_module(nombre_modulo)
    if hasattr(modulo, "main") and callable(modulo.main):
        modulo.main()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pipeline ETL y análisis de egresos hospitalarios por depresión (OMOP CDM)."
    )
    parser.add_argument(
        "--pasos",
        nargs="+",
        help=(
            "Pasos específicos a ejecutar por número o alias "
            "(ej. --pasos 01 02 08 o --pasos limpieza egresos)."
        ),
    )
    parser.add_argument("--desde", help="Paso inicial del rango (ej. --desde 03).")
    parser.add_argument("--hasta", help="Paso final del rango (ej. --hasta 08).")
    parser.add_argument(
        "--listar", action="store_true", help="Muestra los pasos disponibles y sale."
    )

    args = parser.parse_args(argv)

    if args.listar:
        for codigo, (alias, mod) in PASOS.items():
            print(f"  {codigo} ({alias:<15}) -> {mod}")
        return 0

    try:
        a_ejecutar = resolver_pasos(args.pasos, args.desde, args.hasta)
    except (ValueError, KeyError) as err:
        logger.error("Error en argumentos: %s", err)
        return 2

    for codigo in a_ejecutar:
        alias, mod = PASOS[codigo]
        logger.info("Iniciando paso %s (%s)...", codigo, alias)
        try:
            ejecutar_modulo(mod)
            logger.info("Paso %s completado.", codigo)
        except Exception as exc:
            logger.exception("Fallo en el paso %s (%s): %s", codigo, alias, exc)
            return 1

    logger.info("Pipeline finalizado exitosamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
