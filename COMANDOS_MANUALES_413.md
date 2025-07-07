# Comandos Manuales para Solucionar Error 413

## 🚨 Error 413: Request Entity Too Large

### Ejecutar estos comandos uno por uno:

## 1. Verificar estado actual
```bash
# Ver configuración actual de nginx
sudo grep -n "client_max_body_size" /etc/nginx/sites-available/barber-brothers

# Ver configuración actual de Flask
sudo grep -n "MAX_CONTENT_LENGTH" /opt/barber-brothers/app/config/__init__.py

# Ver estado de servicios
sudo systemctl status barber-brothers --no-pager -l
```

## 2. Crear backup de configuración
```bash
# Backup de nginx
sudo cp /etc/nginx/sites-available/barber-brothers /etc/nginx/sites-available/barber-brothers.backup

# Backup de Flask config
sudo cp /opt/barber-brothers/app/config/__init__.py /opt/barber-brothers/app/config/__init__.py.backup
```

## 3. Aumentar límites en nginx
```bash
# Aumentar a 50MB
sudo sed -i 's/client_max_body_size 16M;/client_max_body_size 50M;/' /etc/nginx/sites-available/barber-brothers

# Verificar cambio
sudo grep -n "client_max_body_size" /etc/nginx/sites-available/barber-brothers
```

## 4. Aumentar límites en Flask
```bash
# Aumentar a 50MB
sudo sed -i 's/MAX_CONTENT_LENGTH = 16 \* 1024 \* 1024/MAX_CONTENT_LENGTH = 50 * 1024 * 1024/' /opt/barber-brothers/app/config/__init__.py

# Verificar cambio
sudo grep -n "MAX_CONTENT_LENGTH" /opt/barber-brothers/app/config/__init__.py
```

## 5. Crear configuración de gunicorn
```bash
# Crear archivo de configuración
sudo tee /opt/barber-brothers/gunicorn.conf.py > /dev/null << 'EOF'
# Gunicorn configuration for Barber Brothers
bind = "127.0.0.1:5000"
workers = 3
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
worker_class = "sync"
worker_connections = 1000

# Configuración de tamaño máximo para uploads
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Configuración de memoria y buffers
worker_tmp_dir = "/dev/shm"

# Logs
accesslog = "/var/log/barber-brothers/gunicorn_access.log"
errorlog = "/var/log/barber-brothers/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Configuración de seguridad
forwarded_allow_ips = "127.0.0.1"
proxy_allow_ips = "127.0.0.1"
EOF

# Cambiar permisos
sudo chown ubuntu:ubuntu /opt/barber-brothers/gunicorn.conf.py
```

## 6. Verificar configuración de nginx
```bash
# Verificar sintaxis
sudo nginx -t
```

## 7. Reiniciar servicios
```bash
# Recargar nginx
sudo systemctl reload nginx

# Reiniciar aplicación
sudo systemctl restart barber-brothers
```

## 8. Verificar estado
```bash
# Verificar que los servicios estén corriendo
sudo systemctl is-active nginx
sudo systemctl is-active barber-brothers

# Ver estado detallado
sudo systemctl status barber-brothers --no-pager -l
```

## 9. Verificar logs si hay problemas
```bash
# Logs de nginx
sudo tail -20 /var/log/nginx/barber-brothers_error.log

# Logs de la aplicación
sudo journalctl -u barber-brothers --no-pager -l --since '5 minutes ago'

# Logs en tiempo real
sudo journalctl -u barber-brothers -f
```

## 10. Probar subida de archivos
1. Ve a tu panel de admin
2. Intenta subir una imagen a los sliders
3. Si aún tienes problemas, verifica que:
   - El archivo no sea mayor a 50MB
   - Los servicios estén corriendo
   - Los logs no muestren errores

## 🔧 Si necesitas aumentar más el límite:

### Para 100MB:
```bash
# Nginx
sudo sed -i 's/client_max_body_size 50M;/client_max_body_size 100M;/' /etc/nginx/sites-available/barber-brothers

# Flask
sudo sed -i 's/MAX_CONTENT_LENGTH = 50 \* 1024 \* 1024/MAX_CONTENT_LENGTH = 100 * 1024 * 1024/' /opt/barber-brothers/app/config/__init__.py

# Reiniciar servicios
sudo systemctl reload nginx
sudo systemctl restart barber-brothers
```

## 📋 Troubleshooting adicional:

### Si el error persiste:
```bash
# Verificar espacio en disco
df -h

# Verificar permisos de uploads
ls -la /opt/barber-brothers/app/static/uploads/sliders/

# Verificar proceso de gunicorn
ps aux | grep gunicorn

# Verificar puertos
sudo netstat -tulpn | grep :5000
```

### Restaurar configuración original:
```bash
# Si algo sale mal, restaurar backups
sudo cp /etc/nginx/sites-available/barber-brothers.backup /etc/nginx/sites-available/barber-brothers
sudo cp /opt/barber-brothers/app/config/__init__.py.backup /opt/barber-brothers/app/config/__init__.py
sudo systemctl reload nginx
sudo systemctl restart barber-brothers
``` 