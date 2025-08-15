/**
 * Smart Cart System - Barber Brothers
 * ==================================
 * 
 * Sistema inteligente de carrito que maximiza conversiones
 * usando cookies, analytics y algoritmos de recomendación.
 * 
 * @author AI Assistant
 * @version 1.0
 */

class SmartCart {
    constructor() {
        this.cart = this.loadCart();
        this.viewedProducts = this.loadViewedProducts();
        this.conversionData = this.getConversionData();
        this.init();
    }

    init() {
        console.log('🛒 Smart Cart initialized');
        
        // Override del cart.js existente con funcionalidad inteligente
        this.enhanceExistingCart();
        
        // Cargar carrito persistente
        this.loadPersistentCart();
        
        // Inicializar tracking de productos
        this.initProductTracking();
        
        // Inicializar recomendaciones
        this.initRecommendations();
        
        // Inicializar incentivos de envío
        this.initShippingIncentives();
        
        // Anti-abandono del carrito
        this.initAbandonmentPrevention();
    }

    enhanceExistingCart() {
        // Interceptar funciones del cart.js existente
        const originalAddToCart = window.addToCart || (() => {});
        const originalUpdateCart = window.updateCart || (() => {});
        
        // Enhanced add to cart
        window.addToCart = (productData) => {
            // Ejecutar lógica original
            originalAddToCart(productData);
            
            // Añadir funcionalidad inteligente
            this.smartAddToCart(productData);
        };
        
        // Enhanced update cart
        window.updateCart = () => {
            originalUpdateCart();
            this.savePersistentCart();
            this.updateRecommendations();
            this.checkShippingIncentives();
        };
    }

    loadCart() {
        // Cargar desde localStorage (compatibilidad con cart.js)
        return JSON.parse(localStorage.getItem('cart') || '[]');
    }

    loadPersistentCart() {
        const persistentCart = this.getCookie('persistent_cart');
        if (persistentCart) {
            try {
                const cartData = JSON.parse(persistentCart);
                
                // Verificar si el carrito es reciente (no más de 7 días)
                const cartDate = new Date(cartData.timestamp);
                const daysDiff = (Date.now() - cartDate.getTime()) / (1000 * 3600 * 24);
                
                if (daysDiff <= 7 && cartData.items && cartData.items.length > 0) {
                    this.showCartRecoveryOption(cartData);
                }
            } catch (e) {
                console.log('Error loading persistent cart:', e);
            }
        }
    }

    showCartRecoveryOption(cartData) {
        const recoveryBanner = document.createElement('div');
        recoveryBanner.className = 'cart-recovery-banner';
        recoveryBanner.innerHTML = `
            <div style="background: linear-gradient(135deg, #FF6B6B, #4ECDC4); 
                        color: white; padding: 15px; border-radius: 10px; margin: 15px;
                        display: flex; justify-content: space-between; align-items: center;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <div>
                    <h4 style="margin: 0; font-size: 1.1em;">🛒 Tienes productos guardados</h4>
                    <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 0.9em;">
                        ${cartData.total_items} productos por $${cartData.estimated_total.toLocaleString()} COP
                    </p>
                </div>
                <div>
                    <button onclick="smartCart.recoverCart()" 
                            style="background: white; color: #FF6B6B; border: none; 
                                   padding: 10px 20px; border-radius: 25px; font-weight: bold;
                                   cursor: pointer; margin-right: 10px;">
                        Recuperar
                    </button>
                    <button onclick="this.closest('.cart-recovery-banner').remove()" 
                            style="background: rgba(255,255,255,0.2); color: white; border: 1px solid white;
                                   padding: 8px 15px; border-radius: 20px; cursor: pointer;">
                        ×
                    </button>
                </div>
            </div>
        `;
        
        // Insertar al inicio del body
        document.body.insertBefore(recoveryBanner, document.body.firstChild);
        
        // Auto-hide después de 10 segundos
        setTimeout(() => {
            if (recoveryBanner.parentNode) {
                recoveryBanner.remove();
            }
        }, 10000);
    }

    recoverCart() {
        const persistentCart = this.getCookie('persistent_cart');
        if (persistentCart) {
            try {
                const cartData = JSON.parse(persistentCart);
                
                // Restaurar items al carrito actual
                cartData.items.forEach(item => {
                    this.addToCartSilently(item);
                });
                
                // Actualizar UI
                if (window.updateCart) {
                    window.updateCart();
                }
                
                // Abrir panel del carrito
                if (window.openCartPanel) {
                    window.openCartPanel();
                }
                
                // Mostrar mensaje de éxito
                this.showSuccessMessage('¡Carrito recuperado exitosamente!');
                
                // Tracking
                this.trackEvent('cart_recovered', {
                    items_count: cartData.total_items,
                    cart_value: cartData.estimated_total
                });
                
                // Remover banner
                const banner = document.querySelector('.cart-recovery-banner');
                if (banner) banner.remove();
                
            } catch (e) {
                console.error('Error recovering cart:', e);
            }
        }
    }

    smartAddToCart(productData) {
        // Tracking de producto visto/añadido
        this.trackProductView(productData);
        
        // Guardar carrito persistente
        this.savePersistentCart();
        
        // Actualizar recomendaciones
        this.updateRecommendations();
        
        // Verificar incentivos
        this.checkShippingIncentives();
        
        // Mostrar productos relacionados
        this.showRelatedProducts(productData);
    }

    trackProductView(productData) {
        const viewData = {
            id: productData.id,
            name: productData.name,
            price: productData.price,
            category: productData.category || 'general',
            timestamp: Date.now(),
            action: 'added_to_cart'
        };
        
        // Actualizar lista de productos vistos
        this.viewedProducts = this.viewedProducts.filter(p => p.id !== productData.id);
        this.viewedProducts.unshift(viewData);
        this.viewedProducts = this.viewedProducts.slice(0, 20); // Mantener últimos 20
        
        // Guardar en cookie
        this.setCookie('viewed_products', JSON.stringify({
            products: this.viewedProducts.reduce((acc, p) => {
                acc[p.id] = p;
                return acc;
            }, {}),
            timeline: this.viewedProducts.map(p => ({id: p.id, timestamp: p.timestamp}))
        }), 30);
        
        // Tracking analytics
        this.trackEvent('product_added_to_cart', viewData);
    }

    savePersistentCart() {
        const cartData = {
            items: this.cart,
            timestamp: new Date().toISOString(),
            total_items: this.cart.reduce((sum, item) => sum + (item.quantity || 1), 0),
            estimated_total: this.cart.reduce((sum, item) => sum + (item.price * (item.quantity || 1)), 0),
            session_id: this.getSessionId()
        };
        
        this.setCookie('persistent_cart', JSON.stringify(cartData), 7);
    }

    loadViewedProducts() {
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

    initRecommendations() {
        // Mostrar recomendaciones en la página de productos
        if (window.location.pathname.includes('productos')) {
            this.showViewedRecentlySection();
        }
        
        // Mostrar recomendaciones en el carrito
        this.enhanceCartWithRecommendations();
    }

    showViewedRecentlySection() {
        if (this.viewedProducts.length === 0) return;
        
        const productsContainer = document.querySelector('.productos-container, .products-grid');
        if (!productsContainer) return;
        
        const recentlyViewed = document.createElement('div');
        recentlyViewed.className = 'recently-viewed-section';
        recentlyViewed.innerHTML = `
            <div style="margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                <h3 style="margin-bottom: 15px; color: #333;">👁️ Vistos Recientemente</h3>
                <div class="recently-viewed-products" style="display: flex; gap: 15px; overflow-x: auto; padding: 10px 0;">
                    ${this.viewedProducts.slice(0, 6).map(product => `
                        <div class="recently-viewed-item" style="min-width: 200px; text-align: center;">
                            <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                <h5 style="margin: 0 0 10px 0; font-size: 0.9em;">${product.name}</h5>
                                <p style="margin: 0 0 10px 0; color: #4CAF50; font-weight: bold;">
                                    $${product.price.toLocaleString()} COP
                                </p>
                                <button onclick="smartCart.quickAddToCart('${product.id}')" 
                                        class="quick-add-btn"
                                        style="background: #4CAF50; color: white; border: none; 
                                               padding: 8px 15px; border-radius: 20px; cursor: pointer; font-size: 0.8em;">
                                    + Añadir
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        productsContainer.insertBefore(recentlyViewed, productsContainer.firstChild);
    }

    enhanceCartWithRecommendations() {
        // Interceptar apertura del carrito
        const originalOpenCart = window.openCartPanel || (() => {});
        
        window.openCartPanel = () => {
            originalOpenCart();
            setTimeout(() => this.addCartRecommendations(), 100);
        };
    }

    addCartRecommendations() {
        const cartItems = document.getElementById('cart-items');
        if (!cartItems || this.cart.length === 0) return;
        
        // Evitar duplicados
        if (cartItems.querySelector('.cart-recommendations')) return;
        
        const recommendations = this.getCartBasedRecommendations();
        if (recommendations.length === 0) return;
        
        const recommendationsSection = document.createElement('div');
        recommendationsSection.className = 'cart-recommendations';
        recommendationsSection.innerHTML = `
            <div style="border-top: 1px solid #eee; padding: 15px 0; margin-top: 15px;">
                <h4 style="margin: 0 0 15px 0; color: #333; font-size: 1em;">💡 También te podría interesar</h4>
                <div class="cart-recommendation-items">
                    ${recommendations.map(product => `
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; 
                                    padding: 10px; background: #f8f9fa; border-radius: 8px;">
                            <div style="flex: 1;">
                                <div style="font-weight: 500; font-size: 0.9em;">${product.name}</div>
                                <div style="color: #4CAF50; font-weight: bold; font-size: 0.8em;">
                                    $${product.price.toLocaleString()} COP
                                </div>
                            </div>
                            <button onclick="smartCart.quickAddToCart('${product.id}')" 
                                    style="background: #4CAF50; color: white; border: none; 
                                           padding: 6px 12px; border-radius: 15px; cursor: pointer; font-size: 0.8em;">
                                + Añadir
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        cartItems.appendChild(recommendationsSection);
    }

    getCartBasedRecommendations() {
        // Simular recomendaciones basadas en el carrito actual
        // En producción, esto se conectaría con la API de recomendaciones
        const cartCategories = this.cart.map(item => item.category).filter(Boolean);
        const viewedInCategory = this.viewedProducts.filter(p => 
            cartCategories.includes(p.category) && 
            !this.cart.find(c => c.id === p.id)
        );
        
        return viewedInCategory.slice(0, 3);
    }

    quickAddToCart(productId) {
        const product = this.viewedProducts.find(p => p.id === productId);
        if (product) {
            // Simular click en botón add-to-cart
            const addButton = document.querySelector(`[data-id="${productId}"]`);
            if (addButton) {
                addButton.click();
            } else {
                // Añadir directamente si no hay botón
                this.addToCartSilently(product);
                if (window.updateCart) window.updateCart();
                this.showSuccessMessage(`${product.name} añadido al carrito`);
            }
        }
    }

    addToCartSilently(product) {
        const existingItem = this.cart.find(item => item.id === product.id);
        if (existingItem) {
            existingItem.quantity = (existingItem.quantity || 1) + 1;
        } else {
            this.cart.push({
                id: product.id,
                name: product.name,
                price: product.price,
                quantity: 1,
                image: product.image || '/static/images/default-product.jpg'
            });
        }
        
        // Actualizar localStorage
        localStorage.setItem('cart', JSON.stringify(this.cart));
    }

    initShippingIncentives() {
        this.freeShippingThreshold = 100000; // 100k COP
        this.checkShippingIncentives();
    }

    checkShippingIncentives() {
        const cartTotal = this.cart.reduce((sum, item) => sum + (item.price * (item.quantity || 1)), 0);
        const remaining = this.freeShippingThreshold - cartTotal;
        
        if (remaining > 0 && cartTotal > 0) {
            this.showShippingIncentive(remaining, cartTotal);
        } else if (cartTotal >= this.freeShippingThreshold) {
            this.showFreeShippingAchieved();
        }
    }

    showShippingIncentive(remaining, current) {
        // Remover incentivo anterior
        const existingIncentive = document.querySelector('.shipping-incentive');
        if (existingIncentive) existingIncentive.remove();
        
        const progress = (current / this.freeShippingThreshold) * 100;
        
        const incentive = document.createElement('div');
        incentive.className = 'shipping-incentive';
        incentive.innerHTML = `
            <div style="background: linear-gradient(135deg, #FF9A8B, #A8E6CF); 
                        color: white; padding: 15px; margin: 15px; border-radius: 10px;
                        text-align: center; position: relative; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; height: 100%; 
                           background: rgba(255,255,255,0.2); width: ${progress}%; 
                           transition: width 0.5s ease;"></div>
                <div style="position: relative; z-index: 1;">
                    <h4 style="margin: 0 0 10px 0; font-size: 1.1em;">🚚 ¡Envío GRATIS te espera!</h4>
                    <p style="margin: 0; font-size: 0.9em;">
                        Añade $${remaining.toLocaleString()} COP más y obtén envío gratuito
                    </p>
                    <div style="background: rgba(255,255,255,0.3); height: 4px; 
                               border-radius: 2px; margin: 10px 20px 0 20px;">
                        <div style="background: white; height: 100%; width: ${progress}%; 
                                   border-radius: 2px; transition: width 0.5s ease;"></div>
                    </div>
                </div>
            </div>
        `;
        
        // Insertarlo antes del carrito o en la parte superior
        const cartSection = document.querySelector('.cart-section, .checkout-section') || document.body;
        cartSection.insertBefore(incentive, cartSection.firstChild);
    }

    showFreeShippingAchieved() {
        const celebration = document.createElement('div');
        celebration.className = 'free-shipping-achieved';
        celebration.innerHTML = `
            <div style="background: linear-gradient(135deg, #4CAF50, #45a049); 
                        color: white; padding: 15px; margin: 15px; border-radius: 10px;
                        text-align: center; animation: celebration 0.5s ease;">
                <h4 style="margin: 0; font-size: 1.2em;">🎉 ¡Felicitaciones!</h4>
                <p style="margin: 5px 0 0 0;">Tienes envío GRATIS en tu pedido</p>
            </div>
        `;
        
        document.body.insertBefore(celebration, document.body.firstChild);
        
        // Auto-remove después de 5 segundos
        setTimeout(() => {
            if (celebration.parentNode) {
                celebration.remove();
            }
        }, 5000);
        
        // Tracking
        this.trackEvent('free_shipping_achieved');
    }

    initAbandonmentPrevention() {
        // Detectar cuando el usuario está a punto de abandonar el carrito
        let cartInteractionTimer;
        
        // Resetear timer en cada interacción con el carrito
        document.addEventListener('click', (e) => {
            if (e.target.closest('#cart-panel') || e.target.closest('.cart-related')) {
                clearTimeout(cartInteractionTimer);
                cartInteractionTimer = setTimeout(() => {
                    this.handleCartAbandonment();
                }, 30000); // 30 segundos sin interacción
            }
        });
        
        // Detectar cuando el carrito está abierto pero no hay actividad
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.target.id === 'cart-panel' && 
                    mutation.target.classList.contains('open')) {
                    cartInteractionTimer = setTimeout(() => {
                        this.handleCartAbandonment();
                    }, 30000);
                }
            });
        });
        
        const cartPanel = document.getElementById('cart-panel');
        if (cartPanel) {
            observer.observe(cartPanel, { attributes: true, attributeFilter: ['class'] });
        }
    }

    handleCartAbandonment() {
        if (this.cart.length === 0) return;
        
        const cartValue = this.cart.reduce((sum, item) => sum + (item.price * (item.quantity || 1)), 0);
        
        // Solo mostrar para carritos con valor significativo
        if (cartValue < 30000) return; // Menos de 30k COP
        
        this.showCartAbandonmentPopup(cartValue);
    }

    showCartAbandonmentPopup(cartValue) {
        const popup = document.createElement('div');
        popup.className = 'cart-abandonment-popup';
        popup.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                        background: rgba(0,0,0,0.7); z-index: 10000; display: flex; 
                        justify-content: center; align-items: center;">
                <div style="background: white; padding: 30px; border-radius: 15px; 
                           max-width: 400px; text-align: center; position: relative;">
                    <button onclick="this.closest('.cart-abandonment-popup').remove()" 
                            style="position: absolute; top: 10px; right: 15px; 
                                   background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
                    <h3 style="color: #333; margin-bottom: 15px;">🛒 ¡Tu carrito te espera!</h3>
                    <p style="color: #666; margin-bottom: 20px;">
                        Tienes $${cartValue.toLocaleString()} COP en productos seleccionados.
                        ¡No los pierdas!
                    </p>
                    <div style="display: flex; gap: 10px; justify-content: center;">
                        <button onclick="smartCart.finishPurchase(); this.closest('.cart-abandonment-popup').remove();"
                                style="background: #4CAF50; color: white; border: none; 
                                       padding: 12px 20px; border-radius: 25px; cursor: pointer;">
                            Finalizar Compra
                        </button>
                        <button onclick="smartCart.saveForLater(); this.closest('.cart-abandonment-popup').remove();"
                                style="background: #2196F3; color: white; border: none; 
                                       padding: 12px 20px; border-radius: 25px; cursor: pointer;">
                            Guardar para Después
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(popup);
        
        // Tracking
        this.trackEvent('cart_abandonment_popup_shown', {
            cart_value: cartValue,
            items_count: this.cart.length
        });
    }

    finishPurchase() {
        // Redirigir al checkout
        window.location.href = '/checkout';
        
        // Tracking
        this.trackEvent('cart_abandonment_popup_checkout');
    }

    saveForLater() {
        // Guardar carrito y mostrar mensaje
        this.savePersistentCart();
        this.showSuccessMessage('Carrito guardado. Te esperamos pronto! 😊');
        
        // Tracking
        this.trackEvent('cart_abandonment_popup_saved');
    }

    // Utility functions
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

    getSessionId() {
        let sessionId = sessionStorage.getItem('session_id');
        if (!sessionId) {
            sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('session_id', sessionId);
        }
        return sessionId;
    }

    showSuccessMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'success-toast';
        toast.innerHTML = `
            <div style="position: fixed; top: 20px; right: 20px; z-index: 10001;
                        background: #4CAF50; color: white; padding: 15px 20px; 
                        border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                        transform: translateX(100%); transition: transform 0.3s ease;">
                ${message}
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
        console.log(`📈 Smart Cart Event: ${event}`, data);
        
        // Enviar a analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', event, {
                event_category: 'smart_cart',
                ...data
            });
        }
    }
}

// Inicializar cuando el DOM esté listo
let smartCart;
document.addEventListener('DOMContentLoaded', () => {
    smartCart = new SmartCart();
});

// Exportar para uso global
window.smartCart = smartCart;
