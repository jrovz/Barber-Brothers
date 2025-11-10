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
        
        // Anti-abandono del carrito (eliminado)
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

    initProductTracking() {
        console.log('🔍 Inicializando tracking de productos...');
        
        // Tracking de visualización de productos
        this.setupProductViewTracking();
        
        // Tracking de interacciones con productos
        this.setupProductInteractionTracking();
        
        // Tracking de tiempo en página de producto
        this.setupProductTimeTracking();
        
        // Tracking de abandono de producto
        this.setupProductAbandonmentTracking();
    }

    setupProductViewTracking() {
        // Detectar cuando un producto entra en el viewport
        const productElements = document.querySelectorAll('.producto-item, .product-card, [data-product-id]');
        
        if (productElements.length === 0) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const productElement = entry.target;
                    const productData = this.extractProductData(productElement);
                    
                    if (productData) {
                        this.trackProductView(productData);
                        observer.unobserve(entry.target); // Solo trackear una vez
                    }
                }
            });
        }, {
            threshold: 0.5 // 50% del producto visible
        });
        
        productElements.forEach(element => observer.observe(element));
    }

    setupProductInteractionTracking() {
        // Tracking de clics en productos
        document.addEventListener('click', (e) => {
            const productElement = e.target.closest('.producto-item, .product-card, [data-product-id]');
            if (productElement) {
                const productData = this.extractProductData(productElement);
                if (productData) {
                    this.trackEvent('product_clicked', {
                        product_id: productData.id,
                        product_name: productData.name,
                        product_price: productData.price,
                        click_element: e.target.tagName.toLowerCase()
                    });
                }
            }
            
            // Tracking específico de botones "add to cart"
            if (e.target.closest('.add-to-cart')) {
                const button = e.target.closest('.add-to-cart');
                const productData = {
                    id: button.dataset.id,
                    name: button.dataset.name,
                    price: parseFloat(button.dataset.price),
                    image: button.dataset.image
                };
                
                this.trackEvent('add_to_cart_clicked', productData);
            }
        });
    }

    setupProductTimeTracking() {
        // Tracking de tiempo dedicado a cada producto
        const productElements = document.querySelectorAll('.producto-item, .product-card, [data-product-id]');
        const productTimes = new Map();
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const productId = this.getProductId(entry.target);
                if (!productId) return;
                
                if (entry.isIntersecting) {
                    // Producto entró en viewport
                    productTimes.set(productId, Date.now());
                } else {
                    // Producto salió del viewport
                    const startTime = productTimes.get(productId);
                    if (startTime) {
                        const timeSpent = Date.now() - startTime;
                        if (timeSpent > 1000) { // Solo trackear si estuvo más de 1 segundo
                            this.trackEvent('product_time_spent', {
                                product_id: productId,
                                time_spent_ms: timeSpent
                            });
                        }
                        productTimes.delete(productId);
                    }
                }
            });
        });
        
        productElements.forEach(element => observer.observe(element));
    }

    setupProductAbandonmentTracking() {
        // Detectar cuando el usuario abandona una página de producto
        if (window.location.pathname.includes('producto')) {
            let startTime = Date.now();
            let maxScroll = 0;
            
            window.addEventListener('scroll', () => {
                const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
                maxScroll = Math.max(maxScroll, scrollPercent);
            });
            
            window.addEventListener('beforeunload', () => {
                const timeOnProduct = Date.now() - startTime;
                const productId = this.getCurrentProductId();
                
                if (productId && timeOnProduct > 5000) { // Más de 5 segundos
                    this.trackEvent('product_page_abandoned', {
                        product_id: productId,
                        time_spent: timeOnProduct,
                        max_scroll: Math.round(maxScroll),
                        had_cart_interaction: this.cart.length > 0
                    });
                }
            });
        }
    }

    extractProductData(element) {
        // Extraer datos del producto desde el elemento DOM
        const productId = this.getProductId(element);
        if (!productId) return null;
        
        // Intentar extraer datos de data-attributes
        const name = element.dataset.name || 
                    element.querySelector('.product-name, .producto-nombre')?.textContent?.trim() ||
                    element.querySelector('h3, h4, h5')?.textContent?.trim();
        
        const priceElement = element.querySelector('.price, .precio, [data-price]');
        const price = priceElement ? 
                     parseFloat(priceElement.dataset.price) || 
                     parseFloat(priceElement.textContent.replace(/[^\d.]/g, '')) : 0;
        
        const image = element.querySelector('img')?.src ||
                     element.dataset.image;
        
        return {
            id: productId,
            name: name || 'Producto sin nombre',
            price: price,
            image: image,
            category: element.dataset.category || 'general'
        };
    }

    getProductId(element) {
        return element.dataset.productId || 
               element.dataset.id || 
               element.getAttribute('data-product-id') ||
               element.getAttribute('data-id');
    }

    getCurrentProductId() {
        // Intentar extraer el ID del producto desde la URL o elementos de la página
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('id') || 
               document.querySelector('[data-current-product-id]')?.dataset.currentProductId ||
               document.querySelector('.product-detail')?.dataset.productId;
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
