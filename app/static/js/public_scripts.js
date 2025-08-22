document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM (asegúrate que los IDs existan en todas las páginas donde se use este script)
    const cartButton = document.getElementById('cart-button');
    const cartPanel = document.getElementById('cart-panel');
    const cartOverlay = document.getElementById('cart-overlay');
    const closeCart = document.getElementById('close-cart');
    const cartItems = document.getElementById('cart-items');
    const cartCount = document.querySelector('.cart-count'); // Usar querySelector por si acaso
    const cartTotal = document.getElementById('cart-total');
    
    // Carrito de compras (desde localStorage)
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    
    // Actualizar contador del icono del carrito
    function updateCartCount() {
        if (cartCount) { // Verificar si el elemento existe
            const count = cart.reduce((total, item) => total + item.quantity, 0);
            cartCount.textContent = count;
        }
    }
    
    // Calcular total del carrito
    function calculateTotal() {
        if (cartTotal) { // Verificar si el elemento existe
            const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            cartTotal.textContent = `€${total.toFixed(2)}`;
        }
    }
    
    // Renderizar los productos en el panel del carrito
    function renderCart() {
        if (!cartItems) return; // Salir si el contenedor no existe

        if (cart.length === 0) {
            cartItems.innerHTML = '<div class="empty-cart">Tu carrito está vacío</div>';
        } else {
            cartItems.innerHTML = cart.map(item => `
                <div class="cart-item" data-id="${item.id}">
                    <img src="${item.image || '/static/placeholder.png'}" alt="${item.name}" class="cart-item-img"> {/* Añadir placeholder si no hay imagen */}
                    <div class="cart-item-details">
                        <div class="cart-item-name">${item.name}</div>
                        <div class="cart-item-price">€${item.price.toFixed(2)}</div>
                        <div class="cart-item-quantity">
                            <button class="quantity-btn decrease" aria-label="Disminuir cantidad">-</button>
                            <input type="text" class="quantity-input" value="${item.quantity}" readonly aria-label="Cantidad">
                            <button class="quantity-btn increase" aria-label="Aumentar cantidad">+</button>
                        </div>
                    </div>
                    <button class="remove-item" aria-label="Eliminar producto">&times;</button>
                </div>
            `).join('');
            
            // Añadir event listeners DESPUÉS de renderizar los items
            addCartItemListeners(); 
        }
    }

    // Función para añadir listeners a los botones DENTRO del carrito
    function addCartItemListeners() {
        if (!cartItems) return;

        cartItems.querySelectorAll('.increase').forEach(button => {
            button.addEventListener('click', function() {
                const id = this.closest('.cart-item').dataset.id;
                const item = cart.find(item => item.id === id);
                if (item) {
                    item.quantity++;
                    updateCart();
                }
            });
        });
        
        cartItems.querySelectorAll('.decrease').forEach(button => {
            button.addEventListener('click', function() {
                const id = this.closest('.cart-item').dataset.id;
                const item = cart.find(item => item.id === id);
                if (item && item.quantity > 1) {
                    item.quantity--;
                    updateCart();
                } else if (item && item.quantity === 1) {
                    // Opcional: eliminar si baja de 1
                    cart = cart.filter(item => item.id !== id);
                    updateCart();
                }
            });
        });
        
        cartItems.querySelectorAll('.remove-item').forEach(button => {
            button.addEventListener('click', function() {
                const id = this.closest('.cart-item').dataset.id;
                cart = cart.filter(item => item.id !== id);
                updateCart();
            });
        });
    }
    
    // Actualizar el carrito (localStorage y UI)
    function updateCart() {
        localStorage.setItem('cart', JSON.stringify(cart));
        renderCart(); // Re-renderizar para actualizar items y listeners
        updateCartCount();
        calculateTotal();
    }
    
    // Abrir/cerrar panel del carrito (solo si los elementos existen)
    if (cartButton && cartPanel && cartOverlay && closeCart) {
        cartButton.addEventListener('click', function(e) {
            e.preventDefault();
            cartPanel.classList.add('open');
            cartOverlay.classList.add('open');
            renderCart(); // Renderizar al abrir
            calculateTotal();
        });
        
        closeCart.addEventListener('click', function() {
            cartPanel.classList.remove('open');
            cartOverlay.classList.remove('open');
        });
        
        cartOverlay.addEventListener('click', function() {
            cartPanel.classList.remove('open');
            cartOverlay.classList.remove('open');
        });
    }
    
    // Añadir productos al carrito (listener para botones '.add-to-cart')
    // Este listener solo funcionará si existen botones con esa clase en la página
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            // Asegurarse que los data attributes existen
            const id = this.dataset.id;
            const name = this.dataset.name;
            const price = parseFloat(this.dataset.price);
            const image = this.dataset.image; // Puede ser undefined si no está

            if (!id || !name || isNaN(price)) {
                console.error("Datos del producto incompletos:", this.dataset);
                return; // No añadir si faltan datos esenciales
            }
            
            // Comprobar si el producto ya está en el carrito
            const existingItem = cart.find(item => item.id === id);
            
            if (existingItem) {
                existingItem.quantity++;
            } else {
                cart.push({
                    id,
                    name,
                    price,
                    image: image || null, // Guardar null si no hay imagen
                    quantity: 1
                });
            }
            
            // Efecto visual de confirmación (opcional)
            const originalText = this.textContent;
            this.textContent = '¡Añadido!';
            // Podrías añadir una clase temporal para estilizarlo
            this.disabled = true; // Deshabilitar brevemente
            
            setTimeout(() => {
                this.textContent = originalText;
                this.disabled = false;
            }, 1500);
            
            updateCart(); // Actualizar todo (localStorage, UI)
        });
    });
    
    // Inicializar estado del carrito al cargar la página
    updateCartCount();
    // Opcional: Renderizar carrito si el panel está abierto por defecto (poco común)
    // if (cartPanel && cartPanel.classList.contains('open')) {
    //    renderCart();
    //    calculateTotal();
    // }

    // --- SLIDER LOGIC REMOVED - Handled in Home.html to avoid conflicts ---

    // Slider Image Preloading and Instagram Support
    function optimizeSliderPerformance() {
        const slides = document.querySelectorAll('.slide');
        const slideBackgrounds = document.querySelectorAll('.slide-bg');
        
        if (!slides.length) return;
        
        console.log('Optimizing slider performance...');
        
        // Preload slide background images for smoother transitions
        slideBackgrounds.forEach((slideBg, index) => {
            const bgImageUrl = slideBg.style.backgroundImage;
            if (bgImageUrl) {
                const imageUrl = bgImageUrl.replace(/url\(['"]?(.*?)['"]?\)/, '$1');
                if (imageUrl && imageUrl !== 'none') {
                    const img = new Image();
                    img.onload = function() {
                        console.log('Slide ' + (index + 1) + ' image preloaded');
                        slideBg.classList.add('image-loaded');
                    };
                    img.onerror = function() {
                        console.warn('Failed to preload slide ' + (index + 1) + ' image');
                    };
                    img.src = imageUrl;
                }
            }
        });
        
        // Handle Instagram embed reprocessing when slides become active
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const slide = mutation.target;
                    if (slide.classList.contains('active') && slide.classList.contains('instagram-embed-slide')) {
                        // Reinitialize Instagram embed if needed
                        if (window.instgrm && window.instgrm.Embeds) {
                            setTimeout(function() {
                                window.instgrm.Embeds.process();
                            }, 100);
                        }
                    }
                }
            });
        });
        
        // Observe all slides for class changes
        slides.forEach(function(slide) {
            observer.observe(slide, { attributes: true, attributeFilter: ['class'] });
        });
        
        // Force Instagram embeds processing on initial load
        if (window.instgrm && window.instgrm.Embeds) {
            setTimeout(function() {
                window.instgrm.Embeds.process();
            }, 500);
        }
        
        // Add intersection observer for performance optimization
        if ('IntersectionObserver' in window) {
            const sliderObserver = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        // Slider is visible, ensure smooth performance
                        entry.target.style.willChange = 'transform';
                    } else {
                        // Slider not visible, reduce performance overhead
                        entry.target.style.willChange = 'auto';
                    }
                });
            }, { threshold: 0.1 });
            
            const heroSlider = document.querySelector('.hero-slider');
            if (heroSlider) {
                sliderObserver.observe(heroSlider);
            }
        }
    }
    
    // Initialize slider optimizations after DOM is ready
    if (document.querySelector('.hero-slider')) {
        optimizeSliderPerformance();
    }

    // Gestión del menú móvil - DESHABILITADO para evitar conflictos con menu.js
    // El menú móvil ahora es manejado exclusivamente por menu.js
    console.log('public_scripts.js: Menú móvil deshabilitado para evitar conflictos con menu.js');

}); // Fin del DOMContentLoaded