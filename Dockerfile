# Usar una imagen oficial de Python basada en Debian estable para producción
FROM python:3.11-slim-bookworm

# Configurar variables de entorno esenciales para Python en contenedores
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema y herramientas de compilación necesarias para psycopg2 y librerías de IA
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requisitos e instalar las librerías de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente del proyecto local al contenedor
COPY . /app/

# Exponer el puerto interno en el que correrá Gunicorn
EXPOSE 8000

# Comando por defecto para producción usando Gunicorn
CMD ["gunicorn", "mindmetrics.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
