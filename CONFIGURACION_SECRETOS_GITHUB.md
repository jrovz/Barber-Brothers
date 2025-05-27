# Configuración de Secretos para GitHub Actions (Actualizado)

Este documento explica cómo solucionar el error de autenticación en GitHub Actions para el despliegue a Azure App Service.

## Error encontrado

```
Error: Login failed with Error: Using auth-type: SERVICE_PRINCIPAL. Not all values are present. Ensure 'client-id' and 'tenant-id' are supplied.
```

## Solución 1: Usar Publish Profile (Recomendado)

Esta es la forma más sencilla y ya está configurada en el archivo de workflow:

1. **Obtener el perfil de publicación**:
   - Inicia sesión en el [Portal de Azure](https://portal.azure.com)
   - Navega a tu App Service (`barberia-app`)
   - En el menú de la izquierda, ve a "Overview" (Información general)
   - Haz clic en "Get publish profile" (Obtener perfil de publicación)
   - Se descargará un archivo XML

2. **Añadir el secreto a GitHub**:
   - Ve a tu repositorio en GitHub
   - Haz clic en "Settings" (Configuración)
   - En el menú lateral, haz clic en "Secrets and variables" > "Actions"
   - Haz clic en "New repository secret"
   - Nombre: `AZURE_WEBAPP_PUBLISH_PROFILE`
   - Valor: Copia y pega todo el contenido del archivo XML descargado
   - Haz clic en "Add secret"

## Solución 2: Configurar credenciales separadas (Alternativa)

Si prefieres usar el método de login con service principal, necesitas configurar cuatro secretos separados:

1. **Crear un Service Principal**:
   ```powershell
   # Asegúrate de usar el ID de suscripción correcto
   $subscriptionId = $(az account show --query id -o tsv)
   
   # Crear el service principal
   az ad sp create-for-rbac --name "barberia-app-github" --role contributor --scopes /subscriptions/$subscriptionId/resourceGroups/barberia-rg
   ```

2. **Añadir los secretos a GitHub**:
   La salida del comando anterior tendrá este formato:
   ```json
   {
     "appId": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
     "displayName": "barberia-app-github",
     "password": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
     "tenant": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
   }
   ```

   Debes crear cuatro secretos en GitHub:
   - `AZURE_CLIENT_ID`: Valor de "appId"
   - `AZURE_CLIENT_SECRET`: Valor de "password"
   - `AZURE_TENANT_ID`: Valor de "tenant"
   - `AZURE_SUBSCRIPTION_ID`: Tu ID de suscripción de Azure (puedes obtenerlo con `az account show --query id -o tsv`)

3. **Modificar el workflow**:
   - Edita el archivo `.github/workflows/azure-webapp-deploy.yml`
   - Comenta la sección de "Opción 1" y descomenta la sección de "Opción 2"

## ¿Cuál solución elegir?

La **Solución 1** (Publish Profile) es más sencilla y requiere configurar solo un secreto.

La **Solución 2** es más flexible si necesitas realizar más operaciones en Azure como parte de tu flujo de trabajo, pero requiere configurar cuatro secretos y mantenerlos actualizados.

---

Después de configurar los secretos, ejecuta nuevamente el workflow manualmente desde la sección "Actions" de tu repositorio de GitHub.
