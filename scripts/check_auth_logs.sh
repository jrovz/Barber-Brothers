#!/bin/bash

# Script para verificar logs de Cloud Run
echo "Obteniendo logs recientes de Cloud Run para la aplicación barberia-app"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app AND severity>=ERROR" --limit=20 --format="table(timestamp,severity,textPayload)"

# O usar este comando para filtrar específicamente los errores de autenticación
echo "Filtrando logs relacionados con autenticación/login"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app AND (textPayload:auth OR textPayload:login OR textPayload:session)" --limit=10
