# 💈 Barber Brothers – Sistema de Gestión para Barbería

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/) [![Flask](https://img.shields.io/badge/Flask-2.2.3-green.svg)](https://flask.palletsprojects.com/) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/) [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

### 📝 Descripción
Barber Brothers es una aplicación web para gestionar una barbería moderna: reservas online, catálogo de servicios y productos, panel administrativo y panel de barberos. Construida con Flask y PostgreSQL, con un frontend ligero en HTML/CSS/JS.

### 🖼️ Vista previa
- `website.png` – Página pública
- `admin.png` – Panel administrativo

### ⚙️ Stack
- Frontend: HTML5, CSS3, JavaScript (vanilla)
- Backend: Python 3.11+, Flask 2.2.3, SQLAlchemy
- Base de datos: PostgreSQL 15+
- Email: Flask-Mail (confirmaciones con token)
- Deployment: Docker + Docker Compose (o VPS con Nginx + Gunicorn)

### ✨ Funcionalidades clave
- Clientes: reservas con disponibilidad en tiempo real, confirmación por email, catálogo de servicios y productos
- Administración: dashboard, gestión de barberos, disponibilidad, servicios, productos y citas; CRM básico
- Citas: workflow `pendiente_confirmacion` → `confirmada` → `completada`, prevención de solapamientos

> Los detalles de arquitectura, blueprints, flujos y diagrama están en `ARCHITECTURE.md`.

---

## 🛠️ Instalación y configuración

### Requisitos
- Python 3.11+
- PostgreSQL 13+
- Git, pip y virtualenv

### Pasos rápidos
1) Clonar e instalar dependencias
```bash
git clone https://github.com/tu-usuario/barber-brothers.git
cd barber-brothers
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
```

2) Variables de entorno (.env)
```bash
# Desarrollo
echo "DATABASE_URL=postgresql://usuario:password@localhost/barberia_db" > .env
echo "SECRET_KEY=tu-clave-secreta-aqui" >> .env
echo "FLASK_ENV=development" >> .env
# Opcional correo
echo "MAIL_SERVER=smtp.gmail.com" >> .env
echo "MAIL_USERNAME=tu-email@gmail.com" >> .env
echo "MAIL_PASSWORD=tu-password-app" >> .env
```

3) Base de datos y migraciones
```bash
createdb barberia_db
flask db upgrade
```

4) Datos iniciales (opcional)
```bash
python add_categories.py
```

5) Ejecutar en desarrollo
```bash
flask run
# http://localhost:5000
```

---

## 🐳 Docker (recomendado)
```bash
docker-compose up --build
# App: http://localhost:5000, PostgreSQL: 5432
```

Para producción con Docker:
```bash
docker build -t barber-brothers:prod .
docker run -d \
  -p 80:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="..." \
  -e MAIL_SERVER="smtp.gmail.com" \
  -e MAIL_USERNAME="..." \
  -e MAIL_PASSWORD="..." \
  barber-brothers:prod
```

Alternativa VPS (Gunicorn + Nginx): ver `DEPLOYMENT_MANUAL.md` y scripts en `deployment/`.

---

## 🔌 Endpoints y módulos
- Público (`/`): home, reservas, productos, contacto
- Confirmación de cita: `/confirmar-cita/<token>`
- API (`/api`):
  - GET `/api/disponibilidad/<barbero_id>/<fecha>?servicio_id=...`
  - POST `/api/agendar-cita`
- Admin (`/admin`): dashboard, barberos, clientes, servicios, productos, citas

> Estructura de carpetas y flujos detallados: ver `ARCHITECTURE.md`.

---

## 🔒 Seguridad
- CSRF (Flask-WTF), validaciones servidor/cliente, ORM contra SQLi
- Tokens firmados con caducidad para confirmar citas
- Recomendado: `SECRET_KEY` estable y único en producción

---

## 📈 Monitoreo y observabilidad (sugerencias)
- Uptime externo (UptimeRobot/Better Stack/Pingdom)
- Errores y trazas (Sentry backend + frontend)
- Logs centralizados (Grafana Loki/ELK o servicio gestionado)
- Métricas/APM (OpenTelemetry + Prometheus/Grafana o Datadog/New Relic)
- Email deliverability (Mailgun/SendGrid/Postmark) para tasas de entrega/clicks

---

## 🧪 Testing
Si tu entorno tiene pruebas:
```bash
python -m pytest
```

---

## 🤝 Contribución
- Fork y PRs bienvenidos
- Mantener estilo (PEP 8) y documentación
- Incluir tests cuando sea posible

---

## 📄 Licencia
MIT. Ver `LICENSE`.

---

## 👨‍💻 Autor
Desarrollado con ❤️ para modernizar la gestión de barberías.
