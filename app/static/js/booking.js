document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const barberoSelect = document.getElementById('barbero-select');
    const servicioSelect = document.getElementById('servicio-select');
    const dateOptions = document.querySelectorAll('.date-option');
    const horariosContainer = document.getElementById('horarios-container');
    const bookingConfirmation = document.getElementById('booking-confirmation');
    const confirmButton = document.getElementById('confirm-booking');
    const clientInfoForm = document.getElementById('client-info-form'); // Get the client form div
    const clientNameInput = document.getElementById('client-name');
    const clientEmailInput = document.getElementById('client-email');
    const clientPhoneInput = document.getElementById('client-phone');
    const selectedBarberoIdInput = document.getElementById('selected-barbero-id');
    const selectedServicioIdInput = document.getElementById('selected-servicio-id');
    const selectedDateInput = document.getElementById('selected-date');
    const selectedTimeInput = document.getElementById('selected-time');
    const bookingConfirmationPanel = document.getElementById('booking-confirmation');
    
    // Variables para almacenar la selección
    let selectedBarbero = null;
    let selectedServicio = null;
    let selectedServicioDuracion = 30; // Duración por defecto
    let selectedDate = null;
    let selectedTime = null;
    
    // Inicializar estado
    function init() {
        // Mostrar mensaje de depuración
        console.log('Inicializando sistema de reservas...');
        console.log('Barbero select:', barberoSelect);
        console.log('Servicio select:', servicioSelect);
        
        if (barberoSelect) {
            console.log(`Opciones en select de barberos: ${barberoSelect.options.length}`);
            for (let i = 0; i < barberoSelect.options.length; i++) {
                console.log(`- Opción ${i}: ${barberoSelect.options[i].text} (valor: ${barberoSelect.options[i].value})`);
            }
        } else {
            console.error('No se encontró el elemento select de barberos!');
        }
        
        console.log(`Barberos en selector: ${barberoSelect.options.length - 1}`);
        console.log(`Servicios en selector: ${servicioSelect.options.length - 1}`);
        
        // Ocultar confirmación inicialmente
        if (bookingConfirmation) {
            bookingConfirmation.style.display = 'none';
        }
        
        // Desactivar selector de fechas hasta que se seleccione barbero y servicio
        dateOptions.forEach(option => {
            option.classList.add('disabled');
        });

        // Mensaje inicial si no hay barberos o servicios
        if (barberoSelect && barberoSelect.options.length <= 1) {
            // Podrías mostrar un mensaje en la UI
            console.warn("No hay barberos activos disponibles.");
        }
        if (servicioSelect && servicioSelect.options.length <= 1) {
            // Podrías mostrar un mensaje en la UI
            console.warn("No hay servicios activos disponibles.");
        }
    }
    
    // Cargar horarios disponibles
    async function loadAvailableTimes() {
        if (!selectedBarbero || !selectedServicio || !selectedDate) {
            horariosContainer.innerHTML = '<p class="instruction-message">Selecciona un barbero, servicio y fecha para ver horarios.</p>';
            return;
        }
        
        try {
            horariosContainer.innerHTML = '<p class="instruction-message">Cargando horarios...</p>';
            
            const response = await fetch(`/api/disponibilidad/${selectedBarbero}/${selectedDate}?servicio_id=${selectedServicio}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'No se pudieron cargar los horarios');
            }
            
            if (!data.horarios || data.horarios.length === 0) {
                horariosContainer.innerHTML = `<p class="instruction-message">${data.mensaje || 'No hay horarios disponibles para la selección.'}</p>`;
                return;
            }
            
            // Renderizar horarios
            horariosContainer.innerHTML = data.horarios.map(slot => {
                const className = slot.disponible ? 'time-slot available' : 'time-slot booked';
                return `<div class="${className}" data-hora="${slot.hora}">${slot.hora}</div>`;
            }).join('');
            
            // Añadir event listeners a slots disponibles
            document.querySelectorAll('.time-slot.available').forEach(slot => {
                slot.addEventListener('click', function() {
                    // Quitar selección anterior
                    document.querySelectorAll('.time-slot.selected').forEach(el => {
                        el.classList.remove('selected');
                    });
                    
                    // Añadir selección actual
                    this.classList.add('selected');
                    selectedTime = this.dataset.hora;
                    
                    // Mostrar confirmación
                    showConfirmation();
                });
            });
            
        } catch (error) {
            console.error('Error al cargar horarios:', error);
            horariosContainer.innerHTML = `<p class="instruction-message error">Error: ${error.message}</p>`;
        }
    }
    
    // Mostrar panel de confirmación
    function showConfirmation() {
        if (!bookingConfirmation) return;
        
        // Verificar que tenemos toda la información necesaria
        if (!selectedBarbero || !selectedServicio || !selectedDate || !selectedTime) {
            return;
        }
        
        // Obtener nombres para mostrar
        const barberoNombre = barberoSelect.options[barberoSelect.selectedIndex].text;
        const servicioNombre = servicioSelect.options[servicioSelect.selectedIndex].text;
        
        // Formatear fecha para mostrar
        const fechaObj = new Date(selectedDate + 'T00:00:00');
        const fechaFormateada = fechaObj.toLocaleDateString('es-ES', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        // Actualizar texto de confirmación
        document.getElementById('confirm-barbero').textContent = barberoNombre;
        document.getElementById('confirm-servicio').textContent = servicioNombre;
        document.getElementById('confirm-fecha').textContent = fechaFormateada;
        document.getElementById('confirm-hora').textContent = selectedTime;
        
        // Mostrar panel y formulario de cliente
        bookingConfirmation.style.display = 'block';
        if (clientInfoForm) {
            clientInfoForm.style.display = 'block'; // Make sure client form is visible
        }
        
        // Scroll hacia el panel de confirmación
        bookingConfirmation.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Event Listeners
    
    // Cambio de barbero
    if (barberoSelect) {
        barberoSelect.addEventListener('change', function() {
            selectedBarbero = this.value;
            console.log(`Barbero seleccionado: ${selectedBarbero}`);
            
            // Resetear fecha y hora si cambia el barbero
            selectedDate = null;
            selectedTime = null;
            
            document.querySelectorAll('.date-option.selected').forEach(el => {
                el.classList.remove('selected');
            });
            
            // Activar selector de fechas si tenemos barbero y servicio
            if (selectedBarbero && selectedServicio) {
                dateOptions.forEach(option => {
                    option.classList.remove('disabled');
                });
                loadAvailableTimes(); // Recargar horarios si ya hay fecha seleccionada
            } else {
                dateOptions.forEach(option => option.classList.add('disabled'));
                horariosContainer.innerHTML = '<p class="instruction-message">Selecciona un servicio y fecha.</p>';
            }
            
            // Ocultar confirmación
            if (bookingConfirmation) {
                bookingConfirmation.style.display = 'none';
            }
        });
    } else {
        console.error("Listener no añadido: barberoSelect no encontrado.");
    }
    
    // Cambio de servicio
    if (servicioSelect) {
        servicioSelect.addEventListener('change', function() {
            selectedServicio = this.value;
            const selectedOption = this.options[this.selectedIndex];
            selectedServicioDuracion = parseInt(selectedOption.dataset.duracion || '30', 10); // Obtener duración
            console.log(`Servicio seleccionado: ${selectedServicio}, Duración: ${selectedServicioDuracion} min`);
            
            // Resetear fecha y hora si cambia el servicio
            selectedDate = null;
            selectedTime = null;
            
            document.querySelectorAll('.date-option.selected').forEach(el => {
                el.classList.remove('selected');
            });
            
            // Activar selector de fechas si tenemos barbero y servicio
            if (selectedBarbero && selectedServicio) {
                dateOptions.forEach(option => {
                    option.classList.remove('disabled');
                });
                loadAvailableTimes(); // Recargar horarios si ya hay fecha seleccionada
            } else {
                dateOptions.forEach(option => option.classList.add('disabled'));
                horariosContainer.innerHTML = '<p class="instruction-message">Selecciona un barbero y fecha.</p>';
            }
            
            // Ocultar confirmación
            if (bookingConfirmation) {
                bookingConfirmation.style.display = 'none';
            }
        });
    } else {
        console.error("Listener no añadido: servicioSelect no encontrado.");
    }
    
    // Selección de fecha
    dateOptions.forEach(option => {
        option.addEventListener('click', function() {
            if (this.classList.contains('disabled')) return;
            
            // Quitar selección anterior
            document.querySelectorAll('.date-option.selected').forEach(el => {
                el.classList.remove('selected');
            });
            
            // Añadir selección actual
            this.classList.add('selected');
            selectedDate = this.dataset.fecha;
            console.log(`Fecha seleccionada: ${selectedDate}`);
            selectedTime = null; // Resetear hora al cambiar fecha
            
            // Cargar horarios disponibles
            loadAvailableTimes();
            
            // Ocultar confirmación
            if (bookingConfirmation) {
                bookingConfirmation.style.display = 'none';
            }
        });
    });
    
    // Confirmación de cita
    if (confirmButton) {
        confirmButton.addEventListener('click', async function() {
            // Validar campos del cliente
            const clientNameInput = document.getElementById('client-name');
            const clientEmailInput = document.getElementById('client-email');
            const clientPhoneInput = document.getElementById('client-phone');

            const clientName = clientNameInput ? clientNameInput.value.trim() : '';
            const clientEmail = clientEmailInput ? clientEmailInput.value.trim() : '';
            const clientPhone = clientPhoneInput ? clientPhoneInput.value.trim() : '';
            
            if (!clientName || !clientEmail || !clientPhone) {
                alert('Por favor, completa todos tus datos (Nombre, Correo, Teléfono).');
                return;
            }
            
            // Validar email
            if (!validateEmail(clientEmail)) {
                alert('Por favor, ingresa un correo electrónico válido.');
                return;
            }
            
            // Validar que todos los datos de la cita estén seleccionados
            if (!selectedBarbero || !selectedServicio || !selectedDate || !selectedTime) {
                alert('Error: Faltan datos de la cita. Por favor, selecciona barbero, servicio, fecha y hora.');
                return;
            }

            try {
                // Deshabilitar botón mientras se procesa
                confirmButton.disabled = true;
                confirmButton.textContent = 'Procesando...';
                
                // Enviar datos al servidor (NUEVO ENDPOINT)
                const response = await fetch('/api/agendar-cita', { // Endpoint para agendar
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        // Si usas CSRF con fetch, necesitarás incluir el token
                        // 'X-CSRFToken': '{{ csrf_token() }}' // Esto no funciona directamente en JS, necesitarías obtenerlo de otra forma
                    },
                    body: JSON.stringify({
                        barbero_id: selectedBarbero,
                        servicio_id: selectedServicio,
                        fecha: selectedDate, // Formato YYYY-MM-DD
                        hora: selectedTime,   // Formato HH:MM
                        nombre_cliente: clientName, // Cambiado para claridad
                        email_cliente: clientEmail,   // Cambiado para claridad
                        telefono_cliente: clientPhone // Cambiado para claridad
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Error al agendar la cita. Inténtalo de nuevo.');
                }
                
                // Mostrar mensaje de éxito
                bookingConfirmation.innerHTML = `
                    <h3>¡Cita Confirmada!</h3>
                    <p>Tu cita con ${document.getElementById('confirm-barbero').textContent} para ${document.getElementById('confirm-servicio').textContent} el ${document.getElementById('confirm-fecha').textContent} a las ${selectedTime} ha sido agendada correctamente.</p>
                    <p>Recibirás una confirmación por correo electrónico.</p>
                    <p>ID de Reserva: ${data.cita_id}</p> 
                    <button class="book-button" onclick="window.location.reload()">Hacer otra Reserva</button>
                `;
                
            } catch (error) {
                console.error('Error al confirmar cita:', error);
                alert(`Error al agendar: ${error.message}`);
                
                // Reactivar botón
                confirmButton.disabled = false;
                confirmButton.textContent = 'Confirmar Cita';
            }
        });
    }
    
    // Función para validar email
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(String(email).toLowerCase());
    }
    
    // Inicializar
    init();

    if (confirmButton) {
        confirmButton.addEventListener('click', function() {
            // 1. Get data
            const bookingData = {
                nombre: clientNameInput.value.trim(),
                email: clientEmailInput.value.trim(),
                telefono: clientPhoneInput.value.trim(),
                barbero_id: selectedBarberoIdInput.value,
                servicio_id: selectedServicioIdInput.value,
                fecha: selectedDateInput.value,
                hora: selectedTimeInput.value
                // Add notas if you have an input for it
            };

            // 2. Basic Validation
            if (!bookingData.nombre || !bookingData.email || !bookingData.telefono) {
                alert('Por favor, completa tu nombre, correo electrónico y teléfono.');
                return;
            }
            if (!bookingData.barbero_id || !bookingData.servicio_id || !bookingData.fecha || !bookingData.hora) {
                alert('Error: Faltan detalles de la cita. Por favor, selecciona de nuevo.');
                return;
            }

            // 3. Disable button to prevent multiple clicks
            confirmButton.disabled = true;
            confirmButton.textContent = 'Procesando...';

            // 4. Send data to backend API
            fetch('/api/agendar-cita', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Include CSRF token if needed for POST requests
                    // 'X-CSRFToken': '{{ csrf_token() }}' // This needs backend setup if using Flask-WTF CSRF
                },
                body: JSON.stringify(bookingData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 5. Handle Success
                    bookingConfirmationPanel.innerHTML = `
                        <h3>¡Cita Confirmada!</h3>
                        <p>${data.mensaje || 'Tu cita ha sido agendada correctamente.'}</p>
                        <p>Recibirás una confirmación por correo (si aplica).</p>
                        <button onclick="window.location.reload()">Agendar otra cita</button>
                    `;
                    // Optionally clear form or redirect after a delay
                } else {
                    // 6. Handle Error
                    alert(`Error al agendar la cita: ${data.error || 'Inténtalo de nuevo.'}`);
                    confirmButton.disabled = false; // Re-enable button
                    confirmButton.textContent = 'Confirmar Cita';
                }
            })
            .catch(error => {
                console.error('Error en fetch:', error);
                alert('Ocurrió un error de red. Por favor, inténtalo de nuevo.');
                confirmButton.disabled = false; // Re-enable button
                confirmButton.textContent = 'Confirmar Cita';
            });
        });
    }

    // Function to show confirmation panel (ensure it populates hidden fields)
    function showConfirmationPanel(barberoId, barberoName, servicioId, servicioName, fecha, hora) {
        document.getElementById('confirm-barbero').textContent = barberoName;
        document.getElementById('confirm-servicio').textContent = servicioName;
        document.getElementById('confirm-fecha').textContent = fecha; // Format as needed
        document.getElementById('confirm-hora').textContent = hora;

        // Populate hidden fields
        selectedBarberoIdInput.value = barberoId;
        selectedServicioIdInput.value = servicioId;
        selectedDateInput.value = fecha; // Ensure YYYY-MM-DD format
        selectedTimeInput.value = hora; // Ensure HH:MM format

        bookingConfirmationPanel.style.display = 'block';
        bookingConfirmationPanel.scrollIntoView({ behavior: 'smooth' });
    }

    // Example of how showConfirmationPanel might be called when a time slot is clicked
    // This should be adapted based on how your time slots are generated and handled
    document.getElementById('horarios-container').addEventListener('click', function(event) {
        if (event.target.classList.contains('time-slot') && !event.target.disabled) {
            const selectedTime = event.target.dataset.time; // e.g., "10:30"
            const selectedDate = document.querySelector('.date-option.selected')?.dataset.fecha; // Get selected date
            const selectedBarberoId = document.getElementById('barbero-select').value;
            const selectedBarberoName = document.getElementById('barbero-select').selectedOptions[0]?.textContent;
            const selectedServicioId = document.getElementById('servicio-select').value;
            const selectedServicioName = document.getElementById('servicio-select').selectedOptions[0]?.textContent.split(' - ')[0]; // Extract name

            if (selectedDate && selectedBarberoId && selectedServicioId && selectedTime) {
                showConfirmationPanel(selectedBarberoId, selectedBarberoName, selectedServicioId, selectedServicioName, selectedDate, selectedTime);
            } else {
                alert("Por favor, asegúrate de haber seleccionado barbero, servicio y fecha.");
            }
        }
    });

    // Add the hideConfirmationPanel function if not already present
    window.hideConfirmationPanel = function() { // Make it global if called via onclick
        if (bookingConfirmationPanel) {
            bookingConfirmationPanel.style.display = 'none';
        }
        const clientForm = document.getElementById('client-info-form');
         // Reset client form fields manually if not a <form> element
        if (clientNameInput) clientNameInput.value = '';
        if (clientEmailInput) clientEmailInput.value = '';
        if (clientPhoneInput) clientPhoneInput.value = '';
    }

});