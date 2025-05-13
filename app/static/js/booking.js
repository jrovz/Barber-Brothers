document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const barberoSelect = document.getElementById('barbero-select');
    const servicioSelect = document.getElementById('servicio-select');
    const dateOptions = document.querySelectorAll('.date-option');
    const horariosContainer = document.getElementById('horarios-container');
    const bookingConfirmation = document.getElementById('booking-confirmation'); // Panel completo de confirmación
    const confirmButton = document.getElementById('confirm-booking');
    const clientInfoForm = document.getElementById('client-info-form');
    const clientNameInput = document.getElementById('client-name');
    const clientEmailInput = document.getElementById('client-email');
    const clientPhoneInput = document.getElementById('client-phone');

    // Inputs ocultos para enviar al backend
    const selectedBarberoIdInput = document.getElementById('selected-barbero-id');
    const selectedServicioIdInput = document.getElementById('selected-servicio-id');
    const selectedDateInput = document.getElementById('selected-date');
    const selectedTimeInput = document.getElementById('selected-time');
    
    // Variables para almacenar la selección actual
    let currentSelectedBarberoId = null;
    let currentSelectedServicioId = null;
    // let selectedServicioDuracion = 30; // Si necesitas la duración en el frontend
    let currentSelectedDate = null;
    let currentSelectedTime = null;
    
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

    function init() {
        console.log('Inicializando sistema de reservas...');
        if (!barberoSelect || !servicioSelect || !horariosContainer || !bookingConfirmation || !confirmButton) {
            console.error("Faltan elementos esenciales del DOM para el sistema de reservas.");
            // Podrías deshabilitar la funcionalidad o mostrar un mensaje al usuario.
            return;
        }

        if (barberoSelect) {
            console.log(`Opciones en select de barberos: ${barberoSelect.options.length}`);
        }
        if (servicioSelect) {
            console.log(`Servicios en selector: ${servicioSelect.options.length - 1}`);
        }
        
        if (bookingConfirmation) {
            bookingConfirmation.style.display = 'none';
        }
        
        dateOptions.forEach(option => {
            option.classList.add('disabled');
        });

        if (barberoSelect && barberoSelect.options.length <= 1) {
            console.warn("No hay barberos activos disponibles.");
        }
        if (servicioSelect && servicioSelect.options.length <= 1) {
            console.warn("No hay servicios activos disponibles.");
        }
    }
    
    async function loadAvailableTimes() {
        // Usar los valores actuales de los selects para la petición
        const barberoId = barberoSelect.value;
        const servicioId = servicioSelect.value;
        const fecha = currentSelectedDate; // Esta se actualiza al hacer clic en una fecha

        if (!barberoId || barberoId === "0" || !servicioId || servicioId === "0" || !fecha) {
            horariosContainer.innerHTML = '<p class="instruction-message">Selecciona un barbero, servicio y fecha para ver horarios.</p>';
            return;
        }
        
        try {
            horariosContainer.innerHTML = '<p class="loading-message">Cargando horarios...</p>';
            
            console.log(`Fetching: /api/disponibilidad/${barberoId}/${fecha}?servicio_id=${servicioId}`);
            const response = await fetch(`/api/disponibilidad/${barberoId}/${fecha}?servicio_id=${servicioId}`);
            const data = await response.json();
            console.log("API Response Data:", data);
            
            if (!response.ok) {
                throw new Error(data.error || `Error ${response.status}: No se pudieron cargar los horarios`);
            }
            
            horariosContainer.innerHTML = ''; // Limpiar antes de añadir nuevos

            if (!data.horarios || data.horarios.length === 0) {
                horariosContainer.innerHTML = `<p class="instruction-message">${data.mensaje || 'No hay horarios disponibles para la selección.'}</p>`;
                return;
            }
            
            // Renderizar horarios: data.horarios es un array de strings de hora (ej: ["09:00", "09:30"])
            data.horarios.forEach(horaString => {
                if (typeof horaString === 'string') {
                    const slotButton = document.createElement('button');
                    slotButton.type = 'button';
                    slotButton.classList.add('time-slot-btn'); // Clase para estilizar
                    slotButton.textContent = horaString;      // El string de hora es el contenido
                    slotButton.dataset.hora = horaString;     // Guardar la hora en data attribute

                    slotButton.addEventListener('click', function() {
                        document.querySelectorAll('.time-slot-btn.selected').forEach(el => {
                            el.classList.remove('selected');
                        });
                        this.classList.add('selected');
                        currentSelectedTime = this.dataset.hora;
                        
                        const barberoName = barberoSelect.options[barberoSelect.selectedIndex].text;
                        const servicioName = servicioSelect.options[servicioSelect.selectedIndex].text.split(' - ')[0];

                        showConfirmationPanel(barberoId, barberoName, servicioId, servicioName, fecha, currentSelectedTime);
                    });
                    horariosContainer.appendChild(slotButton);
                } else {
                    console.error("Slot de horario inesperado (no es string):", horaString);
                }
            });
            
        } catch (error) {
            console.error('Error al cargar horarios:', error);
            horariosContainer.innerHTML = `<p class="instruction-message error">Error: ${error.message}</p>`;
        }
    }
    
    function showConfirmationPanel(barberoId, barberoName, servicioId, servicioName, fecha, hora) {
        if (!bookingConfirmation) return;

        document.getElementById('confirm-barbero').textContent = barberoName;
        document.getElementById('confirm-servicio').textContent = servicioName;
        
        const fechaObj = new Date(fecha + 'T00:00:00'); 
        const fechaFormateadaParaDisplay = fechaObj.toLocaleDateString('es-ES', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        });
        document.getElementById('confirm-fecha').textContent = fechaFormateadaParaDisplay;
        document.getElementById('confirm-hora').textContent = hora;

        // Poblar los campos ocultos que se enviarán con el formulario de confirmación
        if (selectedBarberoIdInput) selectedBarberoIdInput.value = barberoId;
        if (selectedServicioIdInput) selectedServicioIdInput.value = servicioId;
        if (selectedDateInput) selectedDateInput.value = fecha; 
        if (selectedTimeInput) selectedTimeInput.value = hora;   

        if (clientInfoForm) {
            clientInfoForm.style.display = 'block';
        }

        bookingConfirmation.style.display = 'block';
        bookingConfirmation.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Event Listeners
    if (barberoSelect) {
        barberoSelect.addEventListener('change', function() {
            currentSelectedBarberoId = this.value; // Actualiza la variable global
            console.log(`Barbero seleccionado ID: ${currentSelectedBarberoId}`);
            
            currentSelectedDate = null; // Resetear fecha
            currentSelectedTime = null; // Resetear hora
            document.querySelectorAll('.date-option.selected').forEach(el => el.classList.remove('selected'));
            
            if (currentSelectedBarberoId && currentSelectedBarberoId !== "0" && currentSelectedServicioId && currentSelectedServicioId !== "0") {
                dateOptions.forEach(option => option.classList.remove('disabled'));
                // No llamamos a loadAvailableTimes aquí, esperamos a que se seleccione una fecha
                horariosContainer.innerHTML = '<p class="instruction-message">Selecciona una fecha.</p>';
            } else {
                dateOptions.forEach(option => option.classList.add('disabled'));
                horariosContainer.innerHTML = '<p class="instruction-message">Selecciona un barbero y servicio.</p>';
            }
            if (bookingConfirmation) bookingConfirmation.style.display = 'none';
        });
    }
    
    if (servicioSelect) {
        servicioSelect.addEventListener('change', function() {
            currentSelectedServicioId = this.value; // Actualiza la variable global
            // const selectedOption = this.options[this.selectedIndex];
            // selectedServicioDuracion = parseInt(selectedOption.dataset.duracion || '30', 10);
            console.log(`Servicio seleccionado ID: ${currentSelectedServicioId}`);
            
            currentSelectedDate = null; // Resetear fecha
            currentSelectedTime = null; // Resetear hora
            document.querySelectorAll('.date-option.selected').forEach(el => el.classList.remove('selected'));
            
            if (currentSelectedBarberoId && currentSelectedBarberoId !== "0" && currentSelectedServicioId && currentSelectedServicioId !== "0") {
                dateOptions.forEach(option => option.classList.remove('disabled'));
                horariosContainer.innerHTML = '<p class="instruction-message">Selecciona una fecha.</p>';
            } else {
                dateOptions.forEach(option => option.classList.add('disabled'));
                horariosContainer.innerHTML = '<p class="instruction-message">Selecciona un barbero y servicio.</p>';
            }
            if (bookingConfirmation) bookingConfirmation.style.display = 'none';
        });
    }
    
    dateOptions.forEach(option => {
        option.addEventListener('click', function() {
            if (this.classList.contains('disabled')) return;
            
            document.querySelectorAll('.date-option.selected').forEach(el => el.classList.remove('selected'));
            this.classList.add('selected');
            currentSelectedDate = this.dataset.fecha; // Actualiza la variable global
            console.log(`Fecha seleccionada: ${currentSelectedDate}`);
            currentSelectedTime = null; 
            
            loadAvailableTimes(); // Ahora sí cargamos horarios
            
            if (bookingConfirmation) bookingConfirmation.style.display = 'none';
        });
    });
    
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(String(email).toLowerCase());
    }
    
    init();

    if (confirmButton) {
        confirmButton.addEventListener('click', function() {
            const bookingData = {
                nombre: clientNameInput.value.trim(),
                email: clientEmailInput.value.trim(),
                telefono: clientPhoneInput.value.trim(),
                barbero_id: selectedBarberoIdInput.value,
                servicio_id: selectedServicioIdInput.value,
                fecha: selectedDateInput.value,
                hora: selectedTimeInput.value
            };

            console.log("Data to be sent to backend:", bookingData);
            if (!csrfToken) {
                console.error('CSRF token not found!');
                alert('Error de configuración: No se pudo encontrar el token de seguridad. Por favor, recarga la página.');
                return;
            }

            if (!bookingData.nombre || !bookingData.email || !bookingData.telefono) {
                alert('Por favor, completa tu nombre, correo electrónico y teléfono.');
                return;
            }
            if (!validateEmail(bookingData.email)) {
                alert('Por favor, ingresa un correo electrónico válido.');
                return;
            }
            if (!bookingData.barbero_id || bookingData.barbero_id === "0" ||
                !bookingData.servicio_id || bookingData.servicio_id === "0" ||
                !bookingData.fecha || !bookingData.hora) {
                alert('Error: Faltan detalles de la cita (barbero, servicio, fecha u hora). Por favor, selecciona de nuevo.');
                console.error("Frontend validation failed. Missing booking details:", bookingData);
                return;
            }

            confirmButton.disabled = true;
            confirmButton.textContent = 'Procesando...';

            fetch('/api/agendar-cita', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(bookingData)
            })
            .then(response => {
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.indexOf("application/json") !== -1) {
                    return response.json().then(data => ({ ok: response.ok, status: response.status, data }));
                } else {
                    return response.text().then(text => {
                        throw new Error(`Respuesta inesperada del servidor (no es JSON): ${text.substring(0, 100)}`);
                    });
                }
            })
            .then(result => {
                const { ok, status, data } = result;
                if (ok && data.success) {
                    if (bookingConfirmation) {
                        // Actualizar el panel de confirmación para informar sobre el correo
                        bookingConfirmation.innerHTML = `
                            <h3 style="color: #28a745;">¡Solicitud Recibida!</h3>
                            <p>${data.mensaje || 'Hemos recibido tu solicitud. Por favor, revisa tu correo electrónico para confirmar la cita en la próxima hora.'}</p>
                            ${data.cita_id ? `<p>ID de Solicitud: ${data.cita_id}</p>` : ''}
                            <p>Si no recibes el correo en unos minutos, revisa tu carpeta de spam.</p>
                            <button class="book-button" onclick="window.location.href='${window.location.pathname}'" style="margin-top: 15px;">Agendar otra cita</button>
                        `;
                        // No ocultar clientInfoForm aquí, ya que el panel se reconstruye
                    }
                } else {
                    // Manejo de error existente
                    alert(`Error al solicitar la cita: ${data.error || `Error ${status}` || 'Inténtalo de nuevo.'}`);
                    confirmButton.disabled = false;
                    confirmButton.textContent = 'Confirmar Cita';
                }
            })
            .catch(error => {
                console.error('Error en fetch o al procesar respuesta:', error);
                alert(`Ocurrió un error: ${error.message}`);
                confirmButton.disabled = false;
                confirmButton.textContent = 'Confirmar Cita';
            });
        });
    }

    // Eliminar el listener genérico para #horarios-container que estaba al final,
    // ya que los listeners se añaden dinámicamente a los botones de hora en loadAvailableTimes.

    window.hideConfirmationPanel = function() {
        if (bookingConfirmation) {
            bookingConfirmation.style.display = 'none';
        }
        // No es necesario resetear el formulario de cliente aquí si el panel de confirmación
        // se reconstruye o si la página se recarga para una nueva cita.
        // Si quieres limpiar los campos explícitamente:
        // if (clientNameInput) clientNameInput.value = '';
        // if (clientEmailInput) clientEmailInput.value = '';
        // if (clientPhoneInput) clientPhoneInput.value = '';
    }
});