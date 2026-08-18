# 💈 Barber Brothers – Sistema de Gestión para Barbería

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/) [![Flask](https://img.shields.io/badge/Flask-3.1.3-green.svg)](https://flask.palletsprojects.com/) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/) [![Tests](https://img.shields.io/badge/tests-13%20passing-brightgreen.svg)](tests/)

> Repositorio privado del sistema de gestión de Barber Brothers. No es un proyecto open source: el código pertenece al negocio, no hay licencia pública asociada.

### 📝 Descripción
Barber Brothers es una aplicación web para gestionar una barbería moderna: reservas online, catálogo de servicios y productos, panel administrativo y panel de barberos. Construida con Flask y PostgreSQL, con un frontend ligero en HTML/CSS/JS.

### 🖼️ Vista previa
- `website.png` – Página pública
- `admin.png` – Panel administrativo

### ⚙️ Stack
- Frontend: HTML5, CSS3, JavaScript (vanilla)
- Backend: Python 3.11+, Flask 3.1.3, Werkzeug 3.1.8, SQLAlchemy 2.0
- Base de datos: PostgreSQL 13+ (SQLite en memoria para tests)
- Email: Flask-Mail (confirmaciones con token)
- Servidor de producción: Gunicorn 26 detrás de Nginx (VPS), ver `deployment/`

### ✨ Funcionalidades clave
- Clientes: reservas con disponibilidad en tiempo real, confirmación por email, catálogo de servicios y productos
- Administración: dashboard, gestión de barberos, disponibilidad, servicios, productos y citas; CRM básico
- Citas: workflow `pendiente_confirmacion` → `confirmada` → `completada`, prevención de solapamientos

> Los detalles de arquitectura, blueprints, flujos y diagrama están en `ARCHITECTURE.md`.

---

## 🛠️ Instalación y configuración (desarrollo local)

### Requisitos
- Python 3.11+
- PostgreSQL 13+ (o usa el fallback a SQLite local si no configuras `DATABASE_URL`)
- Git, pip y virtualenv

### Pasos rápidos
1) Clonar e instalar dependencias
```bash
git clone <url-del-repositorio>
cd Barber-Brothers
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
```

2) Variables de entorno (`.env` en la raíz, nunca lo subas al repo)
```bash
DATABASE_URL=postgresql://usuario:password@localhost/barberia_db
SECRET_KEY=tu-clave-secreta-aqui
# Opcional correo (confirmación de citas)
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-password-de-aplicacion
```

3) Base de datos y migraciones
```bash
createdb barberia_db
flask db upgrade
```

4) Ejecutar en desarrollo

`wsgi.py` fuerza `create_app('production')` sin importar lo que digas en `.flaskenv`, así que `flask run` normal arranca con `ProductionConfig` — incluida la cookie de sesión `Secure`, que no se envía por HTTP plano y rompe el login en `http://localhost`. Para desarrollar de verdad con `DevelopmentConfig` (debug, auto-reload, cookies sin `Secure`):
```bash
python -c "from app import create_app; create_app('development').run(debug=True, port=5000)"
# http://localhost:5000
```

---

## 🚀 Despliegue a producción

El despliegue real es sobre un VPS (Gunicorn + Nginx + PostgreSQL), no Docker. Las guías y scripts están en `deployment/`:
- `deployment/OVH_DEPLOYMENT_GUIDE.md` — guía paso a paso del setup actual.
- `deployment/DATABASE_SETUP_GUIDE.md`, `setup_postgres.sh`, `verify_database.sh` — base de datos.
- `deployment/run_migrations.sh` — migraciones en el servidor.
- `deployment/setup_https*.sh`, `setup_ssl*.sh` — certificados TLS.

El servicio corre como `barber-brothers.service` (systemd) con `gunicorn` escuchando en `127.0.0.1:5000`, detrás de Nginx como proxy inverso.

---

## 🔌 Endpoints y módulos
- Público (`/`): home, reservas, productos, contacto — Blueprint `public`
- Reservas (definidas en `app/public/routes.py`, no en el Blueprint `api` pese al prefijo de URL):
  - GET `/api/disponibilidad/<barbero_id>/<fecha>?servicio_id=...`
  - POST `/api/agendar-cita`
  - GET `/confirmar-cita/<token>`
- Admin (`/admin`, Blueprint `admin`): dashboard, barberos, categorías, servicios, productos, citas, clientes, sliders — vistas organizadas por dominio en `app/admin/routes/` (`productos.py`, `citas.py`, `barberos.py`, etc.)
- Barbero (`/barbero`): panel propio de cada barbero (horarios, sus citas)

> Estructura de carpetas y flujos detallados: ver `ARCHITECTURE.md`.

---

## 🔒 Seguridad
- CSRF global (Flask-WTF), ORM contra SQLi, tokens firmados con caducidad para confirmar citas.
- Todas las rutas de administración pasan por `@login_required` + `@admin_required` (`app/utils/decorators.py`) — un único punto de verificación de rol, no chequeos repetidos por vista.
- Cabeceras de seguridad HTTP (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, HSTS) y cookie de sesión `Secure`/`HttpOnly`/`SameSite` en producción.
- `SECRET_KEY` y `DATABASE_URL` son obligatorias en `ProductionConfig`: la app no arranca en producción si faltan.
- Dependencias auditadas contra la base de datos de vulnerabilidades OSV; se actualizan cuando aparece un CVE relevante.

---

## 🧪 Testing
```bash
pytest tests/ -v
```
Cubre login de administrador, autorización (escanea automáticamente todas las rutas de `/admin/*` y exige 403 sin rol admin) y el flujo de agendamiento de citas (creación, conflicto de horario, confirmación por token). Corre automáticamente en cada push/PR vía `.github/workflows/tests.yml`.

Cobertura pendiente: vistas de barbero, checkout/pedidos, subida de imágenes.

---

## 📈 Monitoreo y observabilidad (sugerencias, no implementado)
- Uptime externo (UptimeRobot/Better Stack/Pingdom)
- Errores y trazas (Sentry backend + frontend)
- Logs centralizados (Grafana Loki/ELK o servicio gestionado)
- Métricas/APM (OpenTelemetry + Prometheus/Grafana o Datadog/New Relic)
- Email deliverability (Mailgun/SendGrid/Postmark) para tasas de entrega/clicks

---

## 👨‍💻 Mantenimiento
Proyecto desarrollado y mantenido para Barber Brothers.
