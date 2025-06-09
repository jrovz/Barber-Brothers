# 🔒 Guía Manual: Configurar SSL con Dominio Propio

## 📋 Pre-requisitos

✅ **ANTES DE EMPEZAR:**
1. Tu aplicación debe estar funcionando en `http://144.217.86.8`
2. Debes tener acceso SSH al servidor VPS
3. Necesitas un dominio propio (comprado en GoDaddy, Namecheap, etc.)

---

## 🌐 Paso 1: Configurar DNS de tu Dominio

### Opción A: Proveedor de Dominio (GoDaddy, Namecheap, etc.)

1. **Accede al panel de control de tu dominio**
2. **Busca "DNS Management" o "DNS Settings"**
3. **Configura estos registros:**

```
Tipo: A
Nombre: @
Valor: 144.217.86.8
TTL: 300 (5 minutos)

Tipo: A
Nombre: www
Valor: 144.217.86.8
TTL: 300 (5 minutos)
```

### Opción B: Cloudflare (si usas Cloudflare)

1. **En Cloudflare Dashboard:**
   - Tipo: `A`
   - Nombre: `@`
   - IPv4: `144.217.86.8`
   - **IMPORTANTE:** Desactiva el proxy (nube debe estar gris, no naranja)

2. **Para www:**
   - Tipo: `A`
   - Nombre: `www`
   - IPv4: `144.217.86.8`
   - **IMPORTANTE:** Desactiva el proxy (nube debe estar gris, no naranja)

---

## ⏱️ Paso 2: Esperar Propagación DNS

**El DNS puede tardar de 5 minutos a 24 horas en propagarse.**

### Verificar DNS:
```bash
# Desde tu computadora local
nslookup tudominio.com
dig tudominio.com

# Debe mostrar: 144.217.86.8
```

### Herramientas online:
- https://dnschecker.org/
- https://www.whatsmydns.net/

---

## 🔧 Paso 3: Configurar SSL en el Servidor

### 3.1 Conectarse al Servidor
```bash
ssh root@144.217.86.8
```

### 3.2 Ir al directorio de despliegue
```bash
cd /var/www/barber-brothers/deployment
```

### 3.3 Editar el script de SSL
```bash
nano setup_ssl_domain.sh
```

**Cambiar la línea:**
```bash
DOMAIN="tudominio.com"  # <- Pon tu dominio aquí
```

**Por ejemplo:**
```bash
DOMAIN="barberbrothers.com"
```

### 3.4 Hacer el script ejecutable
```bash
chmod +x setup_ssl_domain.sh
```

### 3.5 Ejecutar el script
```bash
sudo ./setup_ssl_domain.sh
```

---

## 🔍 Paso 4: Verificaciones

### 4.1 Verificar que el dominio funciona
```bash
curl -I http://tudominio.com
# Debe devolver código 200, 301 o 302
```

### 4.2 Verificar certificado SSL
```bash
curl -I https://tudominio.com
# Debe funcionar sin errores
```

### 4.3 Probar en el navegador
- `https://tudominio.com` ✅
- `https://www.tudominio.com` ✅
- `https://tudominio.com/admin/login` ✅

---

## 🚨 Problemas Comunes y Soluciones

### Error: "DNS no apunta al servidor"
**Solución:**
```bash
# Verificar DNS actual
dig tudominio.com

# Si no muestra 144.217.86.8:
# 1. Revisa configuración DNS
# 2. Espera más tiempo (hasta 24h)
# 3. Si usas Cloudflare, desactiva el proxy
```

### Error: "Certificado SSL falla"
**Solución:**
```bash
# Verificar que Nginx funciona
sudo nginx -t
sudo systemctl status nginx

# Verificar que el dominio es accesible por HTTP
curl http://tudominio.com

# Reinstalar certificado manualmente
sudo certbot --nginx -d tudominio.com -d www.tudominio.com
```

### Error: "Aplicación no funciona con HTTPS"
**Solución:**
```bash
# Verificar que Flask está ejecutándose
sudo systemctl status barber-brothers

# Reiniciar servicios
sudo systemctl restart barber-brothers
sudo systemctl restart nginx
```

---

## 📝 Comandos Útiles Post-SSL

### Ver certificados instalados
```bash
sudo certbot certificates
```

### Renovar certificados manualmente
```bash
sudo certbot renew
```

### Ver logs de Nginx
```bash
sudo tail -f /var/log/nginx/tudominio.com_ssl_access.log
sudo tail -f /var/log/nginx/tudominio.com_ssl_error.log
```

### Verificar configuración SSL
```bash
# Test SSL online
https://www.ssllabs.com/ssltest/

# O desde terminal
openssl s_client -connect tudominio.com:443 -servername tudominio.com
```

---

## 🎯 Resultado Final

Después de completar estos pasos, tendrás:

- ✅ **Dominio propio funcionando**
- ✅ **Certificado SSL válido (Let's Encrypt)**
- ✅ **HTTPS automático**
- ✅ **Redirección HTTP → HTTPS**
- ✅ **Renovación automática del certificado**
- ✅ **Headers de seguridad configurados**

### URLs que funcionarán:
- `https://tudominio.com` ← Principal
- `https://www.tudominio.com` ← Con www
- `https://tudominio.com/admin/login` ← Panel admin
- `http://tudominio.com` ← Redirige a HTTPS

---

## 📞 ¿Necesitas Ayuda?

Si tienes problemas:

1. **Revisa que el DNS apunte a 144.217.86.8**
2. **Verifica que la aplicación funciona en HTTP primero**
3. **Espera a que el DNS se propague completamente**
4. **Ejecuta el script paso a paso**

¡Tu aplicación Barber Brothers estará disponible con SSL en tu dominio propio! 🎉
