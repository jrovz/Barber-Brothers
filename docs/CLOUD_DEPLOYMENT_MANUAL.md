# Manual de Configuración para Despliegue en la Nube - Barber Brothers

## Tabla de Contenidos
1. [Arquitectura de Despliegue](#arquitectura-de-despliegue)
2. [Google Cloud Platform (GCP)](#google-cloud-platform-gcp)
3. [Amazon Web Services (AWS)](#amazon-web-services-aws)
4. [Microsoft Azure](#microsoft-azure)
5. [Docker y Contenedores](#docker-y-contenedores)
6. [Variables de Entorno](#variables-de-entorno)
7. [Configuración de Base de Datos](#configuración-de-base-de-datos)
8. [Monitoreo y Logging](#monitoreo-y-logging)
9. [Certificados SSL/TLS](#certificados-ssltls)
10. [CI/CD Pipeline](#cicd-pipeline)

## Arquitectura de Despliegue

### Componentes Principales
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│  Web Application│────│    Database     │
│   (Nginx/ALB)   │    │   (Flask/Gunicorn)│  │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CDN/Static    │    │   File Storage  │    │    Email Service│
│    Assets       │    │   (Uploads)     │    │    (SMTP/SES)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Requisitos del Sistema
- **CPU**: Mínimo 2 vCPUs para producción
- **RAM**: Mínimo 4GB para aplicación + 2GB para PostgreSQL
- **Storage**: 20GB para aplicación + storage escalable para uploads
- **Network**: HTTPS habilitado, puertos 80/443 abiertos

## Google Cloud Platform (GCP)

### 1. Configuración Inicial

#### Crear Proyecto
```bash
# Crear nuevo proyecto
gcloud projects create barber-brothers-prod --name="Barber Brothers Production"

# Configurar proyecto activo
gcloud config set project barber-brothers-prod

# Habilitar APIs necesarias
gcloud services enable \
    sqladmin.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    storage-api.googleapis.com \
    secretmanager.googleapis.com
```

### 2. Cloud SQL (PostgreSQL)

#### Crear Instancia
```bash
# Crear instancia Cloud SQL
gcloud sql instances create barberia-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-east1 \
    --storage-type=SSD \
    --storage-size=20GB \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04

# Crear base de datos
gcloud sql databases create barberia_db --instance=barberia-db

# Crear usuario
gcloud sql users create barberia_user \
    --instance=barberia-db \
    --password=SecurePassword123!
```

#### Configuración de Conexión
```python
# app/utils/cloud_connection_pg.py
import os
from google.cloud.sql.connector import Connector
import sqlalchemy

def init_connection_engine():
    """Inicializa conexión a Cloud SQL usando Cloud SQL Connector"""
    
    def getconn():
        connector = Connector()
        conn = connector.connect(
            os.environ["INSTANCE_CONNECTION_NAME"],  # "project:region:instance"
            "pg8000",
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASS"],
            db=os.environ["DB_NAME"]
        )
        return conn

    engine = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
    )
    return engine
```

### 3. Cloud Run Deployment

#### Dockerfile para Cloud Run
```dockerfile
# Dockerfile.cloudrun
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de aplicación
COPY . .

# Crear directorio para uploads
RUN mkdir -p app/static/uploads

# Configurar puerto para Cloud Run
ENV PORT=8080
ENV FLASK_ENV=production

# Aplicar migraciones y iniciar aplicación
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 wsgi:app
```

#### Deploy Script
```bash
#!/bin/bash
# scripts/deploy-gcp.sh

# Variables
PROJECT_ID="barber-brothers-prod"
SERVICE_NAME="barber-brothers-app"
REGION="us-east1"

# Build y push imagen
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy a Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "FLASK_ENV=production" \
    --set-cloudsql-instances $PROJECT_ID:$REGION:barberia-db

echo "Deployment completed!"
echo "Service URL: $(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')"
```

### 4. Secret Manager
```bash
# Crear secrets
echo -n "SecurePassword123!" | gcloud secrets create db-password --data-file=-
echo -n "your-secret-key-here" | gcloud secrets create flask-secret-key --data-file=-
echo -n "smtp-password" | gcloud secrets create mail-password --data-file=-

# Dar permisos a Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 5. Cloud Storage para Archivos
```bash
# Crear bucket para uploads
gsutil mb gs://barber-brothers-uploads

# Configurar CORS
cat > cors.json << EOF
[
    {
        "origin": ["https://your-domain.com"],
        "method": ["GET", "POST"],
        "responseHeader": ["Content-Type"],
        "maxAgeSeconds": 3600
    }
]
EOF

gsutil cors set cors.json gs://barber-brothers-uploads
```

## Amazon Web Services (AWS)

### 1. RDS PostgreSQL Setup
```bash
# Crear subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name barberia-subnet-group \
    --db-subnet-group-description "Subnet group for Barberia DB" \
    --subnet-ids subnet-12345 subnet-67890

# Crear instancia RDS
aws rds create-db-instance \
    --db-instance-identifier barberia-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.3 \
    --master-username barberia_user \
    --master-user-password SecurePassword123! \
    --allocated-storage 20 \
    --storage-type gp2 \
    --db-name barberia_db \
    --backup-retention-period 7 \
    --storage-encrypted
```

### 2. ECS Fargate Deployment
```yaml
# docker-compose.aws.yml
version: '3.8'
services:
  web:
    image: your-account.dkr.ecr.region.amazonaws.com/barber-brothers:latest
    ports:
      - "80:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@rds-endpoint/barberia_db
      - SECRET_KEY=${SECRET_KEY}
      - MAIL_SERVER=email-smtp.region.amazonaws.com
      - MAIL_PORT=587
      - MAIL_USE_TLS=True
      - MAIL_USERNAME=${SMTP_USERNAME}
      - MAIL_PASSWORD=${SMTP_PASSWORD}
    logging:
      driver: awslogs
      options:
        awslogs-group: barber-brothers
        awslogs-region: us-east-1
```

### 3. Application Load Balancer
```bash
# Crear ALB
aws elbv2 create-load-balancer \
    --name barber-brothers-alb \
    --subnets subnet-12345 subnet-67890 \
    --security-groups sg-12345

# Crear target group
aws elbv2 create-target-group \
    --name barber-brothers-tg \
    --protocol HTTP \
    --port 5000 \
    --vpc-id vpc-12345 \
    --health-check-path /api/health
```

### 4. S3 para Archivos Estáticos
```python
# app/config/aws_config.py
import boto3
from botocore.config import Config

class AWSConfig:
    S3_BUCKET = os.environ.get('S3_BUCKET', 'barber-brothers-uploads')
    S3_REGION = os.environ.get('S3_REGION', 'us-east-1')
    
    @staticmethod
    def get_s3_client():
        return boto3.client(
            's3',
            region_name=AWSConfig.S3_REGION,
            config=Config(signature_version='s3v4')
        )
```

## Microsoft Azure

### 1. Azure Database for PostgreSQL
```bash
# Crear resource group
az group create --name rg-barber-brothers --location eastus

# Crear servidor PostgreSQL
az postgres server create \
    --resource-group rg-barber-brothers \
    --name barberia-db-server \
    --location eastus \
    --admin-user barberia_admin \
    --admin-password SecurePassword123! \
    --sku-name B_Gen5_1 \
    --version 11

# Crear base de datos
az postgres db create \
    --resource-group rg-barber-brothers \
    --server-name barberia-db-server \
    --name barberia_db
```

### 2. Azure Container Instances
```yaml
# azure-container.yml
apiVersion: 2018-10-01
location: eastus
name: barber-brothers-app
properties:
  containers:
  - name: web
    properties:
      image: your-registry.azurecr.io/barber-brothers:latest
      ports:
      - port: 80
      environmentVariables:
      - name: DATABASE_URL
        value: postgresql://user:pass@server.postgres.database.azure.com/barberia_db
      - name: SECRET_KEY
        secureValue: your-secret-key
      resources:
        requests:
          cpu: 1.0
          memoryInGb: 1.5
  osType: Linux
  restartPolicy: Always
tags: null
type: Microsoft.ContainerInstance/containerGroups
```

### 3. Azure App Service
```bash
# Crear App Service Plan
az appservice plan create \
    --name barber-brothers-plan \
    --resource-group rg-barber-brothers \
    --sku B1 \
    --is-linux

# Crear Web App
az webapp create \
    --resource-group rg-barber-brothers \
    --plan barber-brothers-plan \
    --name barber-brothers-app \
    --deployment-container-image-name your-registry.azurecr.io/barber-brothers:latest
```

## Docker y Contenedores

### 1. Multi-stage Dockerfile Optimizado
```dockerfile
# Dockerfile.production
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependencias de build
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && apt-get clean

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Instalar solo runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias del builder stage
COPY --from=builder /root/.local /root/.local

# Copiar código de aplicación
COPY . .

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Configurar PATH
ENV PATH=/root/.local/bin:$PATH

# Crear directorio para uploads
RUN mkdir -p app/static/uploads

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "wsgi:app"]
```

### 2. Docker Compose para Desarrollo
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
      - DATABASE_URL=postgresql://postgres:password@db:5432/barberia_db
    volumes:
      - .:/app
      - ./app/static/uploads:/app/app/static/uploads
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=barberia_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 3. Docker Compose para Producción
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    image: your-registry/barber-brothers:${VERSION:-latest}
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - MAIL_SERVER=${MAIL_SERVER}
      - MAIL_USERNAME=${MAIL_USERNAME}
      - MAIL_PASSWORD=${MAIL_PASSWORD}
    volumes:
      - uploads:/app/app/static/uploads
    depends_on:
      - db
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/backup:/backup
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - uploads:/var/www/uploads
    depends_on:
      - web

volumes:
  postgres_data:
  uploads:
```

## Variables de Entorno

### 1. Configuración Completa
```bash
# .env.production
# Base de datos
DATABASE_URL=postgresql://user:password@host:5432/database
POSTGRES_USER=barberia_user
POSTGRES_PASSWORD=SecurePassword123!
POSTGRES_DB=barberia_db

# Aplicación
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=False

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=Barber Brothers

# Cloud Storage (opcional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET=barber-brothers-uploads
S3_REGION=us-east-1

# Google Cloud (opcional)
GOOGLE_CLOUD_PROJECT=barber-brothers-prod
INSTANCE_CONNECTION_NAME=project:region:instance
DB_USER=barberia_user
DB_PASS=SecurePassword123!
DB_NAME=barberia_db

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO

# Limits
MAX_CONTENT_LENGTH=16777216  # 16MB
UPLOAD_FOLDER=/app/app/static/uploads
```

### 2. Gestión de Secrets en Kubernetes
```yaml
# k8s/secrets.yml
apiVersion: v1
kind: Secret
metadata:
  name: barber-brothers-secrets
type: Opaque
stringData:
  database-url: postgresql://user:password@postgres:5432/barberia_db
  secret-key: your-super-secret-key
  mail-password: your-mail-password
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: barber-brothers-config
data:
  flask-env: "production"
  mail-server: "smtp.gmail.com"
  mail-port: "587"
  mail-use-tls: "True"
```

## Configuración de Base de Datos

### 1. Configuración para Alta Disponibilidad
```python
# app/config/database.py
class DatabaseConfig:
    # Pool settings para producción
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'max_overflow': 5,
        'pool_pre_ping': True,  # Verificar conexiones antes de usar
    }
    
    # Configuración de timeouts
    SQLALCHEMY_DATABASE_URI = (
        f"{base_url}?"
        f"connect_timeout=10&"
        f"application_name=barber_brothers&"
        f"sslmode=require"
    )
```

### 2. Configuración de Backup Automático
```bash
#!/bin/bash
# scripts/backup-db.sh

# Variables
DB_NAME="barberia_db"
DB_USER="barberia_user"
DB_HOST="localhost"
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --verbose --clean --no-owner --no-privileges \
    > "$BACKUP_DIR/backup_$DATE.sql"

# Comprimir backup
gzip "$BACKUP_DIR/backup_$DATE.sql"

# Limpiar backups antiguos (mantener últimos 7 días)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Subir a cloud storage (ejemplo S3)
aws s3 cp "$BACKUP_DIR/backup_$DATE.sql.gz" \
    s3://barber-brothers-backups/database/
```

### 3. Monitoreo de Base de Datos
```python
# app/utils/db_monitoring.py
import psutil
import sqlalchemy
from flask import current_app

def check_database_health():
    """Verifica el estado de la base de datos"""
    try:
        # Verificar conexión
        from app import db
        db.session.execute(sqlalchemy.text("SELECT 1"))
        
        # Verificar pool de conexiones
        engine = db.engine
        pool = engine.pool
        
        health_info = {
            'status': 'healthy',
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid()
        }
        
        current_app.logger.info(f"Database health: {health_info}")
        return health_info
        
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {str(e)}")
        return {'status': 'unhealthy', 'error': str(e)}
```

## Monitoreo y Logging

### 1. Configuración de Logging Estructurado
```python
# app/utils/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

def setup_logging(app):
    """Configura logging para producción"""
    if app.config.get('FLASK_ENV') == 'production':
        # Handler para stdout (Cloud Logging)
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        
        # Configurar nivel de log
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        handler.setLevel(getattr(logging, log_level))
        
        app.logger.addHandler(handler)
        app.logger.setLevel(getattr(logging, log_level))
        
        # Configurar logging para SQLAlchemy
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
```

### 2. Health Check Endpoint
```python
# app/api/health.py
from flask import Blueprint, jsonify, current_app
from datetime import datetime
import psutil
from app.utils.db_monitoring import check_database_health

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Endpoint de health check para load balancers"""
    try:
        # Verificar base de datos
        db_health = check_database_health()
        
        # Verificar memoria
        memory = psutil.virtual_memory()
        
        # Verificar disco
        disk = psutil.disk_usage('/')
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': current_app.config.get('APP_VERSION', '1.0.0'),
            'database': db_health,
            'system': {
                'memory_usage_percent': memory.percent,
                'disk_usage_percent': (disk.used / disk.total) * 100,
                'cpu_count': psutil.cpu_count()
            }
        }
        
        # Determinar estado general
        if (db_health['status'] != 'healthy' or 
            memory.percent > 90 or 
            (disk.used / disk.total) > 0.9):
            health_status['status'] = 'degraded'
            
        status_code = 200 if health_status['status'] in ['healthy', 'degraded'] else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/ready')
def readiness_check():
    """Readiness probe para Kubernetes"""
    try:
        # Verificar solo que la aplicación esté lista
        from app import db
        db.session.execute(sqlalchemy.text("SELECT 1"))
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        return jsonify({'status': 'not ready', 'error': str(e)}), 503
```

### 3. Métricas Personalizadas
```python
# app/utils/metrics.py
from functools import wraps
import time
from flask import current_app, g

def track_request_metrics(f):
    """Decorator para trackear métricas de requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            status = 'success'
            return result
        except Exception as e:
            status = 'error'
            raise
        finally:
            duration = time.time() - start_time
            current_app.logger.info(
                f"Request metrics",
                extra={
                    'endpoint': f.__name__,
                    'duration_ms': duration * 1000,
                    'status': status
                }
            )
    
    return decorated_function
```

## Certificados SSL/TLS

### 1. Let's Encrypt con Certbot
```bash
# Instalar Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Configurar renovación automática
sudo crontab -e
# Agregar línea:
0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Configuración Nginx con SSL
```nginx
# nginx/nginx.conf
upstream barber_brothers {
    server web:5000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    location / {
        proxy_pass http://barber_brothers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://barber_brothers;
        # ... mismo proxy config
    }

    location /admin/login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://barber_brothers;
        # ... mismo proxy config
    }

    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /uploads/ {
        alias /var/www/uploads/;
        expires 30d;
        add_header Cache-Control "public";
    }
}
```

## CI/CD Pipeline

### 1. GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest coverage
        
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        SECRET_KEY: test-secret-key
      run: |
        coverage run -m pytest
        coverage report
        coverage xml
        
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=sha,prefix={{branch}}-
          
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile.production
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Cloud Run
      uses: google-github-actions/deploy-cloudrun@v1
      with:
        service: barber-brothers-app
        image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:main
        region: us-east1
        env_vars: |
          FLASK_ENV=production
          DATABASE_URL=${{ secrets.DATABASE_URL }}
          SECRET_KEY=${{ secrets.SECRET_KEY }}
```

### 2. Deployment Script
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

# Variables
VERSION=${1:-latest}
ENVIRONMENT=${2:-production}
REGISTRY="your-registry.com"
IMAGE_NAME="barber-brothers"

echo "Deploying version $VERSION to $ENVIRONMENT environment..."

# Build imagen
echo "Building Docker image..."
docker build -f Dockerfile.production -t $REGISTRY/$IMAGE_NAME:$VERSION .

# Push imagen
echo "Pushing image to registry..."
docker push $REGISTRY/$IMAGE_NAME:$VERSION

# Deploy según el entorno
case $ENVIRONMENT in
  "gcp")
    echo "Deploying to Google Cloud Run..."
    gcloud run deploy barber-brothers-app \
      --image $REGISTRY/$IMAGE_NAME:$VERSION \
      --platform managed \
      --region us-east1 \
      --allow-unauthenticated
    ;;
  "aws")
    echo "Deploying to AWS ECS..."
    aws ecs update-service \
      --cluster barber-brothers-cluster \
      --service barber-brothers-service \
      --force-new-deployment
    ;;
  "azure")
    echo "Deploying to Azure Container Instances..."
    az container create \
      --resource-group rg-barber-brothers \
      --name barber-brothers-app \
      --image $REGISTRY/$IMAGE_NAME:$VERSION
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
    ;;
esac

echo "Deployment completed successfully!"
```

## Consideraciones de Seguridad

### 1. Configuración de Firewall
```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Reglas específicas para PostgreSQL (solo desde app servers)
sudo ufw allow from 10.0.1.0/24 to any port 5432
```

### 2. Hardening de PostgreSQL
```sql
-- postgresql.conf
listen_addresses = 'localhost,10.0.1.10'  -- Solo IPs específicas
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
```

### 3. Variables de Entorno Seguras
```python
# app/config/security.py
import os
from cryptography.fernet import Fernet

class SecureConfig:
    @staticmethod
    def decrypt_env_var(encrypted_value):
        """Desencripta variables de entorno sensibles"""
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY not found")
        
        f = Fernet(key.encode())
        return f.decrypt(encrypted_value.encode()).decode()
    
    @staticmethod
    def get_secure_config():
        return {
            'SECRET_KEY': SecureConfig.decrypt_env_var(
                os.environ.get('ENCRYPTED_SECRET_KEY')
            ),
            'DATABASE_PASSWORD': SecureConfig.decrypt_env_var(
                os.environ.get('ENCRYPTED_DB_PASSWORD')
            )
        }
```

## Troubleshooting

### 1. Problemas Comunes y Soluciones

#### Conexión a Base de Datos
```bash
# Verificar conectividad
pg_isready -h your-db-host -p 5432 -U your-user

# Test de conexión desde aplicación
python -c "
import psycopg2
try:
    conn = psycopg2.connect('your-connection-string')
    print('Connection successful')
    conn.close()
except Exception as e:
    print(f'Connection failed: {e}')
"
```

#### Problemas de Memoria
```bash
# Monitorear uso de memoria
docker stats

# Verificar logs del contenedor
docker logs container-name --tail 100

# Analizar heap de Python
pip install memory_profiler
python -m memory_profiler your_script.py
```

#### Problemas de Performance
```python
# app/utils/profiler.py
from flask import request, g
import time

@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    diff = time.time() - g.start_time
    if diff > 1.0:  # Log requests > 1 segundo
        current_app.logger.warning(
            f"Slow request: {request.endpoint} took {diff:.2f}s"
        )
    return response
```

### 2. Monitoring Dashboard
```python
# app/admin/monitoring.py
from flask import Blueprint, render_template, jsonify
from app.utils.db_monitoring import check_database_health
import psutil

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/admin/monitoring')
def monitoring_dashboard():
    """Dashboard de monitoreo para administradores"""
    system_info = {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory': psutil.virtual_memory()._asdict(),
        'disk': psutil.disk_usage('/')._asdict(),
        'network': psutil.net_io_counters()._asdict()
    }
    
    db_health = check_database_health()
    
    return render_template('admin/monitoring.html',
                         system_info=system_info,
                         db_health=db_health)

@monitoring_bp.route('/admin/monitoring/api')
def monitoring_api():
    """API para datos de monitoreo en tiempo real"""
    return jsonify({
        'timestamp': datetime.utcnow().isoformat(),
        'system': {
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent
        },
        'database': check_database_health()
    })
```

## Conclusión

Este manual proporciona una guía completa para el despliegue de la aplicación Barber Brothers en diferentes plataformas cloud. Las configuraciones incluyen:

- **Escalabilidad**: Configuraciones para manejar crecimiento de tráfico
- **Alta Disponibilidad**: Redundancia y failover automático
- **Seguridad**: Mejores prácticas de seguridad implementadas
- **Monitoreo**: Observabilidad completa del sistema
- **Automatización**: CI/CD pipelines para deployments seguros

Seleccione la plataforma que mejor se adapte a sus necesidades y siga las instrucciones específicas para esa plataforma.
