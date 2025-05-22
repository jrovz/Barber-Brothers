# Barber Brothers

## Descripción

Barber Brothers es una aplicación web completa para la gestión integral de una barbería con estética lujosa vintage. El sistema proporciona tanto una interfaz pública elegante para los clientes como un completo panel de administración para los propietarios del negocio.

## Vista Previa

![Página de inicio](website.png)

## Características Principales

### Para Clientes
- **Diseño Elegante**: Interfaz de usuario sofisticada con estética luxury y vintage
- **Reserva de Citas**: Sistema completo para agendar citas con fecha, hora, barbero y servicio
- **Catálogo de Productos**: Visualización de productos organizados por categorías
- **Carrito de Compras**: Funcionalidad para añadir productos y gestionar compras
- **Formulario de Contacto**: Permite a los clientes enviar mensajes directos a la barbería
- **Diseño Responsive**: Experiencia optimizada para todo tipo de dispositivos

### Para Administradores
- **Dashboard**: Panel con métricas clave del negocio
- **Gestión de Barberos**: CRUD completo con control de disponibilidad por día y horario
- **Gestión de Servicios**: Administración de servicios ofrecidos con precios y tiempos
- **Gestión de Productos**: Control de inventario con categorización
- **Gestión de Citas**: Sistema para administrar, confirmar y dar seguimiento a las citas
- **Segmentación de Clientes**: Clasificación automática en VIP, recurrentes, ocasionales, etc.
- **Mensajería**: Centro de mensajes enviados por los clientes

## Características Avanzadas

### Segmentación Inteligente de Clientes
El sistema clasifica automáticamente a los clientes según su comportamiento:
- **Nuevos**: Primera interacción con el negocio
- **Ocasionales**: Entre 2-4 visitas con frecuencia variable
- **Recurrentes**: 5+ visitas con frecuencia regular
- **VIP**: 10+ visitas, clientes con alta fidelidad
- **Inactivos**: Clientes sin visitas recientes (60+ días)

Esta segmentación permite implementar estrategias de fidelización y marketing personalizadas.

### Sistema de Citas
- Confirmación mediante correo electrónico (token seguro)
- Control de disponibilidad personalizada por barbero
- Control inteligente de duración según el servicio seleccionado
- Detección y prevención de conflictos de horarios

### Notificaciones por Email
- Confirmación de citas con datos completos
- Enlaces de confirmación con tokens seguros y caducidad
- Plantillas HTML personalizadas

### Logging y Monitoreo
- Integración con Google Cloud Logging en entorno de producción
- Logging local configurable en desarrollo
- Captura automática de errores y eventos importantes

## Instalación y Configuración

### Requisitos Previos
- Python 3.11+
- PostgreSQL 13+
- Pip y Virtualenv

### Configuración Local

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/barber-brothers.git
cd barber-brothers
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En macOS/Linux
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements/dev.txt
```

4. Configurar variables de entorno:
```bash
# Windows
set FLASK_APP=wsgi.py
set FLASK_ENV=development
# Linux/macOS
export FLASK_APP=wsgi.py
export FLASK_ENV=development
```

5. Crear la base de datos PostgreSQL y configurar credenciales en el archivo de configuración.

6. Ejecutar migraciones:
```bash
flask db upgrade
```

7. Cargar datos iniciales (opcional):
```bash
python init_data.py
```

8. Iniciar el servidor:
```bash
flask run
```

### Despliegue en GCP

El proyecto está optimizado para despliegue en Google Cloud Platform. Consulte la guía completa en `docs/gcp_deployment_guide.md`.

## Estructura del Proyecto

```
├── app/                    # Aplicación principal
│   ├── admin/              # Módulo de administración
│   ├── api/                # Endpoints de API
│   ├── config/             # Configuraciones
│   ├── models/             # Modelos de datos
│   ├── public/             # Rutas públicas
│   ├── static/             # Recursos estáticos
│   ├── templates/          # Plantillas HTML
│   └── utils/              # Utilidades y herramientas
├── docs/                   # Documentación adicional
├── migrations/             # Migraciones de la base de datos
└── requirements/           # Dependencias del proyecto
```

## Contribución

Las contribuciones son bienvenidas. Por favor, sigue estos pasos para contribuir:

1. Fork el repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Realiza tus cambios y haz commit (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un nuevo Pull Request

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).


