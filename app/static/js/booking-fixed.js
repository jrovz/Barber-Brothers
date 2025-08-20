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
            console.log(`${type.toUpperCase()}: ${message}`);
            // Fallback simple si no hay toast system
            if (type === 'error') {
                alert(message);
            }
        },

        setLoadingState(isLoading) {
            appState.isLoading = isLoading;
            
            if (elements.horariosContainer) {
                if (isLoading) {
                    elements.horariosContainer.innerHTML = `
                        <div class="loading-message">
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
        console.log('Inicializando sistema de reservas...');
        
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
            
            const url = `/api/disponibilidad/${barberoId}/${fecha}?servicio_id=${servicioId}`;
            console.log(`Fetching: ${url}`);
            
            const response = await utils.fetchWithRetry(url);
            const data = await response.json();
            
            console.log("API Response Data:", data);
            
            if (!response.ok) {
                throw new Error(data.error || `Error ${response.status}: No se pudieron cargar los horarios`);
            }
            
            // Guardar en cache
            utils.setCachedData(cacheKey, data);
            
            // Renderizar horarios
            renderTimeSlots(data, fecha);
            
        } catch (error) {
            console.error('Error al cargar horarios:', error);
            utils.showError(`Error al cargar horarios: ${error.message}`);
            
            elements.horariosContainer.innerHTML = `
                <div class="error-container">
                    <p class="instruction-message error">❌ ${error.message}</p>
                    <button class="retry-button" onclick="window.loadAvailableTimes()">🔄 Reintentar</button>
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

            const slotButton = createTimeSlotButton(horaString);
            fragment.appendChild(slotButton);
        });
        
        elements.horariosContainer.appendChild(fragment);
    }

    function createTimeSlotButton(horaString) {
        const slotButton = document.createElement('button');
        slotButton.type = 'button';
        slotButton.className = 'time-slot-btn';
        slotButton.textContent = utils.formatTime12h(horaString);
        slotButton.dataset.hora = horaString;
        
        slotButton.addEventListener('click', function() {
            // Deseleccionar otros botones
            document.querySelectorAll('.time-slot-btn.selected').forEach(el => {
                el.classList.remove('selected');
            });
            
            // Seleccionar botón actual
            this.classList.add('selected');
            appState.selectedTime = this.dataset.hora;
            
            console.log(`Slot seleccionado: ${appState.selectedTime}`);
            
            // Mostrar panel de confirmación
            if (elements.bookingConfirmation) {
                elements.bookingConfirmation.style.display = 'block';
                elements.bookingConfirmation.scrollIntoView({ behavior: 'smooth' });
            }
        });
        
        return slotButton;
    }

    // ==================== EVENT LISTENERS ====================
    function setupEventListeners() {
        console.log('Configurando event listeners...');
        
        // Barbero select
        if (elements.barberoSelect) {
            elements.barberoSelect.addEventListener('change', function() {
                appState.selectedBarberoId = this.value;
                console.log(`Barbero seleccionado ID: ${appState.selectedBarberoId}`);
                
                // Resetear selecciones dependientes
                appState.selectedDate = null;
                appState.selectedTime = null;
                document.querySelectorAll('.date-option.selected').forEach(el => el.classList.remove('selected'));
                
                updateDateOptionsState();
                hideBookingConfirmation();
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
                
                updateDateOptionsState();
                hideBookingConfirmation();
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
                
                hideBookingConfirmation();
            });
        });
    }

    function updateDateOptionsState() {
        if (appState.selectedBarberoId && appState.selectedBarberoId !== "0" && 
            appState.selectedServicioId && appState.selectedServicioId !== "0") {
            elements.dateOptions.forEach(option => option.classList.remove('disabled'));
            elements.horariosContainer.innerHTML = '<p class="instruction-message">Selecciona una fecha.</p>';
        } else {
            elements.dateOptions.forEach(option => option.classList.add('disabled'));
            elements.horariosContainer.innerHTML = '<p class="instruction-message">Selecciona un barbero y servicio.</p>';
        }
    }

    function hideBookingConfirmation() {
        if (elements.bookingConfirmation) {
            elements.bookingConfirmation.style.display = 'none';
        }
    }

    // ==================== FUNCIONES GLOBALES ====================
    window.hideConfirmationPanel = hideBookingConfirmation;
    window.loadAvailableTimes = loadAvailableTimes;

    // ==================== INICIALIZACIÓN PRINCIPAL ====================
    init();
    setupEventListeners();

    console.log('Sistema de reservas inicializado correctamente');
});
