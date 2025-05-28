FROM python:3.11-slim

WORKDIR /app

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=wsgi.py
ENV FLASK_ENV=production

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar los archivos de requerimientos primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar los scripts de entrada
COPY wait-for-postgres.sh docker-entrypoint.sh ./
RUN chmod +x wait-for-postgres.sh docker-entrypoint.sh
RUN sed -i 's/\r$//' wait-for-postgres.sh docker-entrypoint.sh

# Copiar el código de la aplicación
COPY . .

# Crear directorio para uploads si no existe
RUN mkdir -p app/static/uploads

# Exponer el puerto que usará la aplicación
EXPOSE 5000

# Comando para iniciar la aplicación
ENTRYPOINT ["./docker-entrypoint.sh"]
