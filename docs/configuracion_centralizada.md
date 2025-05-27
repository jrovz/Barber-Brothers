# Configuración Centralizada en Barber Brothers

## Introducción

Este documento describe la implementación del sistema de configuración centralizada en el proyecto Barber Brothers, que unifica la gestión de:
- Regiones de GCP
- Conexiones a bases de datos
- Secretos y credenciales

Esta arquitectura reemplaza el enfoque anterior donde cada script manejaba individualmente sus configuraciones, reduciendo la duplicación de código y mejorando la seguridad al eliminar credenciales hardcodeadas.

## Estructura Principal

### Módulo de Configuración Centralizada

El núcleo de la implementación es el módulo `config_manager.py` ubicado en `app/utils/config_manager.py`. Este módulo proporciona:

- **Funciones para obtener configuración de GCP**:
  - `get_project_id()`: Obtiene el ID del proyecto GCP
  - `get_gcp_region()`: Obtiene la región de GCP
  - `get_instance_name()`: Obtiene el nombre de la instancia
  - `get_instance_connection_name()`: Construye el nombre completo de conexión de instancia

- **Funciones para manejo de secretos**:
  - `get_secret()`: Obtiene secretos desde Secret Manager
  - `get_db_credentials()`: Obtiene credenciales de base de datos
  - `get_mail_credentials()`: Obtiene credenciales de correo

- **Funciones de construcción de URLs de conexión**:
  - `build_database_url()`: Construye URL de conexión para SQLAlchemy
  
- **Funciones de utilidad**:
  - `is_production()`: Determina si se está ejecutando en entorno de producción

## Configuración de Secret Manager

### Scripts de Configuración

Se proporcionan dos scripts para configurar Secret Manager:

1. **setup_secrets.sh** (Linux/Mac):
   ```bash
   ./scripts/setup_secrets.sh
   ```

2. **setup_secrets.ps1** (Windows):
   ```powershell
   .\scripts\setup_secrets.ps1
   ```

Estos scripts guían al usuario para:
- Configurar el proyecto GCP
- Crear los secretos necesarios
- Almacenar credenciales de base de datos
- Almacenar credenciales de correo
- Verificar que los secretos se crearon correctamente

### Secretos Gestionados

| Secreto | Descripción | Uso |
|---------|-------------|-----|
| `db-user` | Usuario de base de datos | Conexión a PostgreSQL |
| `db-pass` | Contraseña de base de datos | Conexión a PostgreSQL |
| `db-name` | Nombre de la base de datos | Conexión a PostgreSQL |
| `mail-user` | Usuario de correo | Envío de correos |
| `mail-pass` | Contraseña de correo | Envío de correos |
| `admin-email` | Correo de administrador | Notificaciones administrativas |

## Verificación de la Implementación

Para verificar que la implementación se ha realizado correctamente, ejecute:

```bash
python verify_config_migration.py
```

Este script verifica:
- La correcta importación de módulos
- El funcionamiento del módulo de configuración centralizada
- La actualización de scripts principales
- La existencia de scripts de configuración de Secret Manager

## Dependencias

Para instalar todas las dependencias necesarias, ejecute:

```bash
python scripts/update_dependencies.py
```

o en Windows:

```powershell
.\scripts\update_dependencies.ps1
```

## Migración de Scripts Existentes

Al crear nuevos scripts o modificar los existentes, siga estas pautas:

1. **Importar el módulo de configuración**:
   ```python
   from app.utils.config_manager import get_project_id, get_gcp_region, get_db_credentials
   ```

2. **Obtener credenciales de manera segura**:
   ```python
   # En lugar de hardcodear credenciales
   db_credentials = get_db_credentials()
   db_user = db_credentials["user"]
   db_pass = db_credentials["password"]
   db_name = db_credentials["database"]
   ```

3. **Construir URLs de conexión**:
   ```python
   from app.utils.config_manager import build_database_url
   
   # Obtener URL de conexión para SQLAlchemy
   db_url = build_database_url(db_credentials)
   ```

4. **Detectar entorno**:
   ```python
   from app.utils.config_manager import is_production
   
   if is_production():
       # Lógica para entorno de producción
   else:
       # Lógica para entorno de desarrollo
   ```

## Beneficios de la Configuración Centralizada

- **Seguridad mejorada**: Eliminación de credenciales hardcodeadas
- **Mantenibilidad**: Cambios de configuración en un solo lugar
- **Consistencia**: Mismo comportamiento en todos los scripts
- **Flexibilidad**: Fácil cambio entre entornos (desarrollo/producción)
- **Reducción de código duplicado**: Menor probabilidad de errores
