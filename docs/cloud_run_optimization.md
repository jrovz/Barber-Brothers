# Optimización de Cloud Run para la Aplicación de Barbería

Este documento proporciona recomendaciones para optimizar el rendimiento, la seguridad y los costos del servicio Cloud Run para la aplicación de barbería.

## Rendimiento

### 1. Configuración de recursos

Ajusta los recursos asignados al servicio:

```bash
gcloud run services update barberia-app \
  --memory=512Mi \
  --cpu=1 \
  --region=us-central1
```

### 2. Optimización de concurrencia

Aumenta la concurrencia máxima para manejar más solicitudes por instancia:

```bash
gcloud run services update barberia-app \
  --concurrency=80 \
  --region=us-central1
```

### 3. Configuración de escalado automático

Configura el escalado automático para responder rápidamente a picos de tráfico:

```bash
gcloud run services update barberia-app \
  --min-instances=1 \
  --max-instances=10 \
  --region=us-central1
```

### 4. Optimización de la inicialización en frío

Para reducir el tiempo de inicialización en frío:

- Mantener al menos una instancia activa (`--min-instances=1`)
- Optimizar el tamaño de la imagen del contenedor
- Optimizar el tiempo de inicio de la aplicación
- Usar Cloud SQL Proxy para mantener conexiones de base de datos

## Seguridad

### 1. Uso de Secrets Manager

Asegúrate de que todas las credenciales sensibles se almacenen en Secrets Manager:

```bash
# Comprobar secretos existentes
gcloud secrets list

# Crear nuevos secretos si es necesario
echo "valor_secreto" | gcloud secrets create nombre_secreto --data-file=-

# Actualizar servicio para usar el secreto
gcloud run services update barberia-app \
  --set-secrets="NOMBRE_VARIABLE=nombre_secreto:latest" \
  --region=us-central1
```

### 2. Configuración de IAM

Revisa y ajusta los permisos de IAM para el servicio:

```bash
# Listar permisos actuales
gcloud run services get-iam-policy barberia-app --region=us-central1

# Configurar acceso público (si es necesario)
gcloud run services add-iam-policy-binding barberia-app \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --region=us-central1

# O restringir acceso solo a usuarios autenticados
gcloud run services remove-iam-policy-binding barberia-app \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --region=us-central1
```

### 3. Configuración de VPC Connector

Ver el documento `vpc_connector_setup.md` para detalles sobre cómo configurar un VPC Connector para comunicación segura con Cloud SQL y otros servicios internos.

## Optimización de Costos

### 1. Configuración de escalado a cero

Para minimizar costos, permite que el servicio escale a cero cuando no hay tráfico:

```bash
gcloud run services update barberia-app \
  --min-instances=0 \
  --region=us-central1
```

### 2. Ajuste de recursos

Monitorea el uso de recursos y ajusta según sea necesario:

```bash
# Reducir memoria si está sobredimensionada
gcloud run services update barberia-app \
  --memory=256Mi \
  --region=us-central1
```

### 3. Optimización de CPU

Configura la CPU para que escale según la carga:

```bash
gcloud run services update barberia-app \
  --cpu=1 \
  --cpu-boost \
  --region=us-central1
```

## Monitoreo y Diagnóstico

### 1. Configuración de Cloud Monitoring

Configura alertas basadas en métricas clave:

- Latencia de solicitudes
- Errores HTTP 5xx
- Uso de CPU y memoria
- Número de instancias

### 2. Configuración de Cloud Logging

Asegúrate de que los logs se estén capturando correctamente:

```bash
# Ver logs del servicio
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app" --limit=10
```

### 3. Uso del script de diagnóstico

Utiliza el script `scripts/cloud_run_diagnosis.py` para diagnosticar problemas comunes en la configuración de Cloud Run.

## Despliegue continuo

### 1. Configuración de pruebas antes del despliegue

Actualiza el archivo `cloudbuild.yaml` para incluir pruebas automáticas antes del despliegue.

### 2. Configuración de despliegue gradual

Implementa despliegues graduales para minimizar el impacto de los cambios:

```bash
gcloud run services update-traffic barberia-app \
  --to-revisions=REVISION=50 \
  --to-latest=50 \
  --region=us-central1
```

### 3. Configuración de rollback automático

Implementa rollback automático en caso de fallos en el despliegue.
