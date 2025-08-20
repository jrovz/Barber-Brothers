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

    highlightRecommendedProducts() {
        console.log('✨ Destacando productos recomendados...');
        
        // Obtener productos recomendados basados en comportamiento del usuario
        const recommendedProducts = this.getRecommendedProducts();
        
        if (recommendedProducts.length === 0) return;
        
        // Aplicar estilos de destacado a productos recomendados
        this.applyRecommendationHighlights(recommendedProducts);
        
        // Añadir badges de recomendación
        this.addRecommendationBadges(recommendedProducts);
        
        // Mostrar sección de productos recomendados
        this.createRecommendedSection(recommendedProducts);
    }

    getRecommendedProducts() {
        const recommendations = [];
        
        // 1. Productos basados en el historial de visualización
        const viewedProducts = this.getViewedProductsFromCookie();
        if (viewedProducts.length > 0) {
            recommendations.push(...this.getRelatedToViewed(viewedProducts));
        }
        
        // 2. Productos basados en el carrito actual
        const cartProducts = this.getCartProducts();
        if (cartProducts.length > 0) {
            recommendations.push(...this.getComplementaryProducts(cartProducts));
        }
        
        // 3. Productos populares para usuarios nuevos
        if (this.personalData.client.usage_count <= 1) {
            recommendations.push(...this.getPopularProducts());
        }
        
        // 4. Productos basados en preferencias guardadas
        if (this.personalData.preferences.favorite_barbero) {
            recommendations.push(...this.getBarberoFavoriteProducts());
        }
        
        // Eliminar duplicados y limitar a 6 productos
        const uniqueRecommendations = recommendations
            .filter((product, index, self) => 
                index === self.findIndex(p => p.id === product.id))
            .slice(0, 6);
        
        return uniqueRecommendations;
    }

    getViewedProductsFromCookie() {
        const viewedData = this.getCookie('viewed_products');
        if (viewedData) {
            try {
                const data = JSON.parse(viewedData);
                return data.timeline ? data.timeline.map(t => data.products[t.id]).filter(Boolean) : [];
            } catch (e) {
                return [];
            }
        }
        return [];
    }

    getCartProducts() {
        try {
            const cart = JSON.parse(localStorage.getItem('cart') || '[]');
            return cart.map(item => ({
                id: item.id,
                name: item.name,
                price: item.price,
                category: item.category || 'general'
            }));
        } catch (e) {
            return [];
        }
    }

    getRelatedToViewed(viewedProducts) {
        // Simular productos relacionados basados en categorías vistas
        const categories = [...new Set(viewedProducts.map(p => p.category))];
        const relatedProducts = [];
        
        // En una implementación real, esto consultaría una API
        categories.forEach(category => {
            if (category && category !== 'general') {
                relatedProducts.push({
                    id: `related_${category}_${Date.now()}`,
                    name: `Producto recomendado de ${category}`,
                    price: Math.floor(Math.random() * 50000) + 10000,
                    category: category,
                    recommendation_reason: 'Basado en productos vistos'
                });
            }
        });
        
        return relatedProducts.slice(0, 2);
    }

    getComplementaryProducts(cartProducts) {
        // Productos que complementan los del carrito
        const complementary = [];
        
        cartProducts.forEach(product => {
            // Lógica simple de complementos
            if (product.name.toLowerCase().includes('corte')) {
                complementary.push({
                    id: `complement_beard_${Date.now()}`,
                    name: 'Arreglo de Barba',
                    price: 25000,
                    category: 'servicios',
                    recommendation_reason: 'Perfecto con tu corte'
                });
            }
            
            if (product.category === 'productos') {
                complementary.push({
                    id: `complement_aftershave_${Date.now()}`,
                    name: 'Aftershave Premium',
                    price: 35000,
                    category: 'productos',
                    recommendation_reason: 'Complementa tu rutina'
                });
            }
        });
        
        return complementary.slice(0, 2);
    }

    getPopularProducts() {
        // Productos populares para usuarios nuevos
        return [
            {
                id: 'popular_1',
                name: 'Corte Clásico',
                price: 30000,
                category: 'servicios',
                recommendation_reason: 'Más popular'
            },
            {
                id: 'popular_2',
                name: 'Kit de Cuidado Básico',
                price: 45000,
                category: 'productos',
                recommendation_reason: 'Recomendado para principiantes'
            }
        ];
    }

    getBarberoFavoriteProducts() {
        // Productos/servicios del barbero favorito
        return [
            {
                id: 'barbero_special',
                name: 'Servicio Especialidad',
                price: 40000,
                category: 'servicios',
                recommendation_reason: `Especialidad de tu barbero favorito`
            }
        ];
    }

    applyRecommendationHighlights(recommendedProducts) {
        recommendedProducts.forEach(product => {
            // Buscar el elemento del producto en la página
            const productElement = document.querySelector(
                `[data-id="${product.id}"], [data-product-id="${product.id}"]`
            );
            
            if (productElement) {
                // Añadir clase de destacado
                productElement.classList.add('recommended-product');
                
                // Aplicar estilos de destacado
                productElement.style.cssText += `
                    border: 2px solid #4CAF50 !important;
                    box-shadow: 0 4px 20px rgba(76, 175, 80, 0.3) !important;
                    transform: scale(1.02);
                    transition: all 0.3s ease;
                `;
                
                // Añadir animación sutil
                productElement.addEventListener('mouseenter', function() {
                    this.style.transform = 'scale(1.05)';
                });
                
                productElement.addEventListener('mouseleave', function() {
                    this.style.transform = 'scale(1.02)';
                });
            }
        });
    }

    addRecommendationBadges(recommendedProducts) {
        recommendedProducts.forEach(product => {
            const productElement = document.querySelector(
                `[data-id="${product.id}"], [data-product-id="${product.id}"]`
            );
            
            if (productElement && !productElement.querySelector('.recommendation-badge')) {
                const badge = document.createElement('div');
                badge.className = 'recommendation-badge';
                badge.innerHTML = '⭐ Recomendado';
                badge.style.cssText = `
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: linear-gradient(135deg, #4CAF50, #45a049);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                    z-index: 10;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                `;
                
                // Asegurar que el contenedor tenga posición relativa
                productElement.style.position = 'relative';
                productElement.appendChild(badge);
            }
        });
    }

    createRecommendedSection(recommendedProducts) {
        // Verificar si ya existe la sección
        if (document.querySelector('.recommendations-section')) return;
        
        const productsContainer = document.querySelector('.productos-container, .products-grid, .main-content');
        if (!productsContainer) return;
        
        const recommendationsSection = document.createElement('div');
        recommendationsSection.className = 'recommendations-section';
        recommendationsSection.innerHTML = `
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 25px; margin: 30px 0; border-radius: 15px;
                        box-shadow: 0 8px 25px rgba(0,0,0,0.15);">
                <h3 style="margin: 0 0 20px 0; text-align: center; font-size: 1.4em;">
                    ✨ Recomendado Especialmente Para Ti
                </h3>
                <div class="recommendations-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                                                          gap: 20px; margin-top: 20px;">
                    ${recommendedProducts.map(product => `
                        <div class="recommendation-card" style="background: rgba(255,255,255,0.1); 
                                                               border-radius: 10px; padding: 20px; text-align: center;
                                                               backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);">
                            <h4 style="margin: 0 0 10px 0; color: white; font-size: 1.1em;">
                                ${product.name}
                            </h4>
                            <p style="margin: 0 0 10px 0; font-size: 1.2em; font-weight: bold; color: #90EE90;">
                                $${product.price.toLocaleString()} COP
                            </p>
                            <p style="margin: 0 0 15px 0; font-size: 0.9em; opacity: 0.8;">
                                ${product.recommendation_reason}
                            </p>
                            <button onclick="businessOptimizer.addRecommendedProduct('${product.id}')" 
                                    style="background: #4CAF50; color: white; border: none; 
                                           padding: 10px 20px; border-radius: 25px; cursor: pointer;
                                           font-weight: bold; transition: all 0.3s ease;"
                                    onmouseover="this.style.background='#45a049'; this.style.transform='scale(1.05)'"
                                    onmouseout="this.style.background='#4CAF50'; this.style.transform='scale(1)'">
                                ${product.category === 'servicios' ? 'Agendar' : 'Añadir al Carrito'}
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        // Insertar al inicio del contenedor
        productsContainer.insertBefore(recommendationsSection, productsContainer.firstChild);
    }

    addRecommendedProduct(productId) {
        // Buscar el producto en las recomendaciones
        const recommendedProducts = this.getRecommendedProducts();
        const product = recommendedProducts.find(p => p.id === productId);
        
        if (!product) return;
        
        if (product.category === 'servicios') {
            // Redirigir a la página de booking con el servicio preseleccionado
            window.location.href = '/booking?servicio=' + encodeURIComponent(product.name);
        } else {
            // Añadir al carrito
            this.addToCartFromRecommendation(product);
        }
        
        // Tracking del evento
        this.trackEvent('recommended_product_selected', {
            product_id: productId,
            product_name: product.name,
            recommendation_reason: product.recommendation_reason
        });
    }

    addToCartFromRecommendation(product) {
        // Simular añadir al carrito
        if (window.smartCart && window.smartCart.addToCartSilently) {
            window.smartCart.addToCartSilently(product);
            if (window.updateCart) window.updateCart();
        } else {
            // Fallback al localStorage directo
            const cart = JSON.parse(localStorage.getItem('cart') || '[]');
            cart.push({
                id: product.id,
                name: product.name,
                price: product.price,
                quantity: 1,
                image: product.image || '/static/images/default-product.jpg'
            });
            localStorage.setItem('cart', JSON.stringify(cart));
        }
        
        // Mostrar mensaje de éxito
        this.showSuccessMessage(`${product.name} añadido al carrito desde recomendaciones`);
    }

    showSuccessMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'success-toast';
        toast.innerHTML = `
            <div style="position: fixed; top: 20px; right: 20px; z-index: 10001;
                        background: #4CAF50; color: white; padding: 15px 20px; 
                        border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                        transform: translateX(100%); transition: transform 0.3s ease;">
                ✅ ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animar entrada
        setTimeout(() => {
            toast.firstElementChild.style.transform = 'translateX(0)';
        }, 100);
        
        // Animar salida y remover
        setTimeout(() => {
            toast.firstElementChild.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }, 3000);
    }

    highlightViewedProducts() {
        // Destacar productos vistos recientemente
        const viewedProducts = this.getViewedProductsFromCookie();
        
        viewedProducts.slice(0, 3).forEach(product => {
            const productElement = document.querySelector(
                `[data-id="${product.id}"], [data-product-id="${product.id}"]`
            );
            
            if (productElement && !productElement.classList.contains('recently-viewed')) {
                productElement.classList.add('recently-viewed');
                
                // Añadir badge de "visto recientemente"
                const badge = document.createElement('div');
                badge.className = 'recently-viewed-badge';
                badge.innerHTML = '👁️ Visto recientemente';
                badge.style.cssText = `
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    background: rgba(33, 150, 243, 0.9);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 15px;
                    font-size: 11px;
                    z-index: 10;
                `;
                
                productElement.style.position = 'relative';
                productElement.appendChild(badge);
            }
        });
    }

    showCartBasedRecommendations() {
        const cartProducts = this.getCartProducts();
        if (cartProducts.length === 0) return;
        
        const complementaryProducts = this.getComplementaryProducts(cartProducts);
        
        if (complementaryProducts.length > 0) {
            this.createCartBasedRecommendationsWidget(complementaryProducts);
        }
    }

    createCartBasedRecommendationsWidget(products) {
        // Verificar si ya existe
        if (document.querySelector('.cart-recommendations-widget')) return;
        
        const widget = document.createElement('div');
        widget.className = 'cart-recommendations-widget';
        widget.innerHTML = `
            <div style="position: fixed; bottom: 20px; right: 20px; 
                        background: white; border-radius: 15px; padding: 20px;
                        box-shadow: 0 8px 25px rgba(0,0,0,0.15); max-width: 300px;
                        z-index: 1000; border: 2px solid #4CAF50;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: #333;">💡 También podrías necesitar</h4>
                    <button onclick="this.closest('.cart-recommendations-widget').remove()" 
                            style="background: none; border: none; font-size: 18px; cursor: pointer;">×</button>
                </div>
                <div>
                    ${products.map(product => `
                        <div style="display: flex; justify-content: space-between; align-items: center; 
                                    margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                            <div style="flex: 1;">
                                <div style="font-weight: 500; font-size: 0.9em;">${product.name}</div>
                                <div style="color: #4CAF50; font-weight: bold; font-size: 0.8em;">
                                    $${product.price.toLocaleString()} COP
                                </div>
                            </div>
                            <button onclick="businessOptimizer.addRecommendedProduct('${product.id}')" 
                                    style="background: #4CAF50; color: white; border: none; 
                                           padding: 5px 10px; border-radius: 12px; cursor: pointer; font-size: 0.8em;">
                                +
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        document.body.appendChild(widget);
        
        // Auto-remover después de 15 segundos
        setTimeout(() => {
            if (widget.parentNode) {
                widget.remove();
            }
        }, 15000);
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
