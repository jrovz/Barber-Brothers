# 🚀 Manual de Despliegue - Barber Brothers Flask App

## 📋 Requisitos Previos

### Servidor VPS Ubuntu 22.04
- **Mínimo**: 2GB RAM, 2 CPU cores, 20GB almacenamiento
- **Recomendado**: 4GB RAM, 2 CPU cores, 40GB almacenamiento
- Acceso root via SSH
- Dominio configurado (opcional para SSL)

## 🔧 Paso 1: Preparación del Servidor

### 1.1 Conectarse al VPS
```bash
ssh root@tu-servidor-ip
```

### 1.2 Actualizar el sistema
```bash
apt update && apt upgrade -y
```

### 1.3 Crear usuario para la aplicación (opcional, se hace automático en deploy.sh)
```bash
# Esto se hace automáticamente en el script de despliegue
# Solo si quieres hacerlo manualmente antes
useradd -r -s /bin/false -d /var/www/barber-brothers -c "Usuario para Barber Brothers" barber-user
```

## 📥 Paso 2: Descargar el Proyecto

### 2.1 Clonar desde GitHub
```bash
cd /var/www
git clone https://github.com/tu-usuario/barber-brothers.git
cd barber-brothers
```

### 2.2 O subir archivos via SCP (desde tu máquina local)
```bash
# Desde tu máquina Windows (PowerShell)
scp -r "C:\Users\jrove\OneDrive\Documentos\PROYECTOS WEB\Barber-Brothers" root@tu-servidor-ip:/var/www/barber-brothers
```

## 🚀 Paso 3: Ejecutar Despliegue Automático

### 3.1 Hacer ejecutables los scripts
```bash
cd /var/www/barber-brothers/deployment
chmod +x *.sh
```

### 3.2 Ejecutar script principal de despliegue
```bash
sudo bash deploy.sh
```

Este script instala y configura automáticamente:
- ✅ PostgreSQL
- ✅ Nginx
- ✅ Python y dependencias
- ✅ Entorno virtual
- ✅ Gunicorn
- ✅ Servicio systemd
- ✅ Firewall básico
- ✅ Estructura de directorios

## ⚙️ Paso 4: Configuración Post-Despliegue

### 4.1 Editar variables de entorno
```bash
nano /var/www/barber-brothers/.env
```

**Cambiar obligatoriamente:**
```env
SECRET_KEY=tu-clave-secreta-super-segura-nueva
DATABASE_URL=postgresql://barberia_user:tu_password_nuevo@localhost/barberia_db
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu_app_password_gmail
```

### 4.2 Configurar dominio en Nginx
```bash
nano /etc/nginx/sites-available/barber-brothers
```

Cambiar:
```nginx
server_name tu-dominio.com www.tu-dominio.com;
```

### 4.3 Recargar configuraciones
```bash
systemctl restart barber-brothers
systemctl reload nginx
```

## 🔒 Paso 5: Configurar SSL (Opcional pero Recomendado)

### 5.1 Ejecutar script de SSL
```bash
cd /var/www/barber-brothers/deployment
sudo bash setup-ssl.sh tu-dominio.com
```

Este script:
- ✅ Obtiene certificado de Let's Encrypt
- ✅ Configura HTTPS automático
- ✅ Configura renovación automática

## 🗄️ Paso 6: Configurar Base de Datos Inicial

### 6.1 Crear usuario administrador
```bash
cd /var/www/barber-brothers
source venv/bin/activate
python3 -c "
from app import create_app, db
from app.models.admin import User

app = create_app('production')
with app.app_context():
    # Crear usuario admin
    admin = User(username='admin', email='admin@tu-dominio.com', role='admin')
    admin.set_password('tu_password_admin_seguro')
    db.session.add(admin)
    db.session.commit()
    print('Usuario admin creado exitosamente')
"
```

### 6.2 Poblar datos iniciales (opcional)
```bash
# Si tienes datos de categorías u otros datos iniciales
python3 add_categories.py
```

## 📊 Paso 7: Configurar Monitoreo y Backups

### 7.1 Configurar backups automáticos
```bash
sudo crontab -e
```

Agregar líneas del archivo `deployment/crontab-config`:
```cron
# Backup diario a las 2:00 AM
0 2 * * * /var/www/barber-brothers/deployment/backup.sh >> /var/log/barber-brothers/backup.log 2>&1

# Monitoreo cada 15 minutos
*/15 * * * * /var/www/barber-brothers/deployment/monitor.sh status | grep -E "(❌|No funciona)" && /var/www/barber-brothers/deployment/monitor.sh > /var/log/barber-brothers/monitor.log
```

### 7.2 Probar monitoreo
```bash
cd /var/www/barber-brothers/deployment
./monitor.sh
```

## ✅ Paso 8: Verificación Final

### 8.1 Verificar servicios
```bash
systemctl status postgresql
systemctl status nginx
systemctl status barber-brothers
```

### 8.2 Probar la aplicación
```bash
# Probar conectividad
curl -I http://tu-servidor-ip
curl -I http://tu-dominio.com  # Si configuraste dominio

# Probar páginas específicas
curl http://tu-servidor-ip/admin/login
curl http://tu-servidor-ip/api/info
```

### 8.3 Verificar logs
```bash
# Logs de la aplicación
journalctl -u barber-brothers -f

# Logs de Nginx
tail -f /var/log/nginx/barber-brothers_access.log
tail -f /var/log/nginx/barber-brothers_error.log
```

## 🔧 Comandos Útiles para Mantenimiento

### Gestión de la aplicación
```bash
# Reiniciar aplicación
sudo systemctl restart barber-brothers

# Ver estado
sudo systemctl status barber-brothers

# Ver logs en tiempo real
sudo journalctl -u barber-brothers -f

# Reiniciar Nginx
sudo systemctl restart nginx
```

### Gestión de base de datos
```bash
# Conectar a PostgreSQL
sudo -u postgres psql barberia_db

# Hacer backup manual
sudo -u postgres pg_dump barberia_db > backup_manual.sql

# Ver procesos de PostgreSQL
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

### Actualización de la aplicación
```bash
cd /var/www/barber-brothers
git pull origin main
source venv/bin/activate
pip install -r requirements-production.txt
flask db upgrade
sudo systemctl restart barber-brothers
```

## 🚨 Solución de Problemas Comunes

### Error de conexión a base de datos
```bash
# Verificar que PostgreSQL esté ejecutándose
sudo systemctl status postgresql

# Verificar configuración de BD
sudo -u postgres psql -l

# Verificar variables de entorno
cat /var/www/barber-brothers/.env | grep DATABASE
```

### Error 502 Bad Gateway
```bash
# Verificar que Gunicorn esté ejecutándose
sudo systemctl status barber-brothers

# Verificar logs de Gunicorn
journalctl -u barber-brothers -f

# Verificar configuración de Nginx
sudo nginx -t
```

### Permisos de archivos
```bash
# Reconfigurar permisos
cd /var/www/barber-brothers/deployment
sudo bash setup-user.sh
```

### Error de certificado SSL
```bash
# Renovar certificado manualmente
sudo certbot renew

# Verificar configuración SSL
sudo certbot certificates
```

## 📈 Optimizaciones Adicionales

### Para mayor tráfico
1. Configurar múltiples workers de Gunicorn
2. Usar configuración avanzada de Nginx
3. Configurar Redis para caching
4. Configurar CDN para archivos estáticos

### Para mayor seguridad
1. Configurar fail2ban
2. Configurar monitoreo de logs
3. Actualizar regularmente el sistema
4. Configurar backups en ubicación externa

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs primero
2. Ejecuta el script de monitoreo: `./deployment/monitor.sh`
3. Verifica la configuración de red y DNS
4. Consulta la documentación oficial de Flask, Nginx y PostgreSQL
