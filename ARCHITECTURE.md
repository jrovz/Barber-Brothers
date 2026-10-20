# Arquitectura del Proyecto: Barber Brothers

**Versión:** 1.0
**Fecha:** 24 de mayo de 2025

# Barber Brothers - Sistema de Gestión para Barbería

## 1. Resumen Ejecutivo

El proyecto Barber Brothers es una aplicación web completa desarrollada con el microframework **Flask**. Su arquitectura está diseñada para ser **modular, escalable y mantenible**, siguiendo el patrón **Model-View-Template (MVT)**, una variante del conocido Model-View-Controller (MVC).

La aplicación proporciona una plataforma integral para una barbería, incluyendo una página pública para clientes (con sistema de booking y tienda de productos), un panel de administración completo, y un panel específico para los barberos.

La pila tecnológica está orientada a un despliegue en producción robusto, utilizando **PostgreSQL** como base de datos, **Gunicorn** como servidor de aplicaciones WSGI y **Nginx** como proxy inverso.

## 2. Patrón Arquitectónico: Model-View-Template con Blueprints

La arquitectura central se basa en el uso de **Blueprints** de Flask, que permiten organizar la aplicación en componentes lógicos con un alto grado de cohesión y bajo acoplamiento.

```
      +------------------+      +------------------+
      |      Nginx       | <--> |   Archivos Est.  |
      | (Reverse Proxy)  |      | (CSS, JS, Imgs)  |
      +--------+---------+      +------------------+
               |
               v
      +------------------+
      |     Gunicorn     |
      |  (WSGI Server)   |
      +--------+---------+
               |
               v
      +------------------+
      |   Aplicación     |
      |      Flask       |
      +--------+---------+
               |
  +------------+-------------+----------------+
  |            |             |                |
  v            v             v                v
+----------+ +----------+  +----------+   +----------+
|  Public  | |  Admin   |  |   API    |   |  Barbero |
| Blueprint| | Blueprint|  | Blueprint|   | Blueprint|
+----------+ +----------+  +----------+   +----------+
      |            |             |                |
      |      +-----+-------------+-----+          |
      |      |                         |          |
      v      v                         v          v
  +--------------------------------------------------+
  |                  Lógica de Negocio                 |
  | (Vistas, Formularios, Autenticación, Servicios)  |
  +--------------------------+-----------------------+
                             |
                             v
  +--------------------------------------------------+
  |             Capa de Datos (SQLAlchemy)           |
  |  (Modelos: Producto, Cita, Barbero, Servicio...) |
  +--------------------------+-----------------------+
                             |
                             v
                   +------------------+
                   |    PostgreSQL    |
                   |   (Base de Datos)  |
                   +------------------+
```

### Desglose de Componentes:

*   **Model (Modelo):** Representa la capa de datos. Se implementa a través de los modelos de **SQLAlchemy** (`app/models/*.py`). Estos modelos definen la estructura de las tablas de la base de datos y las relaciones entre ellas (ej. `Producto`, `Cita`, `Barbero`).

*   **View (Vista/Controlador):** Es la capa de lógica de negocio. Se implementa en los archivos `routes.py` dentro de cada Blueprint (`app/public/routes.py`, `app/admin/routes.py`, etc.). Estas funciones de vista reciben las peticiones HTTP, interactúan con los modelos para obtener o guardar datos, y renderizan una plantilla para enviar la respuesta al cliente.

*   **Template (Plantilla):** Es la capa de presentación. Utiliza el motor de plantillas **Jinja2** y los archivos se encuentran en `app/templates/`. Las plantillas están organizadas por Blueprint y heredan de plantillas base (`public_base.html`, `admin_base.html`) para mantener la consistencia y seguir el principio DRY (Don't Repeat Yourself).

## 3. Estructura de Directorios

La estructura del proyecto está bien organizada y refleja la arquitectura modular:

```
barber-brothers/
├── app/                      # Directorio principal de la aplicación
│   ├── __init__.py           # Factory de la aplicación (create_app)
│   ├── admin/                # Blueprint para el panel de administración
│   │   └── routes/           # Vistas divididas por dominio (productos, citas, barberos...)
│   ├── api/                  # Blueprint para la API (hoy casi sin uso, ver sección 5)
│   ├── barbero/              # Blueprint para el panel de barberos
│   ├── public/               # Blueprint para la parte pública (incluye el booking real)
│   ├── models/               # Modelos de SQLAlchemy
│   ├── services/             # Lógica de negocio reutilizable (reservas, disponibilidad), sin HTTP
│   ├── static/               # Archivos estáticos (CSS, JS, imágenes)
│   ├── templates/            # Plantillas Jinja2
│   └── utils/                # Funciones de utilidad
├── tests/                    # Suite de pytest + fixtures (app, client, modelos de prueba)
├── .github/workflows/        # CI: corre la suite de tests en cada push/PR
├── migrations/               # Archivos de migración de Flask-Migrate
├── deployment/               # Scripts para despliegue y configuración
├── venv/                     # Entorno virtual de Python
└── wsgi.py                   # Punto de entrada para el servidor WSGI
```

## 4. Pila Tecnológica

### Backend
*   **Framework:** Flask
*   **ORM:** Flask-SQLAlchemy
*   **Migraciones:** Flask-Migrate (basado en Alembic)
*   **Autenticación:** Flask-Login
*   **Formularios:** Flask-WTF
*   **Envío de Correos:** Flask-Mail

### Frontend
*   **Lenguajes:** HTML5, CSS3, JavaScript (ES6)
*   **Motor de Plantillas:** Jinja2
*   **Interactividad:** JavaScript nativo para el slider y la lógica de booking (`booking.js`), que consume la API interna.

### Infraestructura y Despliegue
*   **Base de Datos:** PostgreSQL
*   **Servidor WSGI:** Gunicorn
*   **Proxy Inverso:** Nginx
*   **Gestor de Procesos:** `systemd` (en entorno Linux/Ubuntu)
*   **Automatización:** Scripts de Shell (`.sh`) para migraciones y configuración del servidor.
*   **Conexiones a la base y `preload_app = True`:** Gunicorn crea la app una vez en el proceso maestro y luego hace `fork()` de los workers. Una conexión abierta en el maestro (el `SELECT 1` de arranque) la heredaban todos los workers, y compartir una conexión SSL corrompe el flujo (`SSL error: decryption failed or bad record mac`, `SSL SYSCALL error: EOF detected`: 310 fallos en 16 meses). Por eso `create_app('production')` llama a `liberar_conexiones` antes de devolver la app, y `ProductionConfig` activa `pool_pre_ping` y `pool_recycle`. Regla: **nada que abra conexiones al importar o crear la app puede dejarlas abiertas**.

## 5. Flujos de Datos Clave

### Flujo de Booking de Citas
1.  **Cliente (Frontend):** Selecciona Barbero, Servicio y Fecha en `Home.html`.
2.  **JavaScript (`booking.js`):** Envía una petición `GET` a `/api/disponibilidad/...`.
3.  **Public Blueprint (Backend):** `/api/disponibilidad/<barbero_id>/<fecha>` (definida en `app/public/routes.py`, con el cálculo en `app/services/disponibilidad.py`) consulta los modelos `DisponibilidadBarbero` y `Cita` para calcular los horarios libres.
4.  **Public Blueprint (Backend):** Devuelve una respuesta JSON con los horarios disponibles.
5.  **JavaScript (`booking.js`):** Renderiza dinámicamente los horarios en la página.
6.  **Cliente (Frontend):** Selecciona un horario e introduce sus datos.
7.  **JavaScript (`booking.js`):** Envía una petición `POST` a `/api/agendar-cita` con todos los detalles.
8.  **Public Blueprint (Backend):** `/api/agendar-cita` (también en `app/public/routes.py`) delega en `app/services/reservas.py` (`crear_cita`), que valida los datos, crea un nuevo registro de `Cliente` (si no existe) y una `Cita` con estado `pendiente_confirmacion`, y envía un correo de confirmación con un token. La ruta solo traduce el resultado a JSON y escribe las cookies comerciales.
9.  **Cliente:** Hace clic en el enlace del correo.
10. **Public Blueprint (Backend):** La ruta `/confirmar-cita/<token>` valida el token y actualiza el estado de la cita a `confirmada`.

> Nota: pese al nombre de las URLs (`/api/...`), esta lógica vive en el Blueprint `public`, no en el Blueprint `api` (`app/api/routes.py`), que hoy solo expone un endpoint de ejemplo (`/api/info`). Es una discrepancia heredada del código, documentada aquí para que no confunda a quien la busque en el lugar "obvio".

### Capa de servicios (`app/services/`)

Las reglas que más importan (no doble-reservar, qué horarios están libres) viven en funciones que no conocen HTTP: reciben datos y devuelven un resultado tipado. Las rutas web solo traducen ese resultado a JSON y cookies. Así el mismo código lo usan el formulario de reservas y, más adelante, el chatbot, sin duplicar reglas.

*   `reservas.crear_cita(datos, enviar_correo=True)` → `ResultadoReserva` (cita y token, o un `ErrorReserva` con código, mensaje y estado HTTP). Bloquea la fila del barbero hasta el commit; **toda** salida con error hace `rollback()` para liberar ese bloqueo.
*   `disponibilidad.horarios_libres(barbero, fecha, servicio_id, excluir_pasadas=False)` → `ResultadoDisponibilidad`. Con `excluir_pasadas=True` descarta las horas que ya pasaron en la zona horaria del negocio (`app/utils/tiempo.ahora_negocio`).

Límite de peticiones: `Flask-Limiter` (`app.limiter`), sin límites globales; cada ruta declara el suyo. En producción `confiar_en_proxy` toma la IP real de `X-Forwarded-For` (Nginx); con almacenamiento en memoria el contador es por worker de Gunicorn, así que el límite efectivo es el declarado × el número de workers (para uno exacto, `RATELIMIT_STORAGE_URI` con Redis).

## 6. Evaluación y Puntos de Mejora

### Fortalezas
*   **Modularidad:** El uso de Blueprints es una excelente decisión que facilita el mantenimiento y la adición de nuevas funcionalidades.
*   **Separación de Intereses:** La estructura MVT está bien implementada, separando claramente la lógica, los datos y la presentación.
*   **Pila de Producción:** La elección de Nginx, Gunicorn y PostgreSQL es un estándar de la industria, garantizando rendimiento y fiabilidad.
*   **Automatización:** Los scripts de despliegue (`deployment/*.sh`) son un gran activo para la gestión del ciclo de vida de la aplicación.
*   **Seguridad:** Se implementan conceptos básicos de seguridad como CSRF (con Flask-WTF) y un sistema de autenticación y autorización con Flask-Login.

### Áreas de Mejora Potencial
*   ~~**Testing:** El proyecto carece de una suite de pruebas automatizadas.~~ Resuelto parcialmente: existe `tests/` (pytest) con cobertura de login de administrador, autorización de todas las rutas `/admin/*` y el flujo de agendamiento de citas, más un workflow de CI (`.github/workflows/tests.yml`) que las corre en cada push/PR. Sigue faltando cobertura de las vistas de barbero y del checkout de productos.
*   ~~**Gestión de Dependencias:** Formalizar las dependencias en un archivo `requirements.txt`.~~ Resuelto: `requirements.txt` es la única fuente de verdad (se eliminó el directorio `requirements/` que había quedado duplicado y desactualizado). Además, el job `dependency-audit` de `.github/workflows/tests.yml` corre `pip-audit` contra la base de datos de vulnerabilidades OSV en cada push/PR, y Dependabot (`.github/dependabot.yml`) abre PRs semanales de actualización para `pip` y para las GitHub Actions usadas en el CI.
*   **Tareas en Segundo Plano:** Para operaciones que pueden tardar (como el envío de correos), se podría integrar una cola de tareas como **Celery** con **Redis**. Esto evitaría que la aplicación se bloquee esperando la respuesta del servidor de correo y mejoraría la experiencia del usuario.
*   **Contenerización:** Utilizar **Docker** y **Docker Compose** simplificaría la configuración del entorno de desarrollo y estandarizaría el despliegue, haciéndolo más portable y consistente.
*   **Manejo de Archivos Estáticos:** Para una aplicación a gran escala, se podría considerar el uso de un servicio de almacenamiento de objetos (como Amazon S3 o Google Cloud Storage) para servir las imágenes subidas, delegando esta tarea a un servicio especializado.