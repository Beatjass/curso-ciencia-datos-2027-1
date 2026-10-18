#Build
FROM python:3.12-alpine AS builder
WORKDIR /app

#Entorno virtual de imagen temporal
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

#Producción de la imagen final
FROM python:3.12-alpine
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . /app/
