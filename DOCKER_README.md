# Barber Brothers - Instrucciones de Dockerización

Este documento explica cómo utilizar Docker para ejecutar la aplicación Barber Brothers.

## Requisitos Previos

- Docker
- Docker Compose

## Estructura de Dockerización

Los archivos clave para la dockerización son:

- `Dockerfile`: Define cómo se construye la imagen de la aplicación
- `docker-compose.yml`: Configura los servicios (aplicación web y base de datos)
- `.dockerignore`: Excluye archivos innecesarios de la imagen
- `wait-for-postgres.sh`: Script para esperar a que la base de datos esté disponible
- `docker-entrypoint.sh`: Script de inicialización de la aplicación

## Instrucciones de Uso

### Construcción y Ejecución

1. **Primera vez**: Construir las imágenes e iniciar los contenedores:

```bash
docker-compose up --build
```

2. **Uso posterior**: Iniciar los contenedores sin reconstruir:

```bash
docker-compose up
```

3. **Ejecutar en segundo plano**:

```bash
docker-compose up -d
```

### Gestión de la Base de Datos

- **Ejecutar migraciones manualmente**:

```bash
docker-compose exec web flask db upgrade
```

- **Acceder a la base de datos PostgreSQL**:

```bash
docker-compose exec db psql -U postgres -d barberia_db
```

### Detener los Contenedores

```bash
docker-compose down
```

Para eliminar también los volúmenes (esto borrará los datos de la base de datos):

```bash
docker-compose down -v
```

## Consideraciones de Seguridad

- Las credenciales están incorporadas en el `docker-compose.yml` para desarrollo
- Para producción, se recomienda usar variables de entorno o Docker Secrets

## Despliegue en Azure

Para desplegar esta aplicación en Azure Container Instances o Azure App Service:

1. Construir la imagen:

```bash
docker build -t barberbrothers:latest .
```

2. Etiquetar la imagen para el registro de Azure:

```bash
docker tag barberbrothers:latest [your-registry].azurecr.io/barberbrothers:latest
```

3. Enviar la imagen al registro:

```bash
docker push [your-registry].azurecr.io/barberbrothers:latest
```

4. Desplegar utilizando Azure CLI o desde el portal de Azure.

## Resolución de Problemas

Si encuentras problemas al iniciar los contenedores:

1. Verificar los logs:

```bash
docker-compose logs
```

2. Acceder a un contenedor en ejecución:

```bash
docker-compose exec web bash
```
