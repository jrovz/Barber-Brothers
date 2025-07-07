# SOLUCIÓN MANUAL PARA ERROR 413 - LÍMITE 30MB

## 🚨 PROBLEMA
El admin no puede subir imágenes porque aparece error 413 "Request Entity Too Large"

## ✅ SOLUCIÓN APLICADA
Hemos aumentado los límites de 16MB a **30MB** tanto en Flask como en Nginx.

---

## 📋 PASOS PARA APLICAR EN EL SERVIDOR

### 1. Actualizar Flask (YA HECHO)
```python
# app/config/__init__.py - Línea 12
MAX_CONTENT_LENGTH = 30 * 1024 * 1024  # 30 MB límite de tamaño
```

### 2. Actualizar Nginx (EJECUTAR EN SERVIDOR)

#### Opción A: Script Automático
```bash
chmod +x fix_413_30MB.sh
./fix_413_30MB.sh
```

#### Opción B: Comandos Manuales

**1. Hacer backup:**
```bash
sudo cp /etc/nginx/sites-available/barber-brothers /etc/nginx/sites-available/barber-brothers.backup.$(date +%Y%m%d_%H%M%S)
```

**2. Editar configuración:**
```bash
sudo nano /etc/nginx/sites-available/barber-brothers
```

**3. Buscar y cambiar esta línea:**
```nginx
# Cambiar de:
client_max_body_size 16M;

# A:
client_max_body_size 30M;
```

**4. Si no existe la línea, agregarla dentro del bloque server:**
```nginx
server {
    client_max_body_size 30M;
    # ... resto de configuración
}
```

**5. Verificar configuración:**
```bash
sudo nginx -t
```

**6. Reiniciar nginx:**
```bash
sudo systemctl reload nginx
```

**7. Reiniciar aplicación:**
```bash
sudo systemctl restart barber-brothers
# O si usa gunicorn:
sudo systemctl restart gunicorn
```

---

## 🔍 VERIFICAR QUE FUNCIONE

### Comprobar configuraciones:
```bash
# Ver configuración Flask (en el código)
grep -n "MAX_CONTENT_LENGTH" app/config/__init__.py

# Ver configuración Nginx
grep -n "client_max_body_size" /etc/nginx/sites-available/barber-brothers

# Ver estado de servicios
sudo systemctl status nginx
sudo systemctl status barber-brothers
```

### Probar subida:
1. Ir a `/admin/sliders`
2. Intentar subir una imagen de 20-25 MB
3. Debería funcionar sin error 413

---

## 📝 LOGS PARA DIAGNOSTICAR PROBLEMAS

```bash
# Logs de Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Logs de la aplicación
sudo journalctl -u barber-brothers -f
sudo journalctl -u gunicorn -f

# Logs del sistema
dmesg | tail
```

---

## ⚙️ CONFIGURACIÓN FINAL

- **Flask:** 30 MB ✅
- **Nginx:** 30 MB ✅
- **Recomendación de imagen:** 1920x740px
- **Tamaño máximo práctico:** 2-5 MB (para velocidad web)

---

## 🎯 RECOMENDACIONES ADICIONALES

### Para el Admin:
- **Optimizar imágenes** antes de subir usando herramientas como:
  - TinyPNG.com
  - ImageOptim
  - Photoshop "Save for Web"
- **Formato recomendado:** JPG con 80-90% calidad
- **Dimensiones ideales:** 1920x740px exacto

### Para futuras mejoras:
- Implementar redimensionamiento automático con PIL/Pillow
- Compresión automática en el servidor
- Validación de dimensiones mínimas/máximas
```

</rewritten_file>