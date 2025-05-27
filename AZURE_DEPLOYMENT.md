# Documentación de Despliegue en Azure

## Arquitectura

Esta aplicación de barbería está desplegada en Azure utilizando:

- **Azure App Service (Plan F1, gratuito)**: Aloja la aplicación Flask
- **VM Azure B1ls**: Ejecuta PostgreSQL para la base de datos
- **Azure Blob Storage**: Almacena archivos estáticos (imágenes, CSS, JS)

## Acceso a los Recursos

- **Aplicación**: https://barberia-app.azurewebsites.net
- **Base de Datos**: VM PostgreSQL en IP_PRIVADA_VM (accesible solo desde App Service)
- **Panel de Administración**: https://barberia-app.azurewebsites.net/admin

## Credenciales y Secretos

Las credenciales de acceso están almacenadas como variables de configuración en Azure App Service:

- Variables de base de datos (DB_USER, DB_PASS, etc.)
- Claves de Azure Storage
- SECRET_KEY de Flask

## Mantenimiento

### Base de Datos
- La VM PostgreSQL tiene un script de mantenimiento automático que se ejecuta diariamente
- Los backups se almacenan en la VM en `/home/azureuser/backups`
- Se mantienen los últimos 7 días de backups

### Despliegue
- El despliegue se realiza automáticamente mediante GitHub Actions
- Cualquier cambio a la rama `main` desencadenará un nuevo despliegue

### Monitoreo
- Revisar el panel de Azure para App Service
- Logs disponibles en Azure App Service en `LogFiles`
- Para la VM, revisar `/var/log/postgresql/postgresql-*.log`

## Limitaciones del Plan F1

- **60 minutos de CPU al día**: La aplicación puede volverse lenta si se excede
- **1GB de RAM**: Monitorear el uso de memoria
- **1GB de almacenamiento**: Mantener los archivos estáticos en Blob Storage

## Contactos de Soporte

- Para problemas con Azure: Azure Support
- Para problemas con la aplicación: [Tu información de contacto]
