/**
 * Business Optimization JavaScript - Barber Brothers
 * ================================================
 * 
 * Sistema inteligente que maximiza conversiones usando datos de cookies
 * y algoritmos de personalización en tiempo real.
 * 
 * @author AI Assistant
 * @version 1.0
 */

class BusinessOptimizer {
    constructor() {
        this.conversionData = this.getConversionData();
        this.personalData = this.getPersonalizationData();
        this.init();
    }

    init() {
        console.log('🎯 Business Optimizer initialized');
        
        // Aplicar optimizaciones según el tipo de página
        this.applyPageOptimizations();
        
        // Inicializar tracking de comportamiento
        this.initBehaviorTracking();
        
        // Auto-completar formularios inteligentemente
        this.initSmartAutofill();
        
        // Mostrar recomendaciones personalizadas
        this.showPersonalizedContent();
        
        // Inicializar popups de conversión
        this.initConversionPopups();
    }

    getConversionData() {
        const cookie = this.getCookie('conversion_strategy');
        if (cookie) {
            try {
                return JSON.parse(cookie);
            } catch (e) {
                return {};
            }
        }
        return {};
    }

    getPersonalizationData() {
        const clientData = this.getCookie('client_booking_data');
        const preferences = this.getCookie('favorite_barber_service');
        
        let data = {
            client: {},
            preferences: {}
        };

        if (clientData) {
            try {
                data.client = JSON.parse(clientData);
            } catch (e) {}
        }

        if (preferences) {
            try {
                data.preferences = JSON.parse(preferences);
            } catch (e) {}
        }

        return data;
    }

    applyPageOptimizations() {
        const path = window.location.pathname;
        
        if (path === '/') {
            this.optimizeHomePage();
        } else if (path.includes('booking') || path.includes('agendar')) {
            this.optimizeBookingPage();
        } else if (path.includes('productos')) {
            this.optimizeProductsPage();
        } else if (path.includes('checkout')) {
            this.optimizeCheckoutPage();
        }
    }

    optimizeHomePage() {
        // Personalizar saludo para clientes recurrentes
        if (this.personalData.client.usage_count > 1) {
            this.showReturningCustomerGreeting();
        }

        // Mostrar booking rápido si es apropiado
        if (this.conversionData.show_incentives && this.personalData.preferences.favorite_barbero) {
            this.showQuickBookingOption();
        }

        // Destacar productos recomendados
        this.highlightRecommendedProducts();
    }

    optimizeBookingPage() {
        // Auto-seleccionar barbero favorito
        if (this.personalData.preferences.favorite_barbero) {
            this.autoSelectBarbero(this.personalData.preferences.favorite_barbero);
        }

        // Auto-seleccionar servicio favorito
        if (this.personalData.preferences.favorite_servicio) {
            this.autoSelectServicio(this.personalData.preferences.favorite_servicio);
        }

        // Sugerir horarios preferidos
        if (this.personalData.preferences.favorite_time) {
            this.prioritizeTimeSlots(this.personalData.preferences.favorite_time);
        }

        // Tracking de abandono en tiempo real
        this.trackBookingAbandonment();
    }

    optimizeProductsPage() {
        // Destacar productos vistos recientemente
        this.highlightViewedProducts();
        
        // Mostrar recomendaciones basadas en carrito
        this.showCartBasedRecommendations();
    }

    optimizeCheckoutPage() {
        // Auto-completar datos del cliente
        this.autofillCheckoutForm();
        
        // Mostrar incentivos de envío gratis
        this.showShippingIncentives();
        
        // Tracking anti-abandono
        this.initCheckoutAbandonmentPrevention();
    }

    initSmartAutofill() {
        // Auto-completar formulario de booking
        const bookingForm = document.getElementById('client-info-form');
        if (bookingForm && this.personalData.client.nombre) {
            this.fillBookingForm();
        }

        // Auto-completar formulario de checkout
        const checkoutForm = document.querySelector('form[action*="checkout"]');
        if (checkoutForm && this.personalData.client.nombre) {
            this.fillCheckoutForm();
        }
    }

    fillBookingForm() {
        const nameInput = document.getElementById('client-name');
        const emailInput = document.getElementById('client-email');
        const phoneInput = document.getElementById('client-phone');

        if (nameInput && !nameInput.value && this.personalData.client.nombre) {
            nameInput.value = this.personalData.client.nombre;
            this.addAutofilledClass(nameInput);
        }

        if (emailInput && !emailInput.value && this.personalData.client.email) {
            emailInput.value = this.personalData.client.email;
            this.addAutofilledClass(emailInput);
        }

        if (phoneInput && !phoneInput.value && this.personalData.client.telefono) {
            phoneInput.value = this.personalData.client.telefono;
            this.addAutofilledClass(phoneInput);
        }
    }

    fillCheckoutForm() {
        const fields = {
            'nombre': this.personalData.client.nombre,
            'email': this.personalData.client.email,
            'telefono': this.personalData.client.telefono
        };

        Object.entries(fields).forEach(([fieldName, value]) => {
            const input = document.querySelector(`input[name="${fieldName}"]`);
            if (input && !input.value && value) {
                input.value = value;
                this.addAutofilledClass(input);
            }
        });
    }

    addAutofilledClass(element) {
        element.classList.add('auto-filled');
        element.style.backgroundColor = '#f0f8ff';
        element.style.borderColor = '#4CAF50';
        
        // Mostrar tooltip explicativo
        this.showAutoFillTooltip(element);
    }

    showAutoFillTooltip(element) {
        const tooltip = document.createElement('div');
        tooltip.className = 'autofill-tooltip';
        tooltip.innerHTML = '✓ Completado automáticamente';
        tooltip.style.cssText = `
            position: absolute;
            background: #4CAF50;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
        `;

        document.body.appendChild(tooltip);

        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.right + 10 + 'px';
        tooltip.style.top = rect.top + 'px';

        setTimeout(() => tooltip.style.opacity = '1', 100);
        setTimeout(() => {
            tooltip.style.opacity = '0';
            setTimeout(() => document.body.removeChild(tooltip), 300);
        }, 2000);
    }

    autoSelectBarbero(barberoId) {
        const barberoSelect = document.getElementById('barbero-select');
        if (barberoSelect) {
            barberoSelect.value = barberoId;
            barberoSelect.dispatchEvent(new Event('change'));
            
            // Destacar visualmente
            barberoSelect.style.borderColor = '#4CAF50';
            barberoSelect.style.backgroundColor = '#f0f8ff';
        }
    }

    autoSelectServicio(servicioId) {
        const servicioSelect = document.getElementById('servicio-select');
        if (servicioSelect) {
            servicioSelect.value = servicioId;
            servicioSelect.dispatchEvent(new Event('change'));
            
            // Destacar visualmente
            servicioSelect.style.borderColor = '#4CAF50';
            servicioSelect.style.backgroundColor = '#f0f8ff';
        }
    }

    showReturningCustomerGreeting() {
        const heroSection = document.querySelector('.hero-section');
        if (heroSection && this.personalData.client.nombre) {
            const greeting = document.createElement('div');
            greeting.className = 'returning-customer-greeting';
            greeting.innerHTML = `
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 15px; border-radius: 10px; margin: 15px 0;
                           text-align: center; animation: slideInDown 0.5s;">
                    <h3 style="margin: 0; font-size: 1.2em;">
                        ¡Hola de nuevo, ${this.personalData.client.nombre}! 👋
                    </h3>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">
                        Nos alegra verte otra vez. ¿Lista para tu próxima cita?
                    </p>
                </div>
            `;
            
            heroSection.appendChild(greeting);
        }
    }

    showQuickBookingOption() {
        const preferences = this.personalData.preferences;
        if (preferences.favorite_barbero && preferences.favorite_servicio) {
            
            const quickBooking = document.createElement('div');
            quickBooking.className = 'quick-booking-widget';
            quickBooking.innerHTML = `
                <div style="background: #4CAF50; color: white; padding: 20px; 
                           border-radius: 10px; margin: 20px 0; text-align: center;
                           box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);">
                    <h3 style="margin: 0 0 10px 0;">⚡ Reserva Rápida</h3>
                    <p style="margin: 0 0 15px 0;">
                        Basado en tus preferencias anteriores
                    </p>
                    <button onclick="businessOptimizer.executeQuickBooking()" 
                            style="background: white; color: #4CAF50; border: none; 
                                   padding: 12px 25px; border-radius: 25px; font-weight: bold;
                                   cursor: pointer; transition: transform 0.2s;"
                            onmouseover="this.style.transform='scale(1.05)'"
                            onmouseout="this.style.transform='scale(1)'">
                        Agendar con Configuración Anterior
                    </button>
                </div>
            `;
            
            const bookingSection = document.querySelector('.booking-section');
            if (bookingSection) {
                bookingSection.insertBefore(quickBooking, bookingSection.firstChild);
            }
        }
    }

    executeQuickBooking() {
        // Auto-completar toda la configuración
        this.autoSelectBarbero(this.personalData.preferences.favorite_barbero);
        this.autoSelectServicio(this.personalData.preferences.favorite_servicio);
        
        // Scroll al calendario
        const bookingSection = document.querySelector('.booking-section');
        if (bookingSection) {
            bookingSection.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Tracking del evento
        this.trackEvent('quick_booking_used', {
            barbero_id: this.personalData.preferences.favorite_barbero,
            servicio_id: this.personalData.preferences.favorite_servicio
        });
    }

    initBehaviorTracking() {
        // Tracking de tiempo en página
        this.pageStartTime = Date.now();
        
        // Tracking de scroll
        let maxScroll = 0;
        window.addEventListener('scroll', () => {
            const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
            maxScroll = Math.max(maxScroll, scrollPercent);
        });

        // Tracking de clics en elementos importantes
        document.addEventListener('click', (e) => {
            if (e.target.closest('.add-to-cart') || 
                e.target.closest('.book-button') ||
                e.target.closest('.time-slot-btn')) {
                this.trackElementClick(e.target);
            }
        });

        // Tracking al salir de la página
        window.addEventListener('beforeunload', () => {
            this.trackPageExit(maxScroll);
        });
    }

    trackBookingAbandonment() {
        const steps = ['barbero-select', 'servicio-select', 'date-options', 'horarios-container'];
        let currentStep = 0;

        steps.forEach((stepId, index) => {
            const element = document.getElementById(stepId);
            if (element) {
                element.addEventListener('change', () => {
                    currentStep = Math.max(currentStep, index + 1);
                    this.updateBookingProgress(currentStep, steps.length);
                });
            }
        });

        // Detectar abandono
        let abandonmentTimer;
        document.addEventListener('mousemove', () => {
            clearTimeout(abandonmentTimer);
            abandonmentTimer = setTimeout(() => {
                if (currentStep > 0 && currentStep < steps.length) {
                    this.handleBookingAbandonment(currentStep);
                }
            }, 60000); // 1 minuto sin actividad
        });
    }

    updateBookingProgress(current, total) {
        const progress = (current / total) * 100;
        
        // Actualizar cookie de progreso
        this.setCookie('booking_progress', JSON.stringify({
            step: current,
            total: total,
            progress: progress,
            timestamp: Date.now()
        }), 1); // 1 día
        
        console.log(`📊 Booking progress: ${progress}%`);
    }

    handleBookingAbandonment(step) {
        if (this.conversionData.show_incentives) {
            this.showAbandonmentPopup(step);
        }
    }

    showAbandonmentPopup(step) {
        const popup = document.createElement('div');
        popup.className = 'abandonment-popup';
        popup.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                        background: rgba(0,0,0,0.7); z-index: 10000; display: flex; 
                        justify-content: center; align-items: center;">
                <div style="background: white; padding: 30px; border-radius: 15px; 
                           max-width: 400px; text-align: center; position: relative;">
                    <button onclick="this.closest('.abandonment-popup').remove()" 
                            style="position: absolute; top: 10px; right: 15px; 
                                   background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
                    <h3 style="color: #333; margin-bottom: 15px;">¡Espera! ¿Necesitas ayuda? 🤔</h3>
                    <p style="color: #666; margin-bottom: 20px;">
                        Vemos que estás interesado en agendar una cita. 
                        ${this.conversionData.discount_eligible ? '¡Te ofrecemos un 10% de descuento!' : '¿Te ayudamos a completar tu reserva?'}
                    </p>
                    <div style="display: flex; gap: 10px; justify-content: center;">
                        <button onclick="businessOptimizer.continueBooking(); this.closest('.abandonment-popup').remove();"
                                style="background: #4CAF50; color: white; border: none; 
                                       padding: 12px 20px; border-radius: 25px; cursor: pointer;">
                            Continuar Reserva
                        </button>
                        <button onclick="this.closest('.abandonment-popup').remove()"
                                style="background: #ccc; color: #333; border: none; 
                                       padding: 12px 20px; border-radius: 25px; cursor: pointer;">
                            Tal vez después
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(popup);
        
        // Tracking del evento
        this.trackEvent('abandonment_popup_shown', { step: step });
    }

    continueBooking() {
        // Aplicar descuento si es elegible
        if (this.conversionData.discount_eligible) {
            this.applyDiscountCode('DESCUENTO10');
        }
        
        // Tracking del evento
        this.trackEvent('abandonment_popup_continued');
    }

    initConversionPopups() {
        // Exit intent popup
        if (this.conversionData.show_incentives) {
            this.initExitIntentPopup();
        }
    }

    initExitIntentPopup() {
        let exitIntentShown = false;
        
        document.addEventListener('mouseleave', (e) => {
            if (e.clientY <= 0 && !exitIntentShown) {
                exitIntentShown = true;
                this.showExitIntentPopup();
            }
        });
    }

    showExitIntentPopup() {
        const popup = document.createElement('div');
        popup.className = 'exit-intent-popup';
        popup.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                        background: rgba(0,0,0,0.8); z-index: 10001; display: flex; 
                        justify-content: center; align-items: center;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 40px; border-radius: 20px; max-width: 450px; 
                           text-align: center; position: relative; box-shadow: 0 20px 40px rgba(0,0,0,0.3);">
                    <button onclick="this.closest('.exit-intent-popup').remove()" 
                            style="position: absolute; top: 15px; right: 20px; 
                                   background: none; border: none; color: white; 
                                   font-size: 24px; cursor: pointer;">×</button>
                    <h2 style="margin-bottom: 15px;">¡No te vayas! 🎉</h2>
                    <p style="margin-bottom: 20px; font-size: 1.1em;">
                        ${this.conversionData.discount_eligible ? 
                          '¡Te ofrecemos un 15% de descuento en tu primera cita!' : 
                          '¿Necesitas ayuda para agendar tu cita?'}
                    </p>
                    <div style="display: flex; gap: 15px; justify-content: center; margin-top: 25px;">
                        <button onclick="businessOptimizer.handleExitIntentOffer(); this.closest('.exit-intent-popup').remove();"
                                style="background: #4CAF50; color: white; border: none; 
                                       padding: 15px 25px; border-radius: 30px; cursor: pointer;
                                       font-weight: bold; font-size: 1.1em; transition: transform 0.2s;"
                                onmouseover="this.style.transform='scale(1.05)'"
                                onmouseout="this.style.transform='scale(1)'">
                            ${this.conversionData.discount_eligible ? 'Usar Descuento' : 'Obtener Ayuda'}
                        </button>
                        <button onclick="this.closest('.exit-intent-popup').remove()"
                                style="background: rgba(255,255,255,0.2); color: white; border: 1px solid white; 
                                       padding: 15px 25px; border-radius: 30px; cursor: pointer;">
                            No, gracias
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(popup);
        
        // Tracking del evento
        this.trackEvent('exit_intent_popup_shown');
    }

    handleExitIntentOffer() {
        if (this.conversionData.discount_eligible) {
            this.applyDiscountCode('DESCUENTO15');
            alert('¡Descuento aplicado! Completa tu reserva para aprovecharlo.');
        } else {
            // Redirigir a WhatsApp o mostrar formulario de contacto
            window.open('https://wa.me/573001234567?text=Hola, necesito ayuda para agendar una cita', '_blank');
        }
        
        // Tracking del evento
        this.trackEvent('exit_intent_offer_accepted');
    }

    // Utility functions
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    setCookie(name, value, days) {
        const expires = new Date(Date.now() + days * 864e5).toUTCString();
        document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Lax`;
    }

    trackEvent(event, data = {}) {
        console.log(`📈 Event tracked: ${event}`, data);
        
        // Enviar a analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', event, data);
        }
        
        // Guardar en cookie para análisis interno
        const events = JSON.parse(this.getCookie('tracked_events') || '[]');
        events.push({
            event: event,
            data: data,
            timestamp: Date.now()
        });
        
        // Mantener solo los últimos 50 eventos
        this.setCookie('tracked_events', JSON.stringify(events.slice(-50)), 7);
    }

    trackElementClick(element) {
        this.trackEvent('element_click', {
            element: element.tagName,
            class: element.className,
            text: element.textContent.slice(0, 50)
        });
    }

    trackPageExit(maxScroll) {
        const timeOnPage = Date.now() - this.pageStartTime;
        
        this.trackEvent('page_exit', {
            time_on_page: timeOnPage,
            max_scroll_percent: Math.round(maxScroll),
            page_path: window.location.pathname
        });
    }
}

// Inicializar automáticamente
let businessOptimizer;
document.addEventListener('DOMContentLoaded', () => {
    businessOptimizer = new BusinessOptimizer();
});

// Exportar para uso global
window.businessOptimizer = businessOptimizer;
