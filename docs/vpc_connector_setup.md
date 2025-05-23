# Configuración de VPC Connector para Cloud Run

El VPC Connector permite que los servicios de Cloud Run se comuniquen de manera privada y segura con otros recursos dentro de tu red privada, como Cloud SQL y otros servicios internos de GCP.

## 1. Crear una red VPC

```bash
# Crear una red VPC para el proyecto
gcloud compute networks create barberia-vpc --subnet-mode=custom
```

## 2. Crear una subred para el VPC Connector

```bash
# Crear una subred para el conector VPC en la región us-central1
gcloud compute networks subnets create barberia-connector-subnet \
  --network=barberia-vpc \
  --region=us-central1 \
  --range=10.8.0.0/28
```

## 3. Crear el VPC Connector

```bash
# Crear el conector VPC en la región us-central1
gcloud compute networks vpc-access connectors create barberia-vpc-connector \
  --network=barberia-vpc \
  --region=us-central1 \
  --range=10.8.0.0/28 \
  --min-instances=2 \
  --max-instances=10
```

## 4. Actualizar el servicio Cloud Run para usar el VPC Connector

```bash
# Actualizar el servicio Cloud Run para usar el VPC Connector
gcloud run services update barberia-app \
  --vpc-connector=barberia-vpc-connector \
  --region=us-central1
```

## 5. Configurar Cloud SQL para utilizarse con el VPC Connector

```bash
# Configurar Cloud SQL para aceptar conexiones desde la red VPC
gcloud sql instances patch barberia-db \
  --private-network=barberia-vpc

# Deshabilitar la IP pública para mejorar la seguridad (opcional)
# gcloud sql instances patch barberia-db \
#   --no-assign-ip
```

## 6. Verificar la configuración

```bash
# Verificar el estado del conector VPC
gcloud compute networks vpc-access connectors describe barberia-vpc-connector \
  --region=us-central1
```

## Beneficios de usar VPC Connector

- Mayor seguridad al evitar exponer servicios internos a la Internet pública
- Mejor rendimiento para la comunicación entre servicios
- Reducción del riesgo de ataques externos
- Cumplimiento de requisitos regulatorios para la protección de datos
