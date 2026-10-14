# Guía: de Barber Brothers a plantilla multi-tenant

**Fecha:** 14 de octubre de 2026
**Punto de partida:** rama `main`, commit «fix: cache-bust static assets…» (11/09/2026). La carpeta local y GitHub están iguales.
**Objetivo:** que una sola instalación de esta aplicación (un servidor OVH, un código) atienda a varias barberías, cada una con su dominio, su marca y sus datos aislados.

---

## Cómo usar esta guía

- Sigue las fases **en orden**. Cada una deja la aplicación funcionando y desplegable; no hay que terminar todo para subir algo a producción.
- Cada fase tiene: **qué se hace**, **archivos a tocar**, **pasos**, y **cómo saber que terminó** (criterio de aceptación).
- Trabaja cada fase en su propia rama: `git checkout -b fase-1-marca`, y fusiona a `main` solo con las pruebas en verde.
- Los tiempos son estimados a medio tiempo.

| Fase | Resultado | Tiempo estimado | Estado |
|---|---|---|---|
| 0 | Base segura y pruebas que corren en cualquier máquina | 1–2 días | **Iniciada** (ver sección 0) |
| 1 | La marca sale del código y vive en la base de datos | 3–5 días | Pendiente |
| 2 | La app reconoce la barbería por el dominio | 3–4 días | Pendiente |
| 3 | Imágenes separadas por barbería | 1–2 días | Pendiente |
| 4 | Script para crear una barbería nueva en minutos | 2–3 días | Pendiente |
| 5 | Dominios, subdominios y SSL en Nginx | 1–2 días | Pendiente |
| 6 | Pruebas de aislamiento y lanzamiento | 1–2 días | Pendiente |

---

## Diagnóstico del proyecto (revisión del 14/10/2026)

### Lo que ya está bien y se conserva
- Arquitectura por blueprints: `public`, `admin`, `barbero`, `api`.
- Modelo de datos completo para una barbería: `Barbero`, `DisponibilidadBarbero`, `BloqueoHorario`, `Servicio`, `BarberoServicio` (precio por barbero), `Cliente`, `Cita` (con token de confirmación), `Producto`, `Categoria`, `Pedido`, `Slider`.
- Migraciones con Alembic, 18 pruebas con pytest y GitHub Actions con `pip-audit`.
- Despliegue documentado para OVH (Gunicorn + Nginx + PostgreSQL).

### Hallazgos que bloquean el multi-tenant

| # | Hallazgo | Dónde | Gravedad |
|---|---|---|---|
| H1 | Un barbero puede quedar con sesión de **administrador**: admin y barbero guardan en sesión solo el número de ID, y el cargador de usuario busca primero en la tabla de admins. | `app/__init__.py` (`load_user`, definido dos veces) | **Crítica** — corregida en fase 0 |
| H2 | Dos personas pueden reservar el mismo horario si envían la reserva al mismo tiempo: se revisa el solapamiento y luego se guarda, sin bloqueo. | `app/public/routes.py` → `agendar_cita` | Alta — corregida en fase 0 |
| H3 | La API de reservas acepta fechas pasadas, barberos inactivos o servicios inexistentes si alguien la llama directamente. | `agendar_cita` | Media — corregida en fase 0 |
| H4 | Las pruebas fallan en GitHub Actions y en cualquier PC sin `.env`: `ProductionConfig` lanza error **al importar** si falta `DATABASE_URL`. | `app/config/__init__.py` | Alta — corregida en fase 0 |
| H5 | `requirements.txt` no coincide con lo instalado en tu `venv` (SQLAlchemy 2.0.20 vs 2.0.40, Flask-SQLAlchemy 3.0.3 vs 3.1.1, psycopg2 2.9.5 vs 2.9.10). Con Python 3.13 las versiones fijadas **no instalan**. | `requirements.txt` | Media — corregida en fase 0 |
| H6 | Se registran en el log todos los datos del cliente (nombre, correo, teléfono) en cada reserva. Bajo la Ley 1581 conviene minimizarlo. | `agendar_cita` | Media — corregida en fase 0 |
| H7 | La marca está escrita a mano en **35 archivos** (nombre, dos teléfonos distintos, Instagram, remitente de correo, textos legales, JS). | ver fase 1 | Bloquea fase 1 |
| H8 | No existe el concepto de «negocio»: 153 consultas en 22 archivos asumen una sola barbería. | todo `app/` | Bloquea fase 2 |
| H9 | Todas las imágenes van a `app/static/uploads/` (16 referencias). | `app/admin/utils.py`, rutas de admin | Bloquea fase 3 |
| H10 | `app/health.py` no está registrado y usa `db.session.execute('SELECT 1')` sin `text()`, que falla en SQLAlchemy 2. Es código muerto. | `app/health.py` | Baja — limpiar en fase 1 |
| H11 | La tienda (productos, carrito, pedidos) está siempre activa; muchas barberías no la usarán. | `public/routes.py`, plantillas | Se resuelve en fase 4 con un interruptor por negocio |

---

## Decisión de arquitectura: un esquema de PostgreSQL por barbería

```
                 ┌──────────────── public (esquema compartido) ────────────────┐
                 │ negocios: id, slug, nombre, dominio, colores, logo, plan... │
                 └──────────────────────────────────────────────────────────────┘
barberbrothers.co ─┐
                   ├─> Nginx ─> Gunicorn ─> Flask ─> middleware de negocio
otra.tudominio.co ─┘                                   │  1. lee el Host
                                                       │  2. busca en public.negocios
                                                       │  3. SET search_path TO <slug>, public
                                                       ▼
                      esquema "barberbrothers": barbero, cita, cliente, servicio, ...
                      esquema "otra":           barbero, cita, cliente, servicio, ...
```

**Por qué esquemas y no una columna `negocio_id`:**
- Las 153 consultas siguen funcionando sin agregar filtros; olvidar un filtro sería una fuga de datos entre barberías.
- Las restricciones únicas actuales (`username`, `categorias.nombre`, `numero_pedido`) siguen siendo válidas por barbería sin tocarlas.
- Un respaldo o borrado de una barbería es `pg_dump -n <slug>` o `DROP SCHEMA`.
- Límite práctico: decenas de barberías por servidor. Si algún día pasas de ~50, se reevalúa.

**Lo que hay que cuidar:**
- El `search_path` vive en la **conexión**, y las conexiones se reutilizan (pool). Hay que fijarlo en cada petición y restaurarlo al devolver la conexión.
- Las migraciones de Alembic deben correr una vez por esquema.

---

## Fase 0 — Base segura (iniciada)

**Rama sugerida:** `fase-0-base-segura`

### Cambios ya hechos en tu carpeta (revísalos con `git diff` antes de hacer commit)

| Archivo | Cambio |
|---|---|
| `app/__init__.py` | Un solo `user_loader`. La sesión guarda `admin:<id>` o `barbero:<id>`, así un barbero nunca carga como admin (H1). Las sesiones viejas (solo número) se invalidan: **todos tendrán que volver a iniciar sesión una vez**. |
| `app/models/admin.py` | `get_id()` devuelve `admin:<id>`. |
| `app/models/barbero.py` | `get_id()` devuelve `barbero:<id>`. |
| `app/public/routes.py` | `agendar_cita`: valida que el barbero exista y esté activo, que el servicio exista y esté activo, y que la fecha no esté en el pasado (H3). Bloquea la fila del barbero con `SELECT … FOR UPDATE` antes de revisar solapamientos, para que dos reservas simultáneas se atiendan en fila (H2). Deja de registrar en el log los datos personales completos (H6). |
| `app/config/__init__.py` | `ProductionConfig` ya no falla al importar; la validación de `DATABASE_URL` y `SECRET_KEY` se hace en `create_app('production')` (H4). |
| `requirements.txt` | Versiones alineadas con tu `venv` local, que funcionan en Python 3.11 y 3.13 (H5). Además Werkzeug 3.1.9 y urllib3 2.8.0, que corrigen vulnerabilidades que `pip-audit` reportaba en las versiones anteriores. |
| `tests/conftest.py` | `login_as` usa `user.get_id()`. |
| `tests/test_auth.py`, `tests/test_booking.py` | Pruebas nuevas: barbero no puede entrar al admin aunque comparta ID; fecha pasada, barbero inactivo y servicio inexistente devuelven 400; fechas de prueba movidas al futuro. |

**Verificación hecha:** 24 pruebas en verde con Python 3.11 y 3.13 y `pip-audit` sin vulnerabilidades. Prueba de concurrencia con PostgreSQL real (5 reservas simultáneas al mismo barbero y hora): **antes** se guardaban 5 citas duplicadas; **después** se guarda 1 y las otras 4 reciben «horario ocupado» (409).

### Pasos para cerrar la fase 0
1. En tu PC, dentro de la carpeta del proyecto:
   ```powershell
   git checkout -b fase-0-base-segura
   git status          # deben aparecer los archivos de la tabla
   git diff            # revisa cada cambio
   venv\Scripts\activate
   pip install -r requirements.txt
   python -m pytest tests -q
   ```
   Deben pasar **todas** las pruebas sin necesidad de `.env`.
2. Prueba manual en local (`flask run`):
   - Entra como admin y como barbero en ventanas distintas: cada uno ve solo su panel.
   - Haz una reserva desde la web pública y confírmala desde el correo.
3. Commit y push:
   ```powershell
   git add -A
   git commit -m "fase 0: sesiones por tipo de usuario, bloqueo de doble reserva y validaciones"
   git push -u origin fase-0-base-segura
   ```
   Revisa que GitHub Actions quede en verde y fusiona a `main`.
4. **Respaldos antes de desplegar** (en el servidor OVH):
   ```bash
   pg_dump -Fc "$DATABASE_URL" > ~/backups/bb_$(date +%F).dump
   ```
   Y programa un respaldo diario con `crontab -e`:
   ```
   0 3 * * * pg_dump -Fc "postgresql://..." > /home/ubuntu/backups/bb_$(date +\%F).dump && find /home/ubuntu/backups -mtime +14 -delete
   ```
5. Despliega como siempre (`git pull`, `pip install -r requirements.txt`, reiniciar Gunicorn). Avisa a Barber Brothers que el admin y los barberos deben volver a iniciar sesión.

**Terminado cuando:** pruebas en verde en GitHub, despliegue hecho, respaldo diario funcionando.

### Pendiente opcional de la fase 0
- Validar en el servidor que la hora pedida esté dentro del horario del barbero (`Barbero.esta_disponible`). Hoy solo lo garantiza la interfaz. Requiere confirmar que todos los barberos tienen horarios cargados, por eso no se activó.
- Límite de peticiones a `/api/agendar-cita` (por ejemplo 10 por minuto por IP) para evitar spam.

---

## Fase 1 — Sacar la marca del código

**Rama:** `fase-1-marca` · **Objetivo:** que cambiar de barbería sea cambiar datos, no código. Sirve aunque nunca tengas un segundo cliente.

### 1.1 Crear el modelo `Negocio`
Archivo nuevo `app/models/negocio.py`:

```python
from app import db

class Negocio(db.Model):
    __tablename__ = 'negocios'
    __table_args__ = {'schema': 'public'}   # vivirá siempre en el esquema compartido

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)        # 'barberbrothers'
    nombre = db.Column(db.String(120), nullable=False)                  # 'Barber Brothers'
    dominio = db.Column(db.String(255), unique=True)                    # 'labarberbrothers.com'
    subdominio = db.Column(db.String(63), unique=True)                  # 'barberbrothers'
    telefono = db.Column(db.String(30))
    whatsapp = db.Column(db.String(30))                                 # solo dígitos: 573143782855
    instagram = db.Column(db.String(120))
    direccion = db.Column(db.String(255))
    ciudad = db.Column(db.String(80))
    email_contacto = db.Column(db.String(120))
    remitente_correo = db.Column(db.String(120))
    color_primario = db.Column(db.String(7), default='#111111')
    color_secundario = db.Column(db.String(7), default='#C9A227')
    logo_url = db.Column(db.String(255))
    razon_social = db.Column(db.String(160))                            # para términos y privacidad
    nit = db.Column(db.String(30))
    tienda_activa = db.Column(db.Boolean, default=False)
    plan = db.Column(db.String(20), default='pro')                      # basico | pro | premium
    activo = db.Column(db.Boolean, default=True)
```

Crea la migración: `flask db migrate -m "crear tabla negocios"` y revísala a mano antes de `flask db upgrade`.

### 1.2 Cargar el negocio en cada petición (todavía uno solo)
En `app/__init__.py`, registra un `before_request` que haga `g.negocio = Negocio.query.filter_by(slug='barberbrothers').first()` y un `context_processor` que exponga `negocio` a todas las plantillas. En la fase 2 esto se reemplaza por la detección por dominio.

### 1.3 Reemplazar la marca en los 35 archivos
Lista exacta (búscalos con `git grep -n "Barber Brothers\|labarberbrothers\|3143782855\|314 378 2855\|3102160496\|la_barberbrothers"`):

| Grupo | Archivos | Reemplazo |
|---|---|---|
| Plantillas públicas | `public_base.html`, `Home.html`, `contacto.html`, `servicios.html`, `checkout.html`, `confirmation_status.html`, `confirmacion_pedido.html`, `includes/critical-css.html` | `{{ negocio.nombre }}`, `{{ negocio.telefono }}`, `https://wa.me/{{ negocio.whatsapp }}`, `{{ negocio.instagram }}` |
| Textos legales | `terminos.html`, `privacidad.html`, `cookies.html` | `{{ negocio.razon_social }}`, `{{ negocio.nit }}`, `{{ negocio.direccion }}`, `{{ negocio.email_contacto }}` |
| Paneles | `admin/admin_base.html`, `barbero/barbero_base.html`, `barbero/login.html` | `{{ negocio.nombre }}` |
| Correos | `email/confirm_appointment.html` y `.txt`, `app/models/email.py` | pasar `negocio` al render; remitente = `(negocio.remitente_correo or negocio.nombre, MAIL_USERNAME)` |
| Python | `config/__init__.py`, `public/routes.py`, `admin/forms.py`, `health.py`, `utils/*.py` (formatters, sitemap, business_metrics, business_cookies, cart_optimizer, pricing, canonical_helper), `middleware/business_middleware.py` | leer de `g.negocio`; en `sitemap_generator` y `canonical_helper` usar `request.host_url` en vez del dominio fijo |
| JavaScript | `booking.js`, `slider.js`, `smart_cart.js`, `business_optimization.js`, `dashboard_charts.js` | inyectar en `public_base.html` un `<script>window.NEGOCIO = {{ negocio_publico|tojson }};</script>` y leer de ahí |
| Colores | `public_styles.css` | variables CSS `--color-primario` definidas en `public_base.html` desde `negocio.color_primario` |

Consejo: hazlo por grupos, con un commit por grupo, y revisa la web después de cada uno.

### 1.4 Limpieza
- Borra `app/health.py` (H10) o regístralo corrigiendo `text("SELECT 1")`.
- Corrige las dos versiones del teléfono de Barber Brothers (3143782855 y 3102160496): pregunta cuál es el correcto.

**Terminado cuando:** `git grep "Barber Brothers"` solo aparece en la migración/semilla de datos; la web se ve igual que antes; cambiar `negocio.nombre` en la base cambia el nombre en toda la web y en los correos.

---

## Fase 2 — Reconocer la barbería por el dominio

**Rama:** `fase-2-tenant`

### 2.1 Mover las tablas de Barber Brothers a su esquema
Migración manual (Alembic `op.execute`):
```sql
CREATE SCHEMA barberbrothers;
ALTER TABLE public.barbero SET SCHEMA barberbrothers;
-- repetir para: disponibilidad_barbero, bloqueo_horario, servicio, servicio_imagenes,
-- barbero_servicio, cliente, mensaje, cita, user, categorias, productos, pedidos,
-- pedido_items, sliders, y cualquier otra tabla del proyecto (lista con \dt en psql)
```
`public` se queda solo con `negocios` y `alembic_version` global. **Haz un `pg_dump` antes.** Pruébalo primero en una copia local de la base.

### 2.2 Middleware de negocio
Archivo nuevo `app/middleware/tenant.py`:
1. `before_request`: toma `request.host` (sin puerto), busca por `dominio` o por `subdominio` en `public.negocios`. Si no existe o `activo=False` → 404.
2. Guarda `g.negocio` y ejecuta `db.session.execute(text("SET search_path TO :s, public"), {"s": g.negocio.slug})`. Valida que el slug solo tenga `[a-z0-9_]` antes de usarlo.
3. `teardown_request`: `RESET search_path` (o `SET search_path TO public`) para que la conexión vuelva limpia al pool.
4. Cachea la búsqueda de negocios en memoria por 60 s para no consultar en cada petición.

### 2.3 Sesiones y cookies por negocio
- `SESSION_COOKIE_DOMAIN = None` (cada dominio tiene su cookie).
- El token de confirmación de citas incluye el ID de cita; agrega el `slug` al payload y verifica que coincida con `g.negocio.slug`.
- El `user_loader` ya distingue admin/barbero; como cada esquema tiene sus propias tablas, un admin de una barbería no existe en otra.

### 2.4 Alembic con varios esquemas
En `migrations/env.py`, recorre `SELECT slug FROM public.negocios` y, para cada uno, ejecuta las migraciones con `connection.execute(text(f'SET search_path TO {slug}, public'))` y `version_table_schema=slug`. Así cada barbería tiene su propio historial de versiones.

**Terminado cuando:** Barber Brothers funciona igual desde su dominio; un segundo negocio de prueba (`demo`) en `demo.localhost` muestra datos vacíos y su propia marca.

---

## Fase 3 — Imágenes por barbería

- `UPLOAD_FOLDER` pasa a ser una función: `os.path.join(base_uploads, g.negocio.slug, 'barberos')`, etc.
- Archivos a tocar: `app/admin/utils.py` (guardado de imágenes), rutas de admin de barberos, productos, servicios y sliders, `utils/path_checker.py`.
- Mueve las imágenes actuales: `app/static/uploads/*` → `app/static/uploads/barberbrothers/*` y actualiza las URLs guardadas en la base con un `UPDATE … SET imagen_url = replace(imagen_url, '/uploads/', '/uploads/barberbrothers/')`.
- Nginx sigue sirviendo `/static/uploads/` directamente.

**Terminado cuando:** subir una foto en `demo` no aparece en Barber Brothers ni al revés.

---

## Fase 4 — Crear una barbería nueva con un comando

Script `deployment/crear_negocio.py`:
```
python deployment/crear_negocio.py --slug lavida --nombre "La Vida Barbería" \
    --subdominio lavida --whatsapp 573001234567 --admin-email dueno@correo.com --plan pro
```
Hace, en orden: inserta en `public.negocios` → `CREATE SCHEMA` → corre migraciones en ese esquema → crea el admin con contraseña temporal → crea carpetas de uploads → imprime la URL y la contraseña.

Agrega también:
- `tienda_activa`: oculta menú, rutas y plantillas de productos/carrito si es `False` (H11).
- Plantilla de servicios de ejemplo (corte, barba, corte + barba) para que la barbería no arranque vacía.

**Terminado cuando:** crear una barbería, entrar como su admin, cargar un barbero y recibir una reserva toma menos de 30 minutos.

---

## Fase 5 — Dominios y SSL

1. Compra un dominio para el producto (por ejemplo `tureserva.co`) y crea un registro DNS comodín `*.tureserva.co → IP del servidor`.
2. Certificado comodín con Certbot (requiere validación DNS):
   ```bash
   sudo certbot certonly --manual --preferred-challenges dns -d "tureserva.co" -d "*.tureserva.co"
   ```
3. Nginx: un `server` para `*.tureserva.co` y uno por cada dominio propio de cliente, todos con `proxy_set_header Host $host;` hacia Gunicorn. Parte de `deployment/nginx_seo_config.conf`.
4. Para dominios propios del cliente: el cliente apunta su dominio a tu IP, y tú ejecutas `sudo certbot --nginx -d sudominio.com`.
5. Revisa RAM del servidor de 12 USD: con varias barberías, ajusta los workers de Gunicorn (`2 × núcleos + 1`) y vigila con `htop`.

**Terminado cuando:** `demo.tureserva.co` responde con HTTPS válido.

---

## Fase 6 — Pruebas de aislamiento y lanzamiento

Pruebas nuevas en `tests/test_tenant.py` (con PostgreSQL real, no SQLite, porque SQLite no tiene esquemas):
- Crear negocios A y B; un barbero creado en A no aparece en la API pública de B.
- Un admin de A no puede iniciar sesión en el dominio de B.
- Un token de confirmación de A no confirma nada en B.
- Una imagen subida en A no se sirve bajo la carpeta de B.

En GitHub Actions agrega un servicio `postgres:16` para correr estas pruebas.

**Lista de lanzamiento:**
- [ ] Respaldos diarios por esquema funcionando y probados (restaura uno en local).
- [ ] Monitoreo básico: un ping externo gratuito (UptimeRobot o similar) a cada dominio.
- [ ] Política de tratamiento de datos por negocio (Ley 1581) publicada en cada sitio.
- [ ] Barber Brothers migrado y funcionando 1 semana sin incidentes antes de vender a otra barbería.

---

## Reglas de trabajo para todo el proyecto
- Nunca escribir datos de una barbería concreta en el código: todo sale de `g.negocio`.
- Ninguna consulta SQL escrita a mano con nombres de esquema fijos.
- Cada fase en su rama, con pruebas en verde antes de fusionar.
- Respaldo antes de cada migración en producción.
