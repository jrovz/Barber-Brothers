# Manual de Funcionamiento de Base de Datos - Barber Brothers

## Tabla de Contenidos
1. [Arquitectura de Base de Datos](#arquitectura-de-base-de-datos)
2. [Modelos de Datos](#modelos-de-datos)
3. [Relaciones entre Entidades](#relaciones-entre-entidades)
4. [Configuración de Conexión](#configuración-de-conexión)
5. [Sistema de Migraciones](#sistema-de-migraciones)
6. [Funcionalidades Específicas](#funcionalidades-específicas)
7. [Mantenimiento y Monitoreo](#mantenimiento-y-monitoreo)

## Arquitectura de Base de Datos

### Tecnologías Utilizadas
- **Base de Datos**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0.20
- **Framework de Migraciones**: Flask-Migrate 4.0.4
- **Driver de Conexión**: psycopg2-binary 2.9.5

### Estructura General
La aplicación utiliza una arquitectura de base de datos relacional con las siguientes características:
- **Normalización**: Estructura normalizada hasta la tercera forma normal
- **Integridad Referencial**: Uso extensivo de claves foráneas
- **Índices**: Optimización en campos de búsqueda frecuente
- **Timestamps**: Campos de auditoría en todas las tablas principales

## Modelos de Datos

### 1. Usuario (User)
**Tabla**: `user`
```sql
CREATE TABLE user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256),
    role VARCHAR(20) DEFAULT 'cliente',
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Funcionalidades**:
- Autenticación con hash de contraseñas (Werkzeug)
- Sistema de roles: `cliente`, `admin`, `barbero`
- Métodos de validación integrados

### 2. Cliente
**Tabla**: `cliente`
```sql
CREATE TABLE cliente (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL,
    telefono VARCHAR(20),
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_visita TIMESTAMP,
    total_visitas INTEGER DEFAULT 0,
    segmento VARCHAR(50) DEFAULT 'nuevo',
    fuente_captacion VARCHAR(50)
);
```

**Sistema de Segmentación Automática**:
- **Nuevo**: Sin visitas previas
- **Ocasional**: 2-4 visitas, última visita < 60 días
- **Recurrente**: 5-9 visitas, última visita < 45 días
- **VIP**: 10+ visitas
- **Inactivo**: Más de 45-60 días sin visita

### 3. Barbero
**Tabla**: `barbero`
```sql
CREATE TABLE barbero (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    especialidad VARCHAR(100),
    descripcion TEXT,
    imagen_url VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Sistema de Disponibilidad**:
- Relación con `DisponibilidadBarbero` para horarios
- Validación automática de conflictos de citas
- Control de estado activo/inactivo

### 4. Servicio
**Tabla**: `servicio`
```sql
CREATE TABLE servicio (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio NUMERIC(10,2) NOT NULL,
    duracion_estimada VARCHAR(50),
    activo BOOLEAN DEFAULT TRUE,
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    imagen_url VARCHAR(255)
);
```

### 5. Cita
**Tabla**: `cita`
```sql
CREATE TABLE cita (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES cliente(id),
    barbero_id INTEGER REFERENCES barbero(id),
    servicio_id INTEGER REFERENCES servicio(id),
    fecha TIMESTAMP NOT NULL,
    estado VARCHAR(30) DEFAULT 'pendiente_confirmacion',
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duracion INTEGER DEFAULT 30,
    notas TEXT,
    confirmed_at TIMESTAMP
);
```

**Estados de Cita**:
- `pendiente_confirmacion`: Recién creada, esperando confirmación del cliente
- `confirmada`: Cliente confirmó la cita
- `completada`: Servicio realizado
- `cancelada`: Cancelada por cliente o barbero
- `expirada`: No confirmada a tiempo

### 6. Producto
**Tabla**: `productos`
```sql
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio FLOAT NOT NULL,
    categoria_id INTEGER REFERENCES categorias(id),
    cantidad INTEGER DEFAULT 0,
    imagen_url VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 7. Categoría
**Tabla**: `categorias`
```sql
CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8. Mensaje
**Tabla**: `mensaje`
```sql
CREATE TABLE mensaje (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES cliente(id),
    asunto VARCHAR(150),
    mensaje TEXT NOT NULL,
    leido BOOLEAN DEFAULT FALSE,
    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Relaciones entre Entidades

### Diagrama de Relaciones
```
User (1) ←→ (0..n) Cliente [via email]
Cliente (1) ←→ (0..n) Cita
Cliente (1) ←→ (0..n) Mensaje
Barbero (1) ←→ (0..n) Cita
Servicio (1) ←→ (0..n) Cita
Categoria (1) ←→ (0..n) Producto
Barbero (1) ←→ (0..n) DisponibilidadBarbero
```

### Integridad Referencial
- **Cascadas**: Configuradas en relaciones críticas
- **Restricciones**: Previenen eliminación de datos referenciados
- **Índices**: En todas las claves foráneas para optimización

## Configuración de Conexión

### Entornos de Configuración

#### Desarrollo Local
```python
# app/config/__init__.py
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///app.db'
```

#### Producción
```python
class ProductionConfig(Config):
    DEBUG = False
    # Configuración automática para GCP Cloud SQL
    if os.environ.get("GAE_ENV") == "standard":
        # Usa Cloud SQL Connector
        from app.utils.cloud_connection_pg import init_connection_engine
        engine = init_connection_engine()
    else:
        # Usa DATABASE_URL estándar
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
```

### Pool de Conexiones
```python
# app/utils/local_connection_pg.py
engine = create_engine(
    db_url,
    poolclass=QueuePool,
    pool_size=5,           # Conexiones permanentes
    max_overflow=2,        # Conexiones adicionales
    pool_timeout=30,       # Timeout para obtener conexión
    pool_recycle=1800,     # Reciclar conexiones cada 30 min
)
```

## Sistema de Migraciones

### Gestión de Migraciones con Alembic

#### Comandos Principales
```bash
# Crear nueva migración
flask db migrate -m "Descripción del cambio"

# Aplicar migraciones
flask db upgrade

# Revertir migración
flask db downgrade

# Ver historial
flask db history

# Ver migración actual
flask db current
```

#### Estructura de Migraciones
```
migrations/
├── alembic.ini          # Configuración de Alembic
├── env.py              # Configuración del entorno
├── script.py.mako      # Plantilla para nuevas migraciones
└── versions/           # Archivos de migración
    ├── 35d9b8e11970_crear_tablas_iniciales.py
    ├── 38cfef5f337c_crear_tabla_productos.py
    ├── a894756db028_add_servicio_model.py
    └── ...
```

### Proceso de Inicialización de BD
```python
# app/utils/db_init_handler.py
def init_database_if_needed():
    """Verifica y inicializa la base de datos"""
    try:
        # Verificar conexión
        db.session.execute(text("SELECT 1"))
        current_app.logger.info("Conexión a la base de datos exitosa.")
        
        # Aplicar migraciones pendientes automáticamente
        # (En producción, esto se hace en el entrypoint de Docker)
        
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error de conexión: {str(e)}")
```

## Funcionalidades Específicas

### 1. Sistema de Confirmación de Citas
```python
# Generación de token de confirmación
def generate_confirmation_token(self):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps({'cita_id': self.id})

# Verificación del token
def verify_confirmation_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, max_age=expiration)
        return Cita.query.get(data['cita_id'])
    except:
        return None
```

### 2. Segmentación Automática de Clientes
```python
def clasificar_segmento(self):
    """Clasifica al cliente según su patrón de visitas"""
    today = datetime.utcnow()
    
    if not self.ultima_visita:
        self.segmento = 'nuevo'
        return self.segmento
        
    dias_desde_ultima = (today - self.ultima_visita).days
    
    if self.total_visitas >= 10:
        self.segmento = 'vip'
    elif self.total_visitas >= 5:
        if dias_desde_ultima <= 45:
            self.segmento = 'recurrente'
        else:
            self.segmento = 'inactivo'
    # ... más lógica de segmentación
```

### 3. Validación de Disponibilidad
```python
def esta_disponible(self, fecha_propuesta):
    """Verifica disponibilidad del barbero"""
    solo_fecha = fecha_propuesta.date()
    solo_hora = fecha_propuesta.time()
    dia_semana = solo_fecha.weekday()
    
    # Verificar día laborable
    if dia_semana > 5:  # domingo
        return False
        
    # Verificar horarios de trabajo
    for disp in self.disponibilidad.filter_by(
        dia_semana=dia_semana, activo=True).all():
        if disp.hora_inicio <= solo_hora < disp.hora_fin:
            # Verificar conflictos de citas
            cita_existente = Cita.query.filter_by(
                barbero_id=self.id,
                fecha=fecha_propuesta,
                estado='confirmada'
            ).first()
            return cita_existente is None
    return False
```

### 4. Sistema de Notificaciones por Email
```python
def send_appointment_confirmation_email(cliente_email, cliente_nombre, cita, token):
    confirm_url = url_for('public.confirmar_cita_route', token=token, _external=True)
    subject = "Confirma tu cita en Barber Brothers"
    
    send_email(
        subject=subject,
        recipients=[cliente_email],
        text_body=render_template('email/confirm_appointment.txt',
                                  cliente_nombre=cliente_nombre,
                                  cita=cita,
                                  confirm_url=confirm_url),
        html_body=render_template('email/confirm_appointment.html',
                                  cliente_nombre=cliente_nombre,
                                  cita=cita,
                                  confirm_url=confirm_url)
    )
```

## Mantenimiento y Monitoreo

### 1. Logging de Base de Datos
```python
# Configuración de logging para SQLAlchemy
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 2. Monitoreo de Performance
- **Pool de Conexiones**: Monitorear uso del pool
- **Queries Lentas**: Log de queries > 1 segundo
- **Deadlocks**: Detección y logging de deadlocks

### 3. Backup y Recuperación
```bash
# Backup completo
pg_dump -h localhost -U postgres barberia_db > backup_$(date +%Y%m%d).sql

# Backup solo datos
pg_dump -h localhost -U postgres --data-only barberia_db > data_backup.sql

# Restauración
psql -h localhost -U postgres barberia_db < backup.sql
```

### 4. Optimización de Consultas
```python
# Ejemplos de consultas optimizadas
# Usar eager loading para evitar N+1 queries
citas = Cita.query.options(
    joinedload(Cita.cliente),
                joinedload(Cita.barbero),
    joinedload(Cita.servicio_rel)
).filter(Cita.fecha >= datetime.now()).all()

# Usar índices en consultas frecuentes
Cliente.query.filter(Cliente.email == email).first()  # email tiene índice
```

### 5. Limpieza de Datos
```python
# Script para limpiar citas expiradas
def cleanup_expired_appointments():
    """Limpia citas no confirmadas después de 24 horas"""
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    expired_citas = Cita.query.filter(
        Cita.estado == 'pendiente_confirmacion',
        Cita.creado < cutoff_time
    ).all()
    
    for cita in expired_citas:
        cita.estado = 'expirada'
    
    db.session.commit()
```

## Consideraciones de Seguridad

### 1. Sanitización de Datos
- **SQLAlchemy ORM**: Protección automática contra SQL injection
- **Validación de Entrada**: Uso de Flask-WTF para validación
- **Escapado**: Automático en templates Jinja2

### 2. Manejo de Contraseñas
```python
def set_password(self, password):
    self.password_hash = generate_password_hash(password)

def check_password(self, password):
    return check_password_hash(self.password_hash, password)
```

### 3. Tokens de Confirmación
- **Expiración**: Tokens con tiempo límite
- **Firma Criptográfica**: Uso de itsdangerous
- **Una sola vez**: Tokens invalidados después del uso

## Conclusión

El sistema de base de datos de Barber Brothers está diseñado para:
- **Escalabilidad**: Manejo eficiente de crecimiento
- **Confiabilidad**: Integridad de datos garantizada
- **Mantenibilidad**: Código limpio y bien documentado
- **Performance**: Optimizaciones en consultas críticas
- **Seguridad**: Protección contra vulnerabilidades comunes

Este manual debe ser consultado para cualquier modificación o mantenimiento del sistema de base de datos.
