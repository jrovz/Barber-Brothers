# Guía para Configurar la Base de Datos PostgreSQL

## 📋 Resumen
Esta guía te ayudará a configurar completamente la base de datos PostgreSQL para tu aplicación Barber Brothers en el servidor VPS.

## 🚀 Scripts Disponibles

### 1. `verify_database.sh` - Verificación Completa
**Propósito:** Verificar el estado actual de PostgreSQL y la base de datos
**Cuándo usar:** Antes de hacer cualquier cambio

```bash
cd /opt/barber-brothers
chmod +x deployment/verify_database.sh
bash deployment/verify_database.sh
```

### 2. `run_migrations.sh` - Ejecutar Migraciones
**Propósito:** Crear/actualizar todas las tablas de la base de datos
**Cuándo usar:** Después de verificar que PostgreSQL funciona

```bash
cd /opt/barber-brothers
chmod +x deployment/run_migrations.sh
bash deployment/run_migrations.sh
```

### 3. `create_admin.py` - Crear Usuario Administrador
**Propósito:** Crear el primer usuario administrador para acceder al sistema
**Cuándo usar:** Después de ejecutar las migraciones exitosamente

```bash
cd /opt/barber-brothers
python3 deployment/create_admin.py
```

### 4. `setup_database.py` - Configuración Completa Automática
**Propósito:** Hacer todo el proceso automáticamente (recomendado para primera vez)
**Cuándo usar:** Si quieres automatizar todo el proceso

```bash
cd /opt/barber-brothers
python3 deployment/setup_database.py
```

## 📝 Pasos Recomendados

### Paso 1: Conectar al Servidor
```bash
ssh ubuntu@144.217.86.8
# Usar password: 8BWryhjkm5aw
```

### Paso 2: Ir al Directorio del Proyecto
```bash
cd /opt/barber-brothers
```

### Paso 3: Verificar Estado Actual
```bash
# Dar permisos de ejecución
chmod +x deployment/*.sh

# Verificar estado actual
bash deployment/verify_database.sh
```

### Paso 4: Configurar PostgreSQL (si es necesario)
Si PostgreSQL no está configurado:

```bash
# Instalar PostgreSQL (si no está instalado)
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# Iniciar servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Crear base de datos y usuario
sudo -u postgres psql -c "CREATE DATABASE barber_brothers_db;"
sudo -u postgres psql -c "CREATE USER barber_user WITH PASSWORD 'barber_password_2024';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE barber_brothers_db TO barber_user;"
```

### Paso 5: Ejecutar Migraciones
```bash
# Asegurar que el entorno virtual esté activado
source venv/bin/activate

# Ejecutar migraciones
bash deployment/run_migrations.sh
```

### Paso 6: Crear Usuario Administrador
```bash
# Crear usuario admin
python3 deployment/create_admin.py
```

### Paso 7: Verificar Todo
```bash
# Verificación final
bash deployment/verify_database.sh
```

## 🔧 Solución de Problemas Comunes

### Error: "PostgreSQL no está ejecutándose"
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Error: "Base de datos no existe"
```bash
sudo -u postgres createdb barber_brothers_db
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE barber_brothers_db TO barber_user;"
```

### Error: "Usuario no existe"
```bash
sudo -u postgres psql -c "CREATE USER barber_user WITH PASSWORD 'barber_password_2024';"
```

### Error: "No se puede conectar"
Verifica la configuración en `/etc/postgresql/*/main/pg_hba.conf`:
```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

Asegúrate de tener esta línea:
```
local   all             barber_user                             md5
```

Luego reinicia PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Error: "Flask-Migrate no encontrado"
```bash
source venv/bin/activate
pip install Flask-Migrate
```

### Error: "Módulos no encontrados"
```bash
# Asegurar que estás en el directorio correcto
cd /opt/barber-brothers

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements-ubuntu.txt
```

## 📊 Verificación de Resultados

### Después de ejecutar los scripts, deberías ver:

1. **PostgreSQL activo:**
   ```
   ✅ PostgreSQL está ejecutándose
   ```

2. **Base de datos conectada:**
   ```
   ✅ Base de datos accesible
   ```

3. **Tablas creadas:**
   ```
   ✅ Tablas encontradas:
     - usuario
     - barbero
     - cliente
     - servicio
     - producto
     - categoria
     - cita
   ```

4. **Usuario admin creado:**
   ```
   ✅ Usuario administrador creado exitosamente
   📧 Email: admin@barberbros.com
   🔐 Password: admin123
   ```

## 🌐 Probar la Aplicación

Una vez configurada la base de datos:

1. **Acceder a la aplicación:**
   ```
   http://144.217.86.8
   ```

2. **Acceder al admin:**
   ```
   http://144.217.86.8/admin/login
   Email: admin@barberbros.com
   Password: admin123
   ```

3. **Verificar salud de la aplicación:**
   ```
   http://144.217.86.8/health
   ```

## 🔒 Seguridad

**⚠️ IMPORTANTE:** Después de la primera configuración:

1. Cambia la contraseña del usuario administrador
2. Considera cambiar las credenciales de la base de datos
3. Configura backups automáticos
4. Revisa los logs regularmente

## 📞 Contacto y Soporte

Si encuentras problemas:
1. Revisa los logs: `/var/log/postgresql/` y `/opt/barber-brothers/logs/`
2. Ejecuta `bash deployment/verify_database.sh` para diagnóstico
3. Verifica que todos los servicios estén activos:
   ```bash
   sudo systemctl status postgresql
   sudo systemctl status barber-brothers
   sudo systemctl status nginx
   ```
