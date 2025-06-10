# 💈 Barber Brothers - Sistema de Gestión para Barbería

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.2.3-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Descripción

**Barber Brothers** es una aplicación web completa para la gestión integral de una barbería moderna. Diseñada con tecnologías web estándar y una arquitectura limpia, ofrece tanto una interfaz pública elegante para clientes como un sistema administrativo robusto para la gestión del negocio.

## 🖼️ Vista Previa

![Página de inicio](website.png)
![Página de administracíon](admin.png)

## ⚡ Stack Tecnológico

- **🎨 Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **🔧 Backend**: Python 3.11+ con Flask 2.2.3
- **💾 Base de Datos**: PostgreSQL 15+ con SQLAlchemy 2.0
- **🔐 Autenticación**: Flask-Login con hash seguro
- **📧 Email**: Flask-Mail con confirmaciones automáticas
- **🚀 Deployment**: Docker + Docker Compose
- **🛡️ Seguridad**: CSRF Protection, validaciones dobles

## ✨ Características Principales

### 👥 Para Clientes
- **🎨 Diseño Moderno**: Interface responsiva con estética premium
- **📅 Sistema de Reservas**: Booking interactivo con disponibilidad en tiempo real
- **✂️ Selección de Barberos**: Perfiles detallados con especialidades
- **🛍️ Catálogo de Productos**: Organizados por categorías con gestión de inventario
- **🛒 Carrito de Compras**: Funcionalidad completa de e-commerce
- **📧 Confirmación por Email**: Sistema automático con tokens seguros
- **📱 Diseño Responsive**: Optimizado para todos los dispositivos

### ⚙️ Para Administradores
- **📊 Dashboard Inteligente**: Métricas en tiempo real y KPIs del negocio
- **👨‍💼 Gestión de Barberos**: CRUD completo con configuración de horarios
- **⏰ Control de Disponibilidad**: Sistema flexible por día y horario
- **🎯 CRM Avanzado**: Segmentación automática de clientes
- **📋 Gestión de Servicios**: Precios, duraciones y configuraciones
- **📦 Control de Inventario**: Stock, categorías y productos
- **📅 Administración de Citas**: Estados, notas e historial completo
- **💬 Centro de Mensajes**: Comunicación centralizada con clientes

## 🚀 Funcionalidades Avanzadas

### 🎯 Sistema de Segmentación Automática
Clasificación inteligente de clientes basada en comportamiento:

- **🆕 Nuevos**: Primera interacción (0 visitas)
- **🔄 Ocasionales**: 2-4 visitas, frecuencia variable
- **⭐ Recurrentes**: 5-9 visitas, alta frecuencia (< 45 días)
- **👑 VIP**: 10+ visitas, máxima fidelidad
- **😴 Inactivos**: Sin visitas recientes (60+ días)

### 📅 Sistema Inteligente de Citas
- **✅ Confirmación Automática**: Emails con tokens seguros
- **⏰ Validación de Conflictos**: Prevención automática de solapamientos
- **🔄 Estados de Workflow**: `pendiente` → `confirmada` → `completada`
- **📧 Notificaciones**: Plantillas HTML personalizadas
- **⚡ Disponibilidad en Tiempo Real**: Actualización instantánea

### 🏗️ Arquitectura Técnica
- **📐 Patrón MVC**: Separación clara de responsabilidades
- **🔌 API REST**: Endpoints para funcionalidades principales
- **🏭 Factory Pattern**: Inicialización limpia de la aplicación
- **🔒 Seguridad Multicapa**: CSRF, validaciones, sanitización
- **📊 Logging Estructurado**: Monitoreo y debugging facilitado

## 🛠️ Instalación y Configuración

### 📋 Requisitos Previos
- **Python 3.11+**
- **PostgreSQL 13+**
- **Git**
- **pip** y **virtualenv**

### 🚀 Configuración Rápida

1. **Clonar el repositorio**:
```bash
git clone https://github.com/tu-usuario/barber-brothers.git
cd barber-brothers
```

2. **Crear entorno virtual**:
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**:
```bash
# Crear archivo .env
echo "DATABASE_URL=postgresql://usuario:password@localhost/barberia_db" > .env
echo "SECRET_KEY=tu-clave-secreta-aqui" >> .env
echo "FLASK_ENV=development" >> .env
```

5. **Configurar base de datos**:
```bash
# Crear base de datos PostgreSQL
createdb barberia_db

# Ejecutar migraciones
flask db upgrade
```

6. **Datos iniciales (opcional)**:
```bash
python add_categories.py
```

7. **Iniciar aplicación**:
```bash
flask run
```

🎉 **¡Listo!** La aplicación estará disponible en `http://localhost:5000`

### 🐳 Docker (Recomendado)

Para un setup aún más rápido:

```bash
# Iniciar con Docker Compose
docker-compose up --build

# La aplicación estará en http://localhost:5000
# PostgreSQL en puerto 5432
```

## 📁 Estructura del Proyecto

```
Barber-Brothers/
├── 🔧 app/                    # Aplicación Flask principal
│   ├── __init__.py           # Factory pattern y configuración
│   ├── config/               # Configuración por entornos
│   ├── models/               # 8 modelos de datos (ORM)
│   │   ├── admin.py          # Sistema de usuarios
│   │   ├── barbero.py        # Gestión de barberos
│   │   ├── cliente.py        # CRM y citas
│   │   ├── producto.py       # Inventario
│   │   └── ...
│   ├── admin/                # Panel administrativo
│   ├── public/               # Frontend público
│   ├── api/                  # Endpoints REST
│   ├── templates/            # Jinja2 templates
│   │   ├── admin/            # Templates admin
│   │   ├── public/           # Templates públicos
│   │   └── email/            # Templates email
│   ├── static/               # Assets frontend
│   │   ├── css/              # Estilos (68KB total)
│   │   ├── js/               # Scripts (60KB total)
│   │   ├── images/           # Recursos gráficos
│   │   └── uploads/          # Archivos subidos
│   └── utils/                # Utilidades locales
├── 🐳 docker-compose.yml     # Orquestación Docker
├── 🔧 Dockerfile             # Container configuration
├── 📚 docs/                  # Documentación técnica
├── 🗃️ migrations/            # Migraciones de BD
├── ⚙️ requirements.txt       # Dependencias Python
└── 📋 README.md              # Este archivo
```

## 🔧 Configuración de Entornos

### 🛠️ Desarrollo
```python
# .env
DATABASE_URL=postgresql://user:pass@localhost/barberia_db
FLASK_ENV=development
SECRET_KEY=development-key
DEBUG=True
```

### 🚀 Producción
```python
# Variables de entorno requeridas
DATABASE_URL=postgresql://user:pass@servidor/barberia_db
SECRET_KEY=clave-super-segura
FLASK_ENV=production
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-password-app
```

## 📊 Funcionalidades por Módulo

### 🌐 Módulo Público (`/`)
- **🏠 Página Principal**: Showcase servicios y barberos
- **📅 Sistema de Reservas**: `/` (widget integrado)
- **🛍️ Catálogo**: `/productos` (por categorías)
- **📞 Contacto**: `/contacto` (formulario CRM)
- **✅ Confirmación**: `/confirmar-cita/<token>`

### ⚙️ Módulo Admin (`/admin`)
- **📊 Dashboard**: `/admin/` (métricas y KPIs)
- **👨‍💼 Barberos**: `/admin/barberos` (CRUD + horarios)
- **🎯 Clientes**: `/admin/clientes` (CRM y segmentación)
- **📋 Servicios**: `/admin/servicios` (precios y configuración)
- **📦 Productos**: `/admin/productos` (inventario completo)
- **📅 Citas**: `/admin/citas` (gestión y seguimiento)

### 🔌 API REST (`/api`)
- **GET** `/api/disponibilidad/<barbero_id>/<fecha>` - Horarios
- **POST** `/api/agendar-cita` - Nueva reserva
- Respuestas JSON estructuradas

## 🔒 Seguridad Implementada

- **🛡️ CSRF Protection**: Flask-WTF en formularios
- **🔐 Autenticación**: Hash seguro con Werkzeug
- **✅ Validación Dual**: Cliente + Servidor
- **📁 Upload Security**: Tipos y tamaños validados
- **🔍 SQL Injection**: Protección via ORM
- **📧 Token Security**: Confirmaciones con caducidad

## 🚀 Deployment

### 🐳 Docker Production
```bash
# Build optimizado
docker build -t barber-brothers:prod .

# Deploy con variables de entorno
docker run -d \
  -p 80:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="..." \
  barber-brothers:prod
```

### 🖥️ VPS Traditional
```bash
# Con gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:app

# Con nginx reverse proxy (recomendado)
```

## 📈 Performance

- **⚡ Carga Rápida**: CSS (68KB) + JS (60KB) optimizados
- **🗃️ Base de Datos**: Índices en campos críticos
- **🔄 Caching**: Flask-Caching para consultas frecuentes
- **📱 Responsive**: Optimizado para móviles
- **🎨 Assets**: Compresión de imágenes automática

## 🧪 Testing

```bash
# Ejecutar tests
python -m pytest tests/

# Coverage
coverage run -m pytest
coverage report
```

## 📚 Documentación Adicional

- **📖 Funcionalidades de BD**: `docs/DATABASE_FUNCTIONALITY_MANUAL.md`
- **🐳 Docker Guide**: `DOCKER_README.md`
- **🚀 Deployment**: `DEPLOYMENT_MANUAL.md`

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Por favor:

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** tus cambios (`git commit -am 'Add: nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. **Abre** un Pull Request

### 📋 Guidelines de Contribución
- Mantener el stack tecnológico definido
- Seguir PEP 8 para Python
- Documentar nuevas funcionalidades
- Incluir tests para código nuevo
- Actualizar documentation si es necesario

## 📝 Changelog

### 🔄 v2.0.0 (Actual)
- ✅ Eliminación completa de dependencias cloud (GCP/Azure)
- ✅ Arquitectura simplificada y limpia
- ✅ Stack tecnológico puro (HTML, CSS, JS, Flask, PostgreSQL)
- ✅ Configuración simplificada para development/production
- ✅ Documentación actualizada

### 📜 v1.x.x (Legacy)
- Sistema original con integraciones cloud

## 📄 Licencia

Este proyecto está licenciado bajo la **MIT License** - ver el archivo [LICENSE](LICENSE) para detalles.

## 👨‍💻 Autor

Desarrollado con ❤️ para modernizar la gestión de barberías.

---

⭐ **¡Si te gusta el proyecto, dale una estrella en GitHub!** ⭐


