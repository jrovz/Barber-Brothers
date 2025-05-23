# Guía para la Migración a PostgreSQL en GCP

Esta guía describe los pasos necesarios para migrar la aplicación Barber Brothers de MySQL a PostgreSQL en Google Cloud Platform.

## Pasos Completados

1. ✅ Actualizado `requirements.txt` para usar las dependencias de PostgreSQL
2. ✅ Creado el módulo `cloud_connection_pg.py` para conexión a PostgreSQL en GCP
3. ✅ Actualizada la configuración en `app/config/__init__.py` para usar PostgreSQL
4. ✅ Modificado `cloudbuild.yaml` para incluir variables de entorno de PostgreSQL
5. ✅ Creado script `migrate_to_postgres.py` para la migración de datos

## Pasos Pendientes

### 1. Crear una instancia de PostgreSQL en Cloud SQL

```bash
# Ejecutar en Google Cloud Shell o con gcloud CLI instalado
gcloud sql instances create barberia-db-pg \
    --database-version=POSTGRES_14 \
    --cpu=1 \
    --memory=3840MB \
    --region=us-central1 \
    --storage-type=SSD \
    --storage-size=10GB \
    --availability-type=zonal \
    --root-password="[CONTRASEÑA-SEGURA]"
```

### 2. Crear base de datos y usuario

```bash
# Conectar a la instancia PostgreSQL
gcloud sql connect barberia-db-pg --user=postgres

# En la consola de PostgreSQL, crear base de datos y usuario
CREATE DATABASE barberia_db;
CREATE USER barberia_user WITH PASSWORD '[CONTRASEÑA-SEGURA]';
GRANT ALL PRIVILEGES ON DATABASE barberia_db TO barberia_user;
\q
```

### 3. Almacenar credenciales en Secret Manager

```bash
# Crear secretos para PostgreSQL
echo -n "[USUARIO]" | gcloud secrets create db_user --data-file=-
echo -n "[CONTRASEÑA]" | gcloud secrets create db_pass --data-file=-
```

### 4. Actualizar configuración para Cloud Run

```bash
# Modificar la configuración de Cloud Run para usar la nueva instancia PostgreSQL
gcloud run services update barberia-app \
    --add-cloudsql-instances=PROJECT_ID:us-central1:barberia-db-pg \
    --set-env-vars="INSTANCE_CONNECTION_NAME=PROJECT_ID:us-central1:barberia-db-pg,DB_ENGINE=postgresql"
```

### 5. Migrar los datos

Para migrar los datos desde MySQL a PostgreSQL, se debe ejecutar el script de migración con las variables de entorno adecuadas:

```bash
# Exportar variables de entorno
export MYSQL_DATABASE_URL="mysql+pymysql://[USUARIO_MYSQL]:[CONTRASEÑA_MYSQL]@/[DB_MYSQL]?unix_socket=/cloudsql/[INSTANCIA_MYSQL]"
export DATABASE_URL="postgresql+psycopg2://[USUARIO_PG]:[CONTRASEÑA_PG]@/[DB_PG]?host=/cloudsql/[INSTANCIA_PG]"

# Ejecutar script de migración
python migrate_to_postgres.py
```

### 6. Pruebas y verificación

1. Verificar la conectividad a la base de datos PostgreSQL:
   ```bash
   # Conectar a la instancia PostgreSQL para verificar los datos
   gcloud sql connect barberia-db-pg --user=barberia_user
   # Consultar tablas para verificar datos migrados
   \dt
   SELECT COUNT(*) FROM clientes;
   ```

2. Probar la aplicación en entorno de desarrollo:
   ```bash
   # Configurar la conexión local para desarrollo
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/barberia_db"
   export FLASK_APP=wsgi.py
   export FLASK_ENV=development
   flask run
   ```

## Solución de problemas

### Errores de conexión a la base de datos

Si aparecen errores de conexión a la base de datos PostgreSQL:

1. Verificar que el usuario tenga los permisos adecuados:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE barberia_db TO barberia_user;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO barberia_user;
   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO barberia_user;
   ```

2. Verificar la configuración del Cloud SQL Auth Proxy:
   ```bash
   # Para probar localmente con el proxy
   ./cloud_sql_proxy -instances=PROJECT_ID:us-central1:barberia-db-pg=tcp:5432
   ```

3. Verificar los logs de la aplicación:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=barberia-app"
   ```

## Rollback (En caso de problemas)

Si es necesario revertir a MySQL:

1. Restaurar el archivo de configuración original:
   ```bash
   cp app/config/__init__.py.bak app/config/__init__.py
   ```

2. Actualizar Cloud Run para usar la instancia MySQL:
   ```bash
   gcloud run services update barberia-app \
       --add-cloudsql-instances=PROJECT_ID:us-central1:barberia-db \
       --set-env-vars="INSTANCE_CONNECTION_NAME=PROJECT_ID:us-central1:barberia-db,DB_ENGINE=mysql"
   ```

## Referencias

- [Cloud SQL para PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Migrar de MySQL a PostgreSQL](https://cloud.google.com/solutions/migrating-mysql-to-postgresql)
- [Conectar Cloud Run a Cloud SQL](https://cloud.google.com/run/docs/configuring/connect-cloudsql)
