Laboratorio 05 — Convertir un notebook en un paquete probado

Este repositorio contiene y las validaciones correspondientes solicitadas, usando los datos generados con Synthea en el laboratorio 2.

Estructura del proyecto

El código fuente está estructurado como un paquete instalable de python llamado clinlab.
src/clinlab/: Código fuente del paquete (funciones de validación, cálculos matemáticos, limpieza de datos).
tests/: Suite de pruebas unitarias implementadas con pytest.
pyproject.toml: Archivo de configuración para el empaquetado del proyecto y gestión de dependencias.
.pre-commit-config.yaml: Configuración de herramientas de análisis estático (Ruff y Mypy).

Desarrollo local
Para trabajar en este proyecto localmente y poder correr las pruebas, es necesario seguir los siguientes pasos:
1. Clonar el repositorio.
2. Instalar el paquete en modo editable con dependencias de desarrollo:
Esto instalará clinlab junto con pytest, pre-commit, ruff y mypy.
pip install -e ".[dev]"
3. Activar los hooks de pre-commit

Este proyecto utiliza pre-commit para garantizar la calidad del código antes de cada commit.
pre-commit install

Características validadas en las pruebas:
Cálculo exacto de la ecuación CKD-EPI 2021 contra los valores oficiales de la calculadora NKF/MDCalc.
Manejo de valores nulos, centinelas y datos extremos.
Detección de encuentros clínicos imposibles.
Validación estricta de cardinalidad en cruces de datos.
Eliminación de zonas horarias en columnas temporales.
