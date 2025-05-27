# Solución al problema de autenticación en GitHub Actions

## Problema encontrado

Estás experimentando un error de autenticación en GitHub Actions al intentar desplegar tu aplicación a Azure App Service:

```
Error: Login failed with Error: Using auth-type: SERVICE_PRINCIPAL. Not all values are present. Ensure 'client-id' and 'tenant-id' are supplied.
```

## Causa del problema

El error se debe a que la acción `azure/login@v1` está intentando autenticarse usando un Service Principal (`SERVICE_PRINCIPAL`), pero no se están proporcionando todos los valores necesarios en el secreto `AZURE_CREDENTIALS`.

## Solución paso a paso

Hemos modificado el archivo de workflow para ofrecer dos opciones de autenticación. A continuación se detallan los pasos para implementar cada una:

### Opción 1: Usar Publish Profile (Recomendada)

Este método es más sencillo y requiere configurar solo un secreto:

1. **Ejecuta el script de ayuda** para obtener el perfil de publicación:
   ```powershell
   .\scripts\obtener-publish-profile.ps1
   ```
   
2. El script te guiará para:
   - Iniciar sesión en Azure (si es necesario)
   - Seleccionar la suscripción correcta
   - Seleccionar tu App Service
   - Descargar el perfil de publicación

3. **Sigue las instrucciones** que aparecerán al final del script para añadir el secreto `AZURE_WEBAPP_PUBLISH_PROFILE` a tu repositorio de GitHub.

4. **Ejecuta nuevamente el workflow** desde la pestaña Actions de GitHub.

### Opción 2: Configurar Service Principal con credenciales separadas

Esta opción requiere configurar cuatro secretos, pero puede ser más flexible si necesitas realizar otras operaciones en Azure:

1. **Ejecuta el script de ayuda** para crear el Service Principal:
   ```powershell
   .\scripts\configurar-service-principal.ps1
   ```

2. El script te guiará para:
   - Iniciar sesión en Azure (si es necesario)
   - Seleccionar la suscripción correcta
   - Seleccionar o crear el grupo de recursos
   - Crear un Service Principal con los permisos necesarios

3. **Sigue las instrucciones** que aparecerán al final del script para añadir los cuatro secretos a tu repositorio de GitHub.

4. **Modifica el archivo de workflow** para usar esta opción:
   - Edita el archivo `.github/workflows/azure-webapp-deploy.yml`
   - Comenta la sección de "Opción 1" y descomenta la sección de "Opción 2"

5. **Ejecuta nuevamente el workflow** desde la pestaña Actions de GitHub.

## Recomendación

La **Opción 1 (Publish Profile)** es la más sencilla y es la configuración por defecto en el archivo de workflow actualizado. Es suficiente para la mayoría de los casos de uso y requiere menos mantenimiento.

## Documentación adicional

Para más detalles sobre la configuración de secretos y la autenticación en GitHub Actions, consulta:

- [CONFIGURACION_SECRETOS_GITHUB.md](./CONFIGURACION_SECRETOS_GITHUB.md) - Documentación detallada sobre las opciones de configuración
- [Documentación oficial de Azure Login Action](https://github.com/Azure/login#readme)
- [Documentación oficial de Azure WebApp Deploy Action](https://github.com/Azure/webapps-deploy)

## Después de solucionar el problema

Una vez que hayas solucionado el problema de autenticación y el despliegue sea exitoso, verifica que la aplicación funciona correctamente ejecutando:

```powershell
python scripts\verify_azure_deployment.py
```

Este script verificará que todos los endpoints principales de tu aplicación están funcionando correctamente.
