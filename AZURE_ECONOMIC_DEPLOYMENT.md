# Guía de Despliegue Económico en Azure App Service (Plan F1)

Esta guía te ayudará a desplegar tu aplicación Flask de Barbería en Azure App Service usando el plan gratuito F1, junto con una base de datos PostgreSQL en una VM económica B1ls.

## Costo Mensual Estimado

| Servicio | Nivel | Costo Mensual (USD) |
|----------|-------|----------------------|
| App Service | F1 (Free) | $0 |
| VM para PostgreSQL | B1ls | ~$4.67 |
| **Total** | | **~$4.67/mes** |

## Pasos para el Despliegue

### 1. Crear recursos en Azure

Ejecuta los siguientes comandos en PowerShell después de instalar la CLI de Azure:

```powershell
# Iniciar sesión en Azure
az login

# Crear grupo de recursos
az group create --name barberia-rg --location eastus

# Crear plan de App Service F1 (GRATUITO)
az appservice plan create --name barberia-free-plan --resource-group barberia-rg --sku F1 --is-linux

# Crear la aplicación web
az webapp create --resource-group barberia-rg --plan barberia-free-plan --name barberia-app --runtime "PYTHON:3.11"

# Crear VM económica para PostgreSQL
$VM_PASSWORD = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})
$VM_NAME = "barberia-db-vm"

# Crear VM pequeña
az vm create --resource-group barberia-rg --name $VM_NAME --image UbuntuLTS --size Standard_B1ls --admin-username azureuser --admin-password $VM_PASSWORD

# Abrir puerto PostgreSQL
az vm open-port --resource-group barberia-rg --name $VM_NAME --port 5432

# Obtener IP de la VM
$VM_IP = az vm show -d --resource-group barberia-rg --name $VM_NAME --query publicIps -o tsv

# Guardar credenciales en un archivo seguro
"VM IP: $VM_IP`nVM User: azureuser`nVM Password: $VM_PASSWORD" | Out-File -FilePath "azure-vm-credentials.txt"

# Configurar variables de entorno en App Service
az webapp config appsettings set --resource-group barberia-rg --name barberia-app --settings DB_USER=barberia_user DB_PASS=barberia_password DB_NAME=barberia_db DB_HOST=$VM_IP DB_PORT=5432 FLASK_APP=wsgi.py FLASK_ENV=production
```

### 2. Configurar PostgreSQL en la VM

1. Conectarse a la VM:
   ```powershell
   ssh azureuser@$VM_IP
   ```

2. Copiar el script de configuración:
   ```powershell
   # Desde tu máquina local
   scp scripts/setup-postgres-economic.sh azureuser@$VM_IP:~/
   ```

3. Ejecutar el script en la VM:
   ```bash
   # En la VM
   chmod +x setup-postgres-economic.sh
   ./setup-postgres-economic.sh
   ```

### 3. Configurar GitHub Actions para despliegue

1. Crear un Service Principal para autenticación:
   ```powershell
   # Obtener ID de suscripción
   $subscriptionId = $(az account show --query id -o tsv)
   
   # Crear service principal
   az ad sp create-for-rbac --name "barberia-app-github" --role contributor --scopes /subscriptions/$subscriptionId/resourceGroups/barberia-rg --sdk-auth
   ```

2. Copiar la salida JSON del comando anterior.

3. Añadir el secreto a GitHub:
   - Ve a tu repositorio en GitHub
   - Configuración → Secrets → Actions
   - Nuevo secreto con nombre `AZURE_CREDENTIALS` y valor el JSON del paso anterior

4. Hacer commit y push a GitHub:
   ```powershell
   git add .
   git commit -m "Configuración para despliegue económico en Azure App Service"
   git push
   ```

### 4. Migrar datos a la nueva base de datos

1. Exportar datos de tu base de datos actual:
   ```powershell
   # Si tienes una base de datos PostgreSQL local
   pg_dump -U tu_usuario -d barberia_db > barberia_backup.sql
   ```

2. Importar datos a la VM:
   ```powershell
   # Copiar el archivo a la VM
   scp barberia_backup.sql azureuser@$VM_IP:~/
   
   # Conectarse a la VM
   ssh azureuser@$VM_IP
   
   # Importar datos
   psql -U barberia_user -d barberia_db < barberia_backup.sql
   ```

## Limitaciones del Plan F1

- **60 minutos de CPU al día** (suficiente para uso ligero)
- **1GB de RAM y almacenamiento**
- Sin dominio personalizado (se usará barberia-app.azurewebsites.net)
- La aplicación se hibernará después de 20 minutos de inactividad

## Consejos para Optimizar Rendimiento

1. **Implementar caché agresivamente**:
   - Caché de resultados de consultas frecuentes
   - Caché del lado del cliente para activos estáticos

2. **Minimizar carga de CPU**:
   - Reducir el número de consultas a la base de datos
   - Optimizar imágenes antes de subirlas

3. **Monitorear uso**:
   - Revisar regularmente el uso de CPU en el portal de Azure
   - Si te acercas al límite, considera implementar un sistema de cola para tareas pesadas

## Escalado Futuro

Si tu negocio crece, puedes escalar fácilmente a:
- Plan Basic B1 ($13/mes) para tener más CPU y RAM
- Considerar Azure Database for PostgreSQL ($25+/mes) para mayor fiabilidad
