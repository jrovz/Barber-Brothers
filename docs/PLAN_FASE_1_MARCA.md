# Plan de acción — Fase 1: sacar la marca del código

**Fecha:** 14 de octubre de 2026
**Rama:** `fase-1-marca` (créala desde `main` con la fase 0 ya fusionada)
**Duración estimada:** 4–6 días a medio tiempo, en 9 pasos con un commit cada uno
**Resultado esperado:** la web de Barber Brothers se ve igual que hoy, pero el nombre, los teléfonos, las redes, la dirección, los textos legales, los colores y el SEO salen de una tabla `negocios`. Cambiar de barbería es cambiar una fila, no 35 archivos.

---

## 0. Antes de empezar: decisiones y datos que faltan

La revisión encontró **datos contradictorios** dentro del mismo sitio. Hay que decidir el valor correcto antes de pasarlos a la base de datos, porque también afectan el SEO de Barber Brothers hoy.

| Dato | Lo que aparece en el código | Dónde | Decisión |
|---|---|---|---|
| Teléfono | `314 378 2855` (pie de página, botón de WhatsApp, contacto, confirmación de cita) y `310 216 0496` (datos estructurados de Google, tienda, términos) | `public_base.html`, `Home.html`, `checkout.html`, `confirmacion_pedido.html`, `contacto.html`, `confirmation_status.html` | ☐ ¿Uno solo? ¿O citas = 314 y tienda = 310? |
| Ciudad | «Arkambuco, Boyacá» (pie de página, meta geo, datos estructurados) y «Ibagué» (título y descripción de la portada) | `public_base.html`, `Home.html` | ☐ ¿Cuál es la ciudad real? ¿Se escribe «Arcabuco»? |
| Dominio | `barberbrothers.com` en `robots.txt` y en el `@id` de los datos estructurados; el sitio real es `labarberbrothers.com` | `app/static/robots.txt`, `Home.html` | ☐ Confirmar `labarberbrothers.com` |
| Instagram | `instagram.com/la_barberbrothers` (contacto) e `instagram.com/barberbrothers` (datos estructurados) | `contacto.html`, `Home.html` | ☐ Confirmar `la_barberbrothers` |
| Nombre | «Barber Brothers» y «La Barber Brothers» | varios | ☐ ¿Cuál es el nombre comercial? |
| Datos legales | Razón social, NIT o cédula, dirección y correo del responsable del tratamiento de datos | `terminos.html`, `privacidad.html`, `cookies.html` | ☐ Pedirlos a Barber Brothers |
| Tienda | Productos, carrito y pedidos siempre activos | rutas y menú públicos | ☐ ¿La siguen usando? |

> Hallazgo de SEO: Google hoy recibe dos teléfonos, dos ciudades y un dominio que no es el del sitio. Solo con unificar estos datos, Barber Brothers mejora su ficha en buscadores. Es un argumento para cobrar la actualización.

Si algún dato no llega a tiempo, usa el valor del pie de página actual y corrígelo después desde el panel (paso 5). No bloquea el trabajo.

---

## Mapa del trabajo

```
Paso 1  Modelo Negocio + migración + datos de Barber Brothers     (base de datos)
Paso 2  Cargar el negocio en cada petición                          (Python)
Paso 3  Prueba automática que detecta marca escrita a mano          (red de seguridad)
Paso 4  Plantillas: base, portada, contacto, confirmaciones          (lo que ve el cliente)
Paso 5  Panel de admin «Configuración del negocio»                  (el dueño edita sus datos)
Paso 6  Textos legales: términos, privacidad, cookies               (Ley 1581)
Paso 7  Correos, remitente y paneles de admin y barbero             (comunicaciones)
Paso 8  SEO: robots.txt, sitemap, canonical, datos estructurados    (Google)
Paso 9  Colores, logo, interruptor de tienda y limpieza              (identidad visual)
```

Cada paso termina con las pruebas en verde, la web revisada a ojo en local y un commit.

---

## Paso 1 — Modelo `Negocio`, migración y datos de Barber Brothers
**Tiempo:** 3–4 h · **Commit:** `fase 1.1: modelo Negocio con datos de Barber Brothers`

**Archivos nuevos:** `app/models/negocio.py`, migración en `migrations/versions/`
**Archivos a tocar:** `app/models/__init__.py` (importar el modelo)

### Campos

| Grupo | Campos |
|---|---|
| Identidad | `slug` (único), `nombre`, `nombre_corto`, `eslogan`, `anio_fundacion` |
| Contacto | `telefono`, `whatsapp` (solo dígitos con 57), `telefono_tienda` (opcional), `email_contacto` |
| Redes | `instagram_url`, `tiktok_url`, `facebook_url` |
| Ubicación | `direccion`, `ciudad`, `departamento`, `pais` (por defecto «Colombia»), `latitud`, `longitud` |
| Legal | `razon_social`, `nit`, `direccion_legal`, `email_datos_personales` |
| Web | `dominio`, `subdominio` (único, para la fase 2), `zona_horaria` (por defecto `America/Bogota`) |
| SEO | `seo_titulo`, `seo_descripcion`, `seo_palabras_clave` |
| Contenido | `historia` (texto largo de la sección «Nuestra historia»), `horario_atencion` (JSON: `[{"dias": ["Monday", …], "abre": "08:00", "cierra": "18:00"}]`) |
| Correo | `remitente_nombre` |
| Visual | `logo_url`, `favicon_url`, `color_primario`, `color_secundario`, `color_acento` |
| Producto | `tienda_activa` (bool), `plan` (`basico`/`pro`/`premium`), `activo` (bool) |
| Auditoría | `creado`, `actualizado` |

**Importante:** en esta fase **no** pongas `__table_args__ = {'schema': 'public'}`. SQLite, que usan las pruebas, no tiene esquemas y las pruebas fallarían. El esquema se agrega en la fase 2. *(La guía general mostraba ese atributo en el ejemplo; esta es la versión correcta para la fase 1).*

Agrega dos métodos al modelo:
- `whatsapp_link(texto=None)` → `https://wa.me/<whatsapp>?text=<texto codificado>`
- `datos_publicos()` → diccionario con lo que puede ver el navegador (nombre, teléfono, WhatsApp, colores). Nunca NIT ni correos internos.

### Migración
1. `flask db migrate -m "crear tabla negocios"`. Revisa el archivo generado y deja solo la creación de `negocios`.
2. En la misma migración, agrega una inserción con `op.bulk_insert` con los datos de Barber Brothers. Copia los textos actuales tal cual: la historia de `Home.html`, el horario del JSON-LD, la dirección del pie de página.
3. `flask db upgrade` en tu base local y revisa con `psql`: `SELECT slug, nombre, telefono FROM negocios;`

**Listo cuando:** la tabla existe en local con una fila `barberbrothers` y `flask db downgrade` la borra sin errores.

---

## Paso 2 — Cargar el negocio en cada petición
**Tiempo:** 2–3 h · **Commit:** `fase 1.2: g.negocio y contexto global en plantillas`

**Archivo nuevo:** `app/utils/negocio_actual.py`
**Archivo a tocar:** `app/__init__.py`

1. Función `obtener_negocio()`:
   - Por ahora busca por el slug de la variable de entorno `NEGOCIO_SLUG` (por defecto `barberbrothers`). En la fase 2 se reemplaza por la búsqueda por dominio, **solo esta función**.
   - Guarda el resultado en caché en memoria por 60 segundos, para no consultar la base en cada petición.
   - Si no existe la fila, registra un error claro y devuelve un objeto con valores neutros, para que el sitio no se caiga.
2. En `create_app`:
   - `@app.before_request` → `g.negocio = obtener_negocio()`
   - `@app.context_processor` → expone `negocio` a todas las plantillas, incluidas las de correo.
3. Agrega `NEGOCIO_SLUG=barberbrothers` a tu `.env` y al del servidor.

**Pruebas nuevas** (`tests/test_negocio.py`):
- Con una fila de prueba, `GET /` devuelve 200 y contiene `negocio.nombre`.
- Sin fila, `GET /` sigue devolviendo 200 (no se cae).

Agrega en `tests/conftest.py` un fixture `negocio` con datos falsos («Barbería de Prueba», teléfono `3000000000`), y úsalo en el fixture `app` para que todas las pruebas tengan negocio.

**Listo cuando:** pruebas en verde y la web local se ve igual.

---

## Paso 3 — Prueba que detecta marca escrita a mano
**Tiempo:** 1 h · **Commit:** `fase 1.3: prueba anti-marca en código`

Archivo nuevo `tests/test_sin_marca.py`. Recorre `app/templates`, `app/static/js`, `app/public`, `app/models` y `app/utils`, y falla si encuentra alguno de estos textos:
`Barber Brothers`, `barberbrothers`, `la_barberbrothers`, `3143782855`, `314 378 2855`, `3102160496`, `Arkambuco`, `Ibagué`.

- Mientras avanzas, márcala con `@pytest.mark.xfail(strict=False)` y quítale el `xfail` en el paso 9.
- Haz que el mensaje de error liste **archivo y línea** de cada aparición. Esa lista es tu tablero de avance.
- Ignora comentarios y docstrings de Python (`#`, `"""`), y los archivos `.md`: no afectan al cliente final. Esos se limpian aparte en el paso 9.

**Listo cuando:** `pytest tests/test_sin_marca.py -rx` muestra la lista completa de pendientes (hoy, unas 80 apariciones en 35 archivos).

---

## Paso 4 — Plantillas públicas
**Tiempo:** 1 día · **Commit:** uno por bloque (4a, 4b, 4c)

### 4a. `public_base.html` (7 apariciones, la más importante: la heredan todas)
| Línea aprox. | Hoy | Reemplazo |
|---|---|---|
| 63 | `<title>` con «Barber Brothers … Arkambuco» | `{{ negocio.seo_titulo or negocio.nombre }}` |
| 68–70 | meta description y keywords | `negocio.seo_descripcion`, `negocio.seo_palabras_clave` |
| 71, 89 | `author`, `og:site_name` | `negocio.nombre` |
| 75, 101 | geo y localidad | `negocio.ciudad`, `negocio.departamento` |
| 105 | teléfono de contacto | `negocio.telefono` con formato `+57…` |
| 218 | pie: dirección y teléfono | `negocio.direccion`, `negocio.ciudad`, `negocio.telefono` |
| 229 | botón flotante de WhatsApp | `negocio.whatsapp_link()` |

### 4b. `Home.html` (14 apariciones)
- Título, descripción y palabras clave (líneas 12–18): usa los bloques de `public_base` con los campos SEO.
- **JSON-LD (líneas 30–110):** pásalo a `app/templates/public/includes/schema_negocio.html`, armado desde `negocio` con `|tojson`. Ahí se corrigen de una vez el dominio, el teléfono, el Instagram y el horario.
- Textos del slider con «Arkambuco» (141–162): `{{ negocio.ciudad }}`.
- Sección «Nuestra historia» (327–345): `{{ negocio.historia | safe }}`. Si prefieres no usar `safe`, guarda la historia como párrafos separados por línea en blanco y divídelos en la plantilla.

### 4c. Resto de páginas públicas
| Archivo | Apariciones | Qué cambia |
|---|---|---|
| `contacto.html` | 4 | teléfono, correo, Instagram, TikTok |
| `confirmation_status.html` | 5 | títulos, WhatsApp y teléfono |
| `confirmacion_pedido.html` | 3 | título, teléfono, WhatsApp con texto del pedido (`negocio.whatsapp_link('Hola, tengo el pedido ' ~ pedido.numero_pedido)`) |
| `checkout.html` | 2 | título y teléfono (`negocio.telefono_tienda or negocio.telefono`) |
| `servicios.html` | 1 | título |
| `business_optimization_snippets.html` | 2 | «Gracias por confiar en {{ negocio.nombre }}» |

**Verificación a ojo:** recorre en local la portada, servicios, contacto, tienda, checkout y una confirmación de cita. Compara con el sitio en producción y revisa que no cambie nada visible, salvo los datos que unificaste en el paso 0.

---

## Paso 5 — Panel «Configuración del negocio» en el admin
**Tiempo:** 4–5 h · **Commit:** `fase 1.5: el admin edita los datos del negocio`

**Archivos nuevos:** `app/admin/routes/negocio.py`, `app/templates/admin/negocio.html`
**Archivos a tocar:** `app/admin/forms.py` (formulario `NegocioForm`), `app/admin/routes/__init__.py`, menú en `admin_base.html`

- Ruta `GET/POST /admin/negocio`, protegida con `@login_required` y `@admin_required`. La prueba existente `test_all_admin_routes_reject_non_admin` la cubrirá sola.
- Formulario en pestañas: Contacto · Ubicación · Redes · SEO · Historia y horario · Apariencia.
- **No** dejes editar desde aquí: `slug`, `dominio`, `subdominio`, `plan`, `activo`. Esos los manejas tú, no el cliente.
- Valida el WhatsApp (solo dígitos, empieza por 57, 12 dígitos), los colores (`#RRGGBB`) y las URLs de redes.
- Al guardar, limpia la caché del paso 2 para que el cambio se vea de inmediato.

**Pruebas nuevas:** el admin guarda un teléfono nuevo y la portada lo muestra; un WhatsApp inválido no se guarda; un barbero recibe 403.

**Listo cuando:** cambias el teléfono desde el panel y aparece en el pie, el botón de WhatsApp y la página de contacto.

> Valor comercial: este panel es parte del plan Pro. El dueño actualiza sus datos sin escribirte.

---

## Paso 6 — Textos legales (términos, privacidad, cookies)
**Tiempo:** 3–4 h · **Commit:** `fase 1.6: textos legales con datos del negocio`

| Archivo | Apariciones | Reemplazo |
|---|---|---|
| `terminos.html` | 10 | `negocio.razon_social`, `negocio.nit`, `negocio.direccion_legal`, `negocio.telefono`, `negocio.email_contacto`, `negocio.nombre` |
| `privacidad.html` | 11 | ídem, más `negocio.email_datos_personales` como canal para ejercer los derechos de habeas data |
| `cookies.html` | 5 | `negocio.nombre`, `negocio.dominio` |

- Si falta la razón social o el NIT, muestra el nombre comercial y **no** dejes el campo vacío en la frase: usa `{% if negocio.nit %}`.
- Revisa que la política de privacidad nombre al responsable del tratamiento (Ley 1581 de 2012). Para la plantilla multi-tenant, cada barbería es responsable de sus datos y tú eres el **encargado**: deja un párrafo que lo diga. Conviene validarlo con un abogado antes de vender a la segunda barbería.

---

## Paso 7 — Correos y paneles internos
**Tiempo:** 2–3 h · **Commit:** `fase 1.7: correos y paneles con datos del negocio`

| Archivo | Cambio |
|---|---|
| `app/models/email.py` | Asunto: `f"Confirma tu cita en {g.negocio.nombre}"`. Remitente: `(negocio.remitente_nombre or negocio.nombre, MAIL_USERNAME)`. Pasar `negocio` al `render_template`. Ojo: si el correo se envía desde un hilo o tarea fuera de la petición, `g` no existe; pasa el negocio como argumento. |
| `app/config/__init__.py` | `MAIL_DEFAULT_SENDER_NAME` deja de tener «Barber Brothers» como valor por defecto. |
| `email/confirm_appointment.html` y `.txt` | `{{ negocio.nombre }}` (3 + 2 apariciones) |
| `admin/admin_base.html` | título y `alt` del logo |
| `barbero/barbero_base.html`, `barbero/login.html` | título y `alt` del logo |

**Prueba nueva:** con `mail.record_messages()`, una reserva envía un correo cuyo asunto contiene el nombre del negocio de prueba.

---

## Paso 8 — SEO: robots, sitemap, canonical
**Tiempo:** 2–3 h · **Commit:** `fase 1.8: SEO con dominio dinámico`

| Archivo | Hoy | Cambio |
|---|---|---|
| `app/static/robots.txt` | archivo fijo con `barberbrothers.com` | Bórralo y sirve `/robots.txt` desde la ruta que ya existe en `public/routes.py` (`robots_txt`), con `request.host_url`. Revisa en Nginx que no se esté sirviendo el archivo estático por delante de Flask. |
| `app/utils/sitemap_generator.py`, `app/utils/canonical_helper.py` | | Usar `request.host_url` o `negocio.dominio`, nunca un dominio fijo |
| `google17b126f9a1dae6ef.html` y su ruta | verificación de Search Console de Barber Brothers | Mover el código de verificación a un campo `google_verificacion` del negocio. En la fase 2 cada barbería tendrá el suyo. |

**Después de desplegar:** en Google Search Console de Barber Brothers, reenvía el sitemap y usa la herramienta de prueba de resultados enriquecidos sobre la portada para confirmar que el JSON-LD queda válido, con un solo teléfono y la ciudad correcta.

---

## Paso 9 — Apariencia, tienda y limpieza
**Tiempo:** 4–6 h · **Commit:** uno por punto

1. **Colores.** En `public_base.html`, dentro de `<head>`:
   ```html
   <style>:root{--color-primario:{{ negocio.color_primario }};--color-secundario:{{ negocio.color_secundario }};--color-acento:{{ negocio.color_acento }};}</style>
   ```
   En `public_styles.css` (70 KB) busca los colores fijos más repetidos (`grep -o "#[0-9a-fA-F]\{6\}" app/static/css/public_styles.css | sort | uniq -c | sort -rn | head`) y cambia **solo los 3–5 principales** por `var(--color-…)`. No intentes cambiar todo el CSS.
2. **Logo y favicon.** Reemplaza `url_for('static', filename='logo.png')` (en `public_base`, `admin_base`, `barbero_base`, `barbero/login`, JSON-LD y `og:image`) por `negocio.logo_url or url_for('static', filename='logo.png')`.
3. **Interruptor de tienda.** Si `negocio.tienda_activa` es falso:
   - oculta en el menú los enlaces a productos y carrito;
   - las rutas `/productos`, `/checkout`, `/confirmacion-pedido/*` devuelven 404 (un decorador `@requiere_tienda`);
   - no se carga `smart_cart.js`.
   Prueba: con la tienda desactivada, `/productos` da 404 y la portada no muestra el enlace.
4. **JavaScript.** En `public_base.html` agrega `<script>window.NEGOCIO = {{ negocio.datos_publicos()|tojson }};</script>` antes de los scripts. Los 5 archivos JS solo tienen «Barber Brothers» en comentarios de cabecera: cámbialos a una descripción neutra. Revisa con `grep` que ninguno arme mensajes de WhatsApp con el número escrito a mano.
5. **Limpieza:**
   - borra `app/health.py` (no está registrado y su consulta falla en SQLAlchemy 2);
   - cambia los docstrings «… para Barber Brothers» de `app/utils/*.py`, `middleware/business_middleware.py`, `admin/forms.py`, `public/routes.py` por descripciones neutras;
   - quita el `xfail` de `tests/test_sin_marca.py`: debe pasar.

---

## Cierre de la fase

### Lista de verificación
- [ ] `python -m pytest tests -q`: todo en verde, incluida `test_sin_marca.py` sin `xfail`
- [ ] `git grep -n "Barber Brothers"` solo aparece en la migración de datos y en `docs/`
- [ ] Revisión a ojo en local de portada, servicios, contacto, tienda, reserva completa con correo, panel admin, panel barbero, términos y privacidad
- [ ] Prueba de «segunda barbería»: cambia en tu base local el nombre, teléfono y colores del negocio, y comprueba que **todo** el sitio cambia
- [ ] Respaldo de la base de producción antes de migrar
- [ ] Despliegue: `git pull` → `pip install -r requirements.txt` → `flask db upgrade` → reiniciar Gunicorn → agregar `NEGOCIO_SLUG` al `.env` del servidor
- [ ] Search Console: sitemap reenviado y resultados enriquecidos validados
- [ ] Mostrarle a Barber Brothers el nuevo panel «Configuración del negocio»

### Riesgos y cómo evitarlos
| Riesgo | Prevención |
|---|---|
| Se rompe una página por una variable que no existe | El fixture `negocio` en las pruebas y el objeto neutro del paso 2 |
| Cambia el SEO de Barber Brothers sin querer | Copia los textos SEO actuales tal cual a la base; solo corrige lo decidido en el paso 0 |
| `robots.txt` estático tapa la ruta dinámica | Bórralo y revisa la configuración de Nginx |
| La migración falla en producción | Respaldo previo y `flask db upgrade` probado antes en una copia local de la base de producción |
| El correo se envía sin contexto de petición | Pasar el negocio como argumento a la función de envío |

### Qué queda listo para la fase 2
- Todo el sitio depende de `g.negocio`, y la única función que decide **cuál** negocio es `obtener_negocio()`.
- La fase 2 cambia esa función para que lea el dominio y fije el esquema de PostgreSQL, sin tocar plantillas.
