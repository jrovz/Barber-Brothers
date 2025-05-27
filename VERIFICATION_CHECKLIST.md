# Lista de Verificación Post-Despliegue

## Funcionalidad Básica
- [ ] La página principal carga correctamente
- [ ] Las imágenes y estilos CSS se cargan correctamente
- [ ] El endpoint de health (/api/health) devuelve status 200

## Base de Datos
- [ ] La conexión a la base de datos funciona
- [ ] Los datos existentes son accesibles
- [ ] Se pueden crear nuevos registros

## Autenticación y Administración
- [ ] El formulario de login funciona
- [ ] Se puede acceder al panel administrativo
- [ ] Se pueden crear/editar/eliminar registros

## Gestión de Archivos
- [ ] La subida de imágenes funciona correctamente
- [ ] Las imágenes subidas son accesibles

## Reservas y Funcionamiento del Negocio
- [ ] El formulario de reserva de citas funciona
- [ ] Se pueden ver los servicios disponibles
- [ ] Se pueden ver los barberos y sus horarios

## Rendimiento
- [ ] Los tiempos de carga son aceptables
- [ ] La aplicación responde bien incluso con múltiples solicitudes

## Seguridad
- [ ] HTTPS funciona correctamente
- [ ] Las áreas protegidas requieren autenticación
- [ ] Las contraseñas y datos sensibles están protegidos

## Pasos para Resolver Problemas Comunes

### Si la aplicación no carga:
1. Verificar que la aplicación está en estado "Running" en Azure Portal
2. Revisar los logs de aplicación en Azure
3. Verificar que las variables de entorno están configuradas correctamente

### Si hay problemas con la base de datos:
1. Verificar que la VM está ejecutándose
2. Comprobar que las credenciales de base de datos son correctas
3. Verificar la conectividad desde App Service a la VM

### Si hay problemas con las imágenes o archivos:
1. Verificar la configuración de almacenamiento
2. Comprobar permisos en las carpetas de uploads
3. Verificar que las rutas a los archivos son correctas
