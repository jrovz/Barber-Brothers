# Configuración de Secretos para GitHub Actions

Para que el despliegue a Azure App Service funcione correctamente, necesitas configurar los siguientes secretos en tu repositorio de GitHub:

## 1. AZURE_WEBAPP_PUBLISH_PROFILE

Este es el método recomendado y más seguro para desplegar a Azure App Service.

### Pasos para obtener y configurar el perfil de publicación:

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

## 2. Método alternativo: AZURE_CREDENTIALS

Si prefieres usar el método de inicio de sesión de Azure en lugar del perfil de publicación, necesitarás crear un service principal y configurar el secreto AZURE_CREDENTIALS.

### Pasos para configurar AZURE_CREDENTIALS:

1. **Instalar la CLI de Azure** si aún no la tienes: [Instrucciones de instalación](https://docs.microsoft.com/es-es/cli/azure/install-azure-cli)

2. **Iniciar sesión en Azure**:
   ```powershell
   az login
   ```

3. **Crear un Service Principal**:
   ```powershell
   # Asegúrate de usar el ID de suscripción correcto
   $subscriptionId = $(az account show --query id -o tsv)
   
   # Crear el service principal
   az ad sp create-for-rbac --name "barberia-app-github" --role contributor --scopes /subscriptions/$subscriptionId/resourceGroups/barberia-rg --sdk-auth
   ```

4. **Copiar la salida JSON** del comando anterior

5. **Añadir el secreto a GitHub**:
   - Ve a tu repositorio en GitHub
   - Haz clic en "Settings" (Configuración)
   - En el menú lateral, haz clic en "Secrets and variables" > "Actions"
   - Haz clic en "New repository secret"
   - Nombre: `AZURE_CREDENTIALS`
   - Valor: Pega la salida JSON del paso anterior
   - Haz clic en "Add secret"

6. **Actualizar el flujo de trabajo**: Descomenta la sección alternativa en el archivo `.github/workflows/azure-webapp-deploy.yml`

## Nota importante

Si configuraste Azure Static Web Apps previamente, es posible que ya tengas un secreto similar en tu repositorio. Sin embargo, para App Service necesitas específicamente el perfil de publicación del App Service o las credenciales de un service principal con permisos en el resource group correcto.

---

Una vez configurado el secreto apropiado, el flujo de trabajo de GitHub Actions debería funcionar correctamente y desplegar tu aplicación a Azure App Service.
