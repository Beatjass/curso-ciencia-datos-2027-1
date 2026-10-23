Laboratorio 06 — Containerizar tu paquete de análisis.

Este repositorio documenta el desarrollo, análisis de seguridad e implementación de un pipeline para el laboratorio.

Para ganrantizar un entorno de producción robusto y seguro, el proyecto implementa los siguiente principios de contenedores:
- Construcción de múltiples etapas (Multi.stage buildings): Separa el entorno de compilación e instalación de dependencias del entorno final de ejecución, reduciendo la superficei de ataque y el tamaño de la imagen.
- Usuario: La aplicación no se ejecuta bajo el usuario root, disminuyendo riesgos críticos en caso de una vulnerabilidad de escalación de privilegios dentro del contenedor.

Cómo se usa
- 1. Construir la imagen localmente: docker build -t clinlab .
- 2. Comprobar que el paquete pasa todas la validaciones de manera aislada dentro del contenedor: docker run --rm clinlab pytest
- 3. Una vez liberada una versión a través del pipeline, ejecutar las pruebas directamente desde el registro remoto sin necesidad de clonar el código fuente: docker run -rm ghcr.io/Beatjass/clinilab:0.1.0 pytest
 
Hallazgos
- Reproducibilidad y control de dependencias: El uso de un gestor de dependencias determinista permitió estabilizar el entorno del proyecto, evidenciando cómo las aplicaciones modernas arrastran dependencias transitivas ocultas que deben ser gestionadas y versionadas rigurosamente.
- Optimización y eficiencia de contenedores: Se demostró que la estructura de un Dockerfile impacta drásticamente en el rendimiento, limpiar el contexto de transferencia con .dockerignore y aplicar construcciones en múltiples etapas (*multi-stage builds*) reduce drásticamente el tamaño de las imágenes (por debajo de los 250 MB) y acelera los tiempos de compilación mediante el uso eficiente de la caché.
- Seguridad y gestión de riesgos: El análisis estático mediante herramientas de escaneo de vulnerabilidades permitió identificar componentes desactualizados y definir planes de eficaces. Asimismo, se comprobó que los datos y credenciales mal gestionados durante la construcción persisten de forma inmutable en el historial de capas de Docker.
- Aislamiento y validación de pruebas: La ejecución de la suite de pruebas bajo un entorno containerizado estricto (utilizando un usuario no privilegiado) evidenció la importancia de evitar dependencias ocultas del entorno local, garantizando que el software funcione de manera idéntica e independiente de la máquina del desarrollador.

Requisitos
Antes de ejecutar el laboratorio, se debe de contar con el siguiente entorno y dependencias:
- Entorno: Docker instalado.
- Versión de Python: Python 3.12.
- Repositorio clinlab del laboratorio 05 completo.
