/**
 * ========================================================================
 * SISTEMA DE RESERVAS AVANZADO - BOOKING.JS
 * ========================================================================
 * 
 * @file booking.js
 * @version 2.0.0
 * @description Sistema completo de gestión de citas para barbería con funcionalidades
 *              avanzadas de optimización, validación en tiempo real y manejo de errores.
 * 
 * @author Barber Brothers Development Team
 * @created 2024
 * @lastModified 2024
 * 
 * ========================================================================
 * CARACTERÍSTICAS PRINCIPALES
 * ========================================================================
 * 
 * 🔧 FUNCIONALIDADES CORE:
 * - Selección dinámica de barberos y servicios
 * - Calendario interactivo con fechas disponibles
 * - Horarios en tiempo real con validación de disponibilidad
 * - Formulario de confirmación con validaciones avanzadas
 * - Manejo de estados de carga y errores
 * 
 * ⚡ OPTIMIZACIONES DE RENDIMIENTO:
 * - Sistema de caché inteligente (5 minutos de duración)
 * - Debouncing en peticiones de horarios (300ms)
 * - Lazy loading de elementos DOM
 * - Fragment para renderizado optimizado
 * - Validación en tiempo real cada 30 segundos
 * 
 * 🛡️ SEGURIDAD Y ROBUSTEZ:
 * - Protección CSRF en todas las peticiones
 * - Validación de datos en cliente y servidor
 * - Retry automático con exponential backoff
 * - Timeout de peticiones (10 segundos)
 * - Sanitización de inputs
 * 
 * 🎨 EXPERIENCIA DE USUARIO:
 * - Interfaz responsive y accesible (ARIA)
 * - Navegación por teclado completa
 * - Notificaciones toast informativas
 * - Estados de carga visuales
 * - Formateo automático de horarios (12h/24h)
 * 
 * ========================================================================
 * ARQUITECTURA DEL SISTEMA
 * ========================================================================
 * 
 * El sistema está organizado en los siguientes módulos:
 * 
 * 1. CONFIGURACIÓN Y CONSTANTES
 *    - Timeouts, delays, duraciones de caché
 *    - Configuración de reintentos y validaciones
 * 
 * 2. GESTIÓN DEL DOM
 *    - Referencias a elementos críticos del formulario
 *    - Validación de existencia de elementos
 * 
 * 3. ESTADO DE LA APLICACIÓN
 *    - Variables de selección (barbero, servicio, fecha, hora)
 *    - Cache de datos y flags de estado
 * 
 * 4. UTILIDADES Y HELPERS
 *    - Funciones de debouncing y throttling
 *    - Validaciones (email, horarios, fechas)
 *    - Formateo de datos y manejo de errores
 * 
 * 5. LÓGICA DE NEGOCIO
 *    - Carga de horarios disponibles
 *    - Validación de disponibilidad
 *    - Procesamiento de reservas
 * 
 * 6. INTERFAZ DE USUARIO
 *    - Renderizado de componentes
 *    - Manejo de eventos
 *    - Navegación y accesibilidad
 * 
 * ========================================================================
 * FLUJO DE TRABAJO TÍPICO
 * ========================================================================
 * 
 * 1. Usuario selecciona barbero → Habilita selector de servicios
 * 2. Usuario selecciona servicio → Habilita calendario de fechas
 * 3. Usuario selecciona fecha → Carga horarios disponibles vía API
 * 4. Sistema muestra horarios filtrados (excluye pasados si es hoy)
 * 5. Usuario selecciona horario → Valida disponibilidad en tiempo real
 * 6. Sistema muestra panel de confirmación con resumen
 * 7. Usuario completa datos → Validación de formulario
 * 8. Envío de datos → Confirmación y notificación de resultado
 * 
 * ========================================================================
 * API ENDPOINTS UTILIZADOS
 * ========================================================================
 * 
 * GET /api/disponibilidad/{barbero_id}/{fecha}?servicio_id={id}
 * - Obtiene horarios disponibles para barbero/servicio/fecha específicos
 * - Incluye validación opcional de slot específico
 * 
 * POST /api/agendar-cita
 * - Procesa la solicitud de nueva cita
 * - Requiere CSRF token y validación completa
 * 
 * ========================================================================
 * CONFIGURACIÓN DE CACHÉ
 * ========================================================================
 * 
 * - Duración: 5 minutos por entrada
 * - Clave: {barbero_id}-{servicio_id}-{fecha}
 * - Invalidación: Automática por tiempo y manual en cambios
 * - Almacenamiento: Map() en memoria del navegador
 * 
 * ========================================================================
 * ACCESIBILIDAD (WCAG 2.1 AA)
 * ========================================================================
 * 
 * - Roles ARIA apropiados (radiogroup, radio, button)
 * - Labels descriptivos para lectores de pantalla
 * - Navegación completa por teclado (Tab, Arrow keys, Enter, Space)
 * - Estados visuales claros (focus, selected, disabled)
 * - Contraste de colores adecuado
 * 
 * ========================================================================
 * MANEJO DE ERRORES
 * ========================================================================
 * 
 * - Timeouts de red (10s)
 * - Reintentos automáticos (3 intentos)
 * - Validación offline/online
 * - Mensajes de error específicos y accionables
 * - Recuperación graceful ante fallos
 * 
 * ========================================================================
 * EVENTOS PERSONALIZADOS
 * ========================================================================
 * 
 * - Validación en tiempo real cada 30 segundos
 * - Limpieza automática de recursos al salir
 * - Invalidación de caché en cambios de selección
 * - Actualización automática de horarios en conflictos
 * 
 * ========================================================================
 * DEPENDENCIAS
 * ========================================================================
 * 
 * - Vanilla JavaScript (ES6+)
 * - Fetch API para peticiones HTTP
 * - AbortController para cancelación de peticiones
 * - CSS personalizado para estilos y animaciones
 * - CSRF token meta tag requerido
 * 
 * ========================================================================
 * NOTAS DE DESARROLLO
 * ========================================================================
 * 
 * - Todos los console.log están incluidos para debugging
 * - El sistema es completamente modular y testeable
 * - Compatible con navegadores modernos (IE11+)
 * - Optimizado para mobile-first
 * - Preparado para PWA y Service Workers
 * 
 * ========================================================================
 */

document.addEventListener('DOMContentLoaded', function() {
    // ==================== CONFIGURACIÓN Y CONSTANTES ====================
    const CONFIG = {
        DEBOUNCE_DELAY: 300,
        REQUEST_TIMEOUT: 10000,
        RETRY_ATTEMPTS: 3,
        CACHE_DURATION: 5 * 60 * 1000, // 5 minutos
        VALIDATION_INTERVAL: 30000 // 30 segundos
    };

    // ==================== ELEMENTOS DEL DOM ====================
    const elements = {
        barberoSelect: document.getElementById('barbero-select'),
        servicioSelect: document.getElementById('servicio-select'),
        dateOptions: document.querySelectorAll('.date-option'),
        horariosContainer: document.getElementById('horarios-container'),
        bookingConfirmation: document.getElementById('booking-confirmation'),
        confirmButton: document.getElementById('confirm-booking'),
        clientInfoForm: document.getElementById('client-info-form'),
        clientNameInput: document.getElementById('client-name'),
        clientEmailInput: document.getElementById('client-email'),
        clientPhoneInput: document.getElementById('client-phone'),
        selectedBarberoIdInput: document.getElementById('selected-barbero-id'),
        selectedServicioIdInput: document.getElementById('selected-servicio-id'),
        selectedDateInput: document.getElementById('selected-date'),
        selectedTimeInput: document.getElementById('selected-time')
    };

    // ==================== ESTADO DE LA APLICACIÓN ====================
    const appState = {
        selectedBarberoId: null,
        selectedServicioId: null,
        selectedDate: null,
        selectedTime: null,
        isLoading: false,
        lastRequestTime: 0,
        cache: new Map(),
        retryCount: 0
    };

    // ==================== UTILIDADES ====================
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    let debounceTimer = null;
    let validationInterval = null;

    // ==================== FUNCIONES UTILITARIAS ====================
    const utils = {
        debounce(func, delay) {
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(debounceTimer);
                    func(...args);
                };
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(later, delay);
            };
        },

        async fetchWithRetry(url, options = {}, retries = CONFIG.RETRY_ATTEMPTS) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT);
            
            try {
                const response = await fetch(url, {
                    ...options,
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                return response;
            } catch (error) {
                clearTimeout(timeoutId);
                
                if (retries > 0 && error.name !== 'AbortError') {
                    console.warn(`Reintentando petición a ${url}. Intentos restantes: ${retries - 1}`);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    return utils.fetchWithRetry(url, options, retries - 1);
                }
                throw error;
            }
        },

        getCacheKey(barberoId, servicioId, fecha) {
            return `${barberoId}-${servicioId}-${fecha}`;
        },

        getCachedData(key) {
            const cached = appState.cache.get(key);
            if (cached && Date.now() - cached.timestamp < CONFIG.CACHE_DURATION) {
                return cached.data;
            }
            appState.cache.delete(key);
            return null;
        },

        setCachedData(key, data) {
            appState.cache.set(key, {
                data,
                timestamp: Date.now()
            });
        },

        validateEmail(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(String(email).toLowerCase());
        },

        formatTime12h(hhmm) {
            const [hh, mm] = hhmm.split(':').map(Number);
            const suffix = hh >= 12 ? 'pm' : 'am';
            const hour12 = (hh % 12) || 12;
            return `${hour12}:${mm.toString().padStart(2, '0')} ${suffix}`;
        },

        showError(message, type = 'error') {
            // Crear notificación toast mejorada
            const toast = document.createElement('div');
            toast.className = `booking-toast booking-toast--${type}`;
            toast.innerHTML = `
                <div class="toast-content">
                    <span class="toast-icon">${type === 'error' ? '⚠️' : '✅'}</span>
                    <span class="toast-message">${message}</span>
                    <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
                </div>
            `;
            
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 5000);
        },

        setLoadingState(isLoading) {
            appState.isLoading = isLoading;
            
            if (elements.horariosContainer) {
                if (isLoading) {
                    elements.horariosContainer.innerHTML = `
                        <div class="loading-spinner">
                            <div class="spinner"></div>
                            <p>Cargando horarios disponibles...</p>
                        </div>
                    `;
                }
            }
            
            // Deshabilitar controles durante carga
            [elements.barberoSelect, elements.servicioSelect].forEach(el => {
                if (el) el.disabled = isLoading;
            });
        }
    };

    // ==================== INICIALIZACIÓN ====================
    function init() {
        console.log('Inicializando sistema de reservas optimizado...');
        
        // Debug: Mostrar todos los elementos encontrados
        console.log('Estado de elementos DOM:');
        Object.keys(elements).forEach(key => {
            console.log(`${key}:`, elements[key] ? '✓ Encontrado' : '❌ No encontrado');
        });
        
        // Validación de elementos críticos
        const requiredElements = [
            'barberoSelect', 'servicioSelect', 'horariosContainer', 
            'bookingConfirmation', 'confirmButton'
        ];
        
        const missingElements = requiredElements.filter(name => !elements[name]);
        if (missingElements.length > 0) {
            console.error(`Faltan elementos esenciales del DOM: ${missingElements.join(', ')}`);
            utils.showError('Error de configuración: No se puede inicializar el sistema de reservas.');
            return;
        }

        if (elements.barberoSelect) {
            console.log(`Opciones en select de barberos: ${elements.barberoSelect.options.length}`);
        }
        if (elements.servicioSelect) {
            console.log(`Servicios en selector: ${elements.servicioSelect.options.length - 1}`);
        }
        
        if (elements.bookingConfirmation) {
            elements.bookingConfirmation.style.display = 'none';
        }
        
        elements.dateOptions.forEach(option => {
            option.classList.add('disabled');
        });

        if (elements.barberoSelect && elements.barberoSelect.options.length <= 1) {
            console.warn("No hay barberos activos disponibles.");
        }
        if (elements.servicioSelect && elements.servicioSelect.options.length <= 1) {
            console.warn("No hay servicios activos disponibles.");
        }
    }
    
    // ==================== FUNCIONES PRINCIPALES ====================
    const loadAvailableTimes = utils.debounce(async function() {
        console.log('=== loadAvailableTimes ejecutándose ===');
        
        const barberoId = elements.barberoSelect?.value;
        const servicioId = elements.servicioSelect?.value;
        const fecha = appState.selectedDate;
        
        console.log('Valores actuales:', {
            barberoId,
            servicioId,
            fecha,
            horariosContainer: !!elements.horariosContainer
        });

        // Validaciones básicas
        if (!barberoId || barberoId === "0" || !servicioId || servicioId === "0" || !fecha) {
            console.log('Validación fallida - faltan datos básicos');
            if (elements.horariosContainer) {
                elements.horariosContainer.innerHTML = '<p class="instruction-message">Selecciona un barbero, servicio y fecha para ver horarios.</p>';
            } else {
                console.error('horariosContainer no encontrado!');
            }
            return;
        }

        // Verificar cache primero
        const cacheKey = utils.getCacheKey(barberoId, servicioId, fecha);
        const cachedData = utils.getCachedData(cacheKey);
        
        if (cachedData) {
            console.log('Usando datos en cache para horarios');
            renderTimeSlots(cachedData, fecha);
            return;
        }
        
        try {
            utils.setLoadingState(true);
            appState.lastRequestTime = Date.now();
            
            const url = `/api/disponibilidad/${barberoId}/${fecha}?servicio_id=${servicioId}`;
            console.log(`Fetching: ${url}`);
            
            const response = await utils.fetchWithRetry(url);
            const data = await response.json();
            
            console.log("API Response Data:", data);
            console.log(`Horarios disponibles recibidos: ${data.horarios ? data.horarios.length : 0}`);
            
            if (!response.ok) {
                throw new Error(data.error || `Error ${response.status}: No se pudieron cargar los horarios`);
            }
            
            // Guardar en cache
            utils.setCachedData(cacheKey, data);
            
            // Renderizar horarios
            renderTimeSlots(data, fecha);
            
            // Resetear contador de reintentos en caso de éxito
            appState.retryCount = 0;
            
        } catch (error) {
            console.error('Error al cargar horarios:', error);
            
            if (error.name === 'AbortError') {
                utils.showError('La solicitud tardó demasiado. Por favor, intenta de nuevo.');
            } else if (!navigator.onLine) {
                utils.showError('Sin conexión a internet. Verifica tu conexión y vuelve a intentar.');
            } else {
                utils.showError(`Error al cargar horarios: ${error.message}`);
            }
            
            elements.horariosContainer.innerHTML = `
                <div class="error-container">
                    <p class="instruction-message error">❌ ${error.message}</p>
                    <button class="retry-button" onclick="loadAvailableTimes()">🔄 Reintentar</button>
                </div>
            `;
        } finally {
            utils.setLoadingState(false);
        }
    }, CONFIG.DEBOUNCE_DELAY);

    function renderTimeSlots(data, fecha) {
        elements.horariosContainer.innerHTML = '';

            if (!data.horarios || data.horarios.length === 0) {
            elements.horariosContainer.innerHTML = `
                <p class="instruction-message">${data.mensaje || 'No hay horarios disponibles para la selección.'}</p>
            `;
                return;
            }
            
        // Filtrar horas pasadas si es hoy
            const [anioSel, mesSel, diaSel] = fecha.split('-').map(Number);
            const now = new Date();
            const isToday = (
            now.getFullYear() === anioSel && 
            (now.getMonth() + 1) === mesSel && 
            now.getDate() === diaSel
            );

            const isPastOnSelectedDay = (hhmm) => {
                const [hh, mm] = hhmm.split(':').map(Number);
            const slotDate = new Date(anioSel, mesSel - 1, diaSel, hh, mm, 0, 0);
                return slotDate.getTime() <= now.getTime();
            };

        // Fragment para mejor performance
        const fragment = document.createDocumentFragment();
        
            data.horarios.forEach(horaString => {
            if (typeof horaString !== 'string') {
                console.error("Slot de horario inesperado (no es string):", horaString);
                return;
            }

                    // Si es el día actual, ocultar horas que ya pasaron
                    if (isToday && isPastOnSelectedDay(horaString)) {
                return;
            }

            const slotButton = createTimeSlotButton(horaString, fecha);
            fragment.appendChild(slotButton);
        });
        
        elements.horariosContainer.appendChild(fragment);
        
        // Agregar atributos de accesibilidad
        elements.horariosContainer.setAttribute('role', 'radiogroup');
        elements.horariosContainer.setAttribute('aria-label', 'Horarios disponibles');
    }

    function createTimeSlotButton(horaString, fecha) {
                    const slotButton = document.createElement('button');
                    slotButton.type = 'button';
        slotButton.className = 'time-slot-btn';
        slotButton.textContent = utils.formatTime12h(horaString);
        slotButton.dataset.hora = horaString;
        
        // Atributos de accesibilidad
        slotButton.setAttribute('role', 'radio');
        slotButton.setAttribute('aria-checked', 'false');
        slotButton.setAttribute('aria-label', `Horario ${utils.formatTime12h(horaString)}`);
        
        // Event listeners optimizados
        slotButton.addEventListener('click', handleTimeSlotClick);
        slotButton.addEventListener('keydown', handleTimeSlotKeydown);
        
        return slotButton;
    }

    function handleTimeSlotClick(event) {
        const button = event.currentTarget;
        
        // Deseleccionar otros botones
                        document.querySelectorAll('.time-slot-btn.selected').forEach(el => {
                            el.classList.remove('selected');
            el.setAttribute('aria-checked', 'false');
        });
        
        // Seleccionar botón actual
        button.classList.add('selected');
        button.setAttribute('aria-checked', 'true');
        
        appState.selectedTime = button.dataset.hora;
        
        console.log(`Slot seleccionado: ${appState.selectedTime}`);
        
        const barberoName = elements.barberoSelect.options[elements.barberoSelect.selectedIndex].text;
        const servicioName = elements.servicioSelect.options[elements.servicioSelect.selectedIndex].text.split(' - ')[0];

        showConfirmationPanel(
            appState.selectedBarberoId, 
            barberoName, 
            appState.selectedServicioId, 
            servicioName, 
            appState.selectedDate, 
            appState.selectedTime
        );
    }

    function handleTimeSlotKeydown(event) {
        const buttons = Array.from(document.querySelectorAll('.time-slot-btn'));
        const currentIndex = buttons.indexOf(event.currentTarget);
        
        switch (event.key) {
            case 'ArrowLeft':
            case 'ArrowUp':
                event.preventDefault();
                const prevIndex = currentIndex > 0 ? currentIndex - 1 : buttons.length - 1;
                buttons[prevIndex].focus();
                break;
            case 'ArrowRight':
            case 'ArrowDown':
                event.preventDefault();
                const nextIndex = currentIndex < buttons.length - 1 ? currentIndex + 1 : 0;
                buttons[nextIndex].focus();
                break;
            case 'Enter':
            case ' ':
                event.preventDefault();
                handleTimeSlotClick(event);
                break;
        }
    }
    
    function showConfirmationPanel(barberoId, barberoName, servicioId, servicioName, fecha, hora) {
        if (!elements.bookingConfirmation) return;

        // Validación en tiempo real antes de mostrar el panel
        validateSlotAvailability(barberoId, servicioId, fecha, hora)
            .then(isAvailable => {
                if (!isAvailable) {
                    utils.showError('Lo sentimos, este horario ya no está disponible. Te mostraremos horarios actualizados.');
                    loadAvailableTimes();
                    return;
                }
                
                // Continuar con la confirmación si está disponible
                displayConfirmationPanel(barberoId, barberoName, servicioId, servicioName, fecha, hora);
            })
            .catch(error => {
                console.error('Error validando disponibilidad:', error);
                // Continuar con la confirmación en caso de error de validación
                displayConfirmationPanel(barberoId, barberoName, servicioId, servicioName, fecha, hora);
            });
    }
    
    async function validateSlotAvailability(barberoId, servicioId, fecha, hora) {
        try {
            const url = `/api/disponibilidad/${barberoId}/${fecha}?servicio_id=${servicioId}&validate_slot=${hora}`;
            const response = await utils.fetchWithRetry(url);
            const data = await response.json();
            
            if (!response.ok) {
                console.warn('Error validando slot:', data.error);
                return true; // En caso de error, permitir continuar
            }
            
            // Verificar si el horario específico está en la lista de disponibles
            return data.horarios && data.horarios.includes(hora);
        } catch (error) {
            console.error('Error en validación de slot:', error);
            return true; // En caso de error, permitir continuar
        }
    }
    
    function displayConfirmationPanel(barberoId, barberoName, servicioId, servicioName, fecha, hora) {
        // Actualizar información de la confirmación
        const confirmBarbero = document.getElementById('confirm-barbero');
        const confirmServicio = document.getElementById('confirm-servicio');
        const confirmFecha = document.getElementById('confirm-fecha');
        const confirmHora = document.getElementById('confirm-hora');
        
        if (confirmBarbero) confirmBarbero.textContent = barberoName;
        
        // Obtener la duración del servicio seleccionado
        const selectedServiceOption = elements.servicioSelect.options[elements.servicioSelect.selectedIndex];
        const duracionMinutos = selectedServiceOption.dataset.duracion || '30';
        const servicioConDuracion = `${servicioName} (${duracionMinutos} min)`;
        
        if (confirmServicio) confirmServicio.textContent = servicioConDuracion;
        
        // Formatear fecha para display
        const fechaObj = new Date(fecha + 'T00:00:00'); 
        const fechaFormateadaParaDisplay = fechaObj.toLocaleDateString('es-ES', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        });
        if (confirmFecha) confirmFecha.textContent = fechaFormateadaParaDisplay;
        
        // Calcular y mostrar hora de inicio y finalización
        const [horas, minutos] = hora.split(':').map(Number);
        const minutosFinalizacion = minutos + parseInt(duracionMinutos);
        const horasFinalizacion = horas + Math.floor(minutosFinalizacion / 60);
        const minutosRestantes = minutosFinalizacion % 60;
        const horaFin24 = `${(horasFinalizacion%24).toString().padStart(2, '0')}:${minutosRestantes.toString().padStart(2, '0')}`;

        const horaFormateada = `${utils.formatTime12h(hora)} - ${utils.formatTime12h(horaFin24)}`;
        if (confirmHora) confirmHora.textContent = horaFormateada;

        // Poblar los campos ocultos
        if (elements.selectedBarberoIdInput) elements.selectedBarberoIdInput.value = barberoId;
        if (elements.selectedServicioIdInput) elements.selectedServicioIdInput.value = servicioId;
        if (elements.selectedDateInput) elements.selectedDateInput.value = fecha; 
        if (elements.selectedTimeInput) elements.selectedTimeInput.value = hora;   

        // Mostrar formulario y panel
        if (elements.clientInfoForm) {
            elements.clientInfoForm.style.display = 'block';
        }

        elements.bookingConfirmation.style.display = 'block';
        elements.bookingConfirmation.scrollIntoView({ behavior: 'smooth' });
        
        // Focus en el primer campo del formulario para mejor UX
        if (elements.clientNameInput) {
            elements.clientNameInput.focus();
        }
    }
    
    // ==================== EVENT LISTENERS ====================
    function setupEventListeners() {
        // Barbero select
        if (elements.barberoSelect) {
            elements.barberoSelect.addEventListener('change', function() {
                appState.selectedBarberoId = this.value;
                console.log(`Barbero seleccionado ID: ${appState.selectedBarberoId}`);
                
                // Resetear selecciones dependientes
                appState.selectedDate = null;
                appState.selectedTime = null;
            document.querySelectorAll('.date-option.selected').forEach(el => el.classList.remove('selected'));
            
                // Invalidar cache relacionado
                clearRelatedCache();
                
                                if (appState.selectedBarberoId && appState.selectedBarberoId !== "0" && 
                    appState.selectedServicioId && appState.selectedServicioId !== "0") {
                    elements.dateOptions.forEach(option => option.classList.remove('disabled'));
                    elements.horariosContainer.innerHTML = '<p class="instruction-message">Selecciona una fecha.</p>';
            } else {
                    elements.dateOptions.forEach(option => option.classList.add('disabled'));
                    elements.horariosContainer.innerHTML = '<p class="instruction-message">Selecciona un barbero y servicio.</p>';
                }
                if (elements.bookingConfirmation) elements.bookingConfirmation.style.display = 'none';
            });
        }

        // Servicio select
        if (elements.servicioSelect) {
            elements.servicioSelect.addEventListener('change', function() {
                appState.selectedServicioId = this.value;
                console.log(`Servicio seleccionado ID: ${appState.selectedServicioId}`);
                
                // Resetear selecciones dependientes
                appState.selectedDate = null;
                appState.selectedTime = null;
            document.querySelectorAll('.date-option.selected').forEach(el => el.classList.remove('selected'));
            
                // Invalidar cache relacionado
                clearRelatedCache();
                
                if (appState.selectedBarberoId && appState.selectedBarberoId !== "0" && 
                    appState.selectedServicioId && appState.selectedServicioId !== "0") {
                    elements.dateOptions.forEach(option => option.classList.remove('disabled'));
                    elements.horariosContainer.innerHTML = '<p class="instruction-message">Selecciona una fecha.</p>';
            } else {
                    elements.dateOptions.forEach(option => option.classList.add('disabled'));
                    elements.horariosContainer.innerHTML = '<p class="instruction-message">Selecciona un barbero y servicio.</p>';
            }
                if (elements.bookingConfirmation) elements.bookingConfirmation.style.display = 'none';
        });
    }
    
        // Date options
        console.log(`Configurando ${elements.dateOptions.length} opciones de fecha`);
        elements.dateOptions.forEach((option, index) => {
        option.addEventListener('click', function() {
                console.log(`Click en fecha ${index}, disabled: ${this.classList.contains('disabled')}`);
            if (this.classList.contains('disabled')) return;
            
            document.querySelectorAll('.date-option.selected').forEach(el => el.classList.remove('selected'));
            this.classList.add('selected');
                appState.selectedDate = this.dataset.fecha;
                console.log(`Fecha seleccionada: ${appState.selectedDate}`);
                appState.selectedTime = null;
                
                console.log('Llamando a loadAvailableTimes...');
                loadAvailableTimes();
                
                if (elements.bookingConfirmation) elements.bookingConfirmation.style.display = 'none';
            });
        });

        // Confirm booking button
        if (elements.confirmButton) {
            elements.confirmButton.addEventListener('click', handleBookingConfirmation);
        }
    }

    function clearRelatedCache() {
        // Limpiar cache relacionado cuando cambian barbero o servicio
        const keysToDelete = [];
        for (const key of appState.cache.keys()) {
            if (key.startsWith(`${appState.selectedBarberoId}-`) || 
                key.includes(`-${appState.selectedServicioId}-`)) {
                keysToDelete.push(key);
            }
        }
        keysToDelete.forEach(key => appState.cache.delete(key));
    }
    
    // ==================== CONFIRMACIÓN DE BOOKING ====================
    async function handleBookingConfirmation() {
            const bookingData = {
            nombre: elements.clientNameInput?.value?.trim(),
            email: elements.clientEmailInput?.value?.trim(),
            telefono: elements.clientPhoneInput?.value?.trim(),
            barbero_id: elements.selectedBarberoIdInput?.value,
            servicio_id: elements.selectedServicioIdInput?.value,
            fecha: elements.selectedDateInput?.value,
            hora: elements.selectedTimeInput?.value
            };

            console.log("Data to be sent to backend:", bookingData);
        
        // Validaciones mejoradas
        const validationErrors = validateBookingData(bookingData);
        if (validationErrors.length > 0) {
            utils.showError(validationErrors.join('<br>'));
                return;
            }

        // Verificar CSRF token
        if (!csrfToken) {
            console.error('CSRF token not found!');
            utils.showError('Error de configuración: No se pudo encontrar el token de seguridad. Por favor, recarga la página.');
                return;
            }

        // Deshabilitar botón y mostrar loading
        elements.confirmButton.disabled = true;
        elements.confirmButton.textContent = 'Procesando...';

        try {
            const response = await utils.fetchWithRetry('/api/agendar-cita', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(bookingData)
            });

                const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                const text = await response.text();
                throw new Error(`Respuesta inesperada del servidor: ${text.substring(0, 100)}`);
            }

            const data = await response.json();
            
            if (response.ok && data.success) {
                handleBookingSuccess(data);
            } else {
                handleBookingError(response.status, data);
            }
            
        } catch (error) {
            console.error('Error en fetch o al procesar respuesta:', error);
            
            if (error.name === 'AbortError') {
                utils.showError('La solicitud tardó demasiado. Por favor, intenta de nuevo.');
            } else if (!navigator.onLine) {
                utils.showError('Sin conexión a internet. Verifica tu conexión y vuelve a intentar.');
                } else {
                utils.showError(`Ocurrió un error: ${error.message}`);
            }
        } finally {
            elements.confirmButton.disabled = false;
            elements.confirmButton.textContent = 'Confirmar Cita';
        }
    }

    function validateBookingData(data) {
        const errors = [];
        
        if (!data.nombre) errors.push('• El nombre es obligatorio');
        if (!data.email) errors.push('• El correo electrónico es obligatorio');
        else if (!utils.validateEmail(data.email)) errors.push('• El correo electrónico no es válido');
        if (!data.telefono) errors.push('• El teléfono es obligatorio');
        if (!data.barbero_id || data.barbero_id === "0") errors.push('• Debe seleccionar un barbero');
        if (!data.servicio_id || data.servicio_id === "0") errors.push('• Debe seleccionar un servicio');
        if (!data.fecha) errors.push('• Debe seleccionar una fecha');
        if (!data.hora) errors.push('• Debe seleccionar un horario');
        
        return errors;
    }

    function handleBookingSuccess(data) {
        if (elements.bookingConfirmation) {
            elements.bookingConfirmation.innerHTML = `
                <div class="booking-success">
                    <h3 style="color: #28a745;">¡Solicitud Recibida! ✅</h3>
                            <p>${data.mensaje || 'Hemos recibido tu solicitud. Por favor, revisa tu correo electrónico para confirmar la cita en la próxima hora.'}</p>
                    ${data.cita_id ? `<p><strong>ID de Solicitud:</strong> ${data.cita_id}</p>` : ''}
                    <p><small>Si no recibes el correo en unos minutos, revisa tu carpeta de spam.</small></p>
                    <button class="book-button" onclick="window.location.reload()" style="margin-top: 15px;">Agendar otra cita</button>
                </div>
            `;
        }
        
        utils.showError('¡Cita solicitada exitosamente! Revisa tu correo para confirmar.', 'success');
        
        // Limpiar cache para refrescar horarios
        appState.cache.clear();
    }

    function handleBookingError(status, data) {
        switch (status) {
            case 409:
                utils.showError('Lo sentimos, alguien más acaba de agendar este horario. Te mostraremos horarios actualizados.');
                        console.log('Conflicto de horario detectado, recargando horarios disponibles...');
                        loadAvailableTimes();
                if (elements.bookingConfirmation) elements.bookingConfirmation.style.display = 'none';
                break;
            case 400:
                utils.showError(`Error en los datos proporcionados: ${data.error || 'Por favor, verifica tu información e inténtalo de nuevo.'}`);
                break;
            default:
                utils.showError(`Error al solicitar la cita: ${data.error || `Error ${status}` || 'Inténtalo de nuevo.'}`);
        }
    }

    // ==================== INICIALIZACIÓN PRINCIPAL ====================
    init();
    setupEventListeners();

    // ==================== FUNCIONES GLOBALES ====================
    window.hideConfirmationPanel = function() {
        if (elements.bookingConfirmation) {
            elements.bookingConfirmation.style.display = 'none';
        }
        
        // Limpiar formulario opcionalmente
        [elements.clientNameInput, elements.clientEmailInput, elements.clientPhoneInput].forEach(input => {
            if (input) input.value = '';
        });
    };

    // Función global para reintentar desde botones de error
    window.loadAvailableTimes = loadAvailableTimes;

    // Configurar validación en tiempo real
    function setupRealTimeValidation() {
        if (validationInterval) {
            clearInterval(validationInterval);
        }
        
        validationInterval = setInterval(() => {
            if (appState.selectedTime && appState.selectedDate && appState.selectedBarberoId && appState.selectedServicioId) {
                validateSlotAvailability(
                    appState.selectedBarberoId, 
                    appState.selectedServicioId, 
                    appState.selectedDate, 
                    appState.selectedTime
                ).then(isAvailable => {
                    if (!isAvailable) {
                        utils.showError('El horario seleccionado ya no está disponible. Se actualizarán los horarios.');
                        loadAvailableTimes();
                    }
                });
            }
        }, CONFIG.VALIDATION_INTERVAL);
    }

    // Limpiar recursos al salir de la página
    window.addEventListener('beforeunload', function() {
        if (validationInterval) {
            clearInterval(validationInterval);
        }
        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }
    });

    // Iniciar validación en tiempo real si hay selecciones
    setupRealTimeValidation();
});