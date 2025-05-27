# Lista de Verificación para Implementación en Azure

## Preparación Inicial

- [ ] Instalar Azure CLI (`winget install -e --id Microsoft.AzureCLI`)
- [ ] Iniciar sesión en Azure (`az login`)
- [ ] Crear cuenta de GitHub si aún no la tienes (para CI/CD)
- [ ] Clonar el repositorio localmente si no lo has hecho

## Creación de Recursos

- [ ] Ejecutar script PowerShell para crear recursos de Azure
- [ ] Verificar que se haya creado:
  - [ ] Grupo de recursos (barberia-rg)
  - [ ] App Service Plan (F1 gratuito)
  - [ ] App Service (barberia-app)
  - [ ] Cuenta de almacenamiento y contenedor Blob
  - [ ] VM para PostgreSQL (B1ls)

## Configuración de Base de Datos

- [ ] Transferir script setup-postgres.sh a la VM
- [ ] Ejecutar setup-postgres.sh en la VM
- [ ] Verificar que PostgreSQL acepta conexiones:
  - [ ] Probar conexión: `psql -h [IP_VM] -U barberia_user -d barberia_db`
- [ ] Exportar datos de base de datos actual (si existe)
- [ ] Importar datos a la nueva base de datos en VM

## Adaptación del Código

- [ ] Verificar que azure_connection_pg.py esté correctamente configurado
- [ ] Verificar que azure_storage.py esté correctamente configurado
- [ ] Actualizar archivos de configuración para detectar entorno Azure
- [ ] Probar conexión a base de datos localmente

## Configuración de CI/CD

- [ ] Configurar secreto AZURE_WEBAPP_PUBLISH_PROFILE en GitHub:
  - [ ] Ir a Azure Portal > App Service > Deployment Center > Manage publish profile
  - [ ] Descargar el perfil de publicación
  - [ ] Añadir como secreto en GitHub (Settings > Secrets > New repository secret)
- [ ] Verificar que el flujo de trabajo azure-deploy.yml esté configurado
- [ ] Realizar un commit de prueba para verificar el despliegue automático

## Despliegue Manual (opcional)

- [ ] Ejecutar script deploy-to-azure.ps1 para despliegue manual
- [ ] Verificar que la aplicación se ha desplegado correctamente
- [ ] Acceder a la aplicación en https://barberia-app.azurewebsites.net

## Pruebas Post-Despliegue

- [ ] Verificar funcionalidad de la aplicación
  - [ ] Acceso a la página principal
  - [ ] Creación de citas
  - [ ] Panel de administración
  - [ ] Carga y visualización de imágenes
- [ ] Verificar logs en Azure Portal
- [ ] Verificar que la base de datos está funcionando correctamente

## Monitoreo y Mantenimiento

- [ ] Configurar script de mantenimiento db_maintenance.sh en la VM
- [ ] Configurar cron job para ejecutar el mantenimiento diario
- [ ] Configurar alertas básicas en Azure para VM y App Service

## Optimización

- [ ] Revisar rendimiento y ajustar configuración si es necesario
- [ ] Implementar estrategias de caché para mejorar rendimiento
- [ ] Revisar consumo de recursos y optimizar según sea necesario
