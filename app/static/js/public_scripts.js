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

    // --- Añadir aquí cualquier otro JS específico de Home.html si es necesario ---
    // Por ejemplo, la lógica del slider:
    const sliderContainer = document.querySelector('.slider-container');
    const slides = document.querySelectorAll('.slide');
    const prevArrow = document.querySelector('.prev-arrow');
    const nextArrow = document.querySelector('.next-arrow');
    const dots = document.querySelectorAll('.dot');
    
    let currentIndex = 0;
    let slideInterval;

    function updateSlider() {
        if (!sliderContainer || !slides.length) return; // Salir si no hay slider
        sliderContainer.style.transform = `translateX(-${currentIndex * 100}%)`;
        
        // Actualizar dots activos
        if (dots.length) {
            dots.forEach((dot, index) => {
                dot.classList.toggle('active', index === currentIndex);
            });
        }
    }

    function nextSlide() {
        if (!slides.length) return;
        currentIndex = (currentIndex + 1) % slides.length;
        updateSlider();
    }

    function prevSlide() {
        if (!slides.length) return;
        currentIndex = (currentIndex - 1 + slides.length) % slides.length;
        updateSlider();
    }

    function goToSlide(index) {
        if (!slides.length) return;
        currentIndex = index;
        updateSlider();
        resetInterval(); // Reiniciar intervalo al hacer clic en un dot
    }

    function startInterval() {
        if (!slides.length) return;
        // Limpiar intervalo existente por si acaso
        clearInterval(slideInterval); 
        slideInterval = setInterval(nextSlide, 5000); // Cambiar cada 5 segundos
    }

    function resetInterval() {
        if (!slides.length) return;
        clearInterval(slideInterval);
        startInterval();
    }

    // Añadir listeners para controles del slider (solo si existen)
    if (nextArrow) {
        nextArrow.addEventListener('click', () => {
            nextSlide();
            resetInterval();
        });
    }
    if (prevArrow) {
        prevArrow.addEventListener('click', () => {
            prevSlide();
            resetInterval();
        });
    }
    if (dots.length) {
        dots.forEach(dot => {
            dot.addEventListener('click', () => {
                goToSlide(parseInt(dot.dataset.slide));
            });
        });
    }

    // Iniciar slider si existe
    if (sliderContainer && slides.length > 1) {
        updateSlider(); // Estado inicial
        startInterval(); // Iniciar cambio automático
    }


    // Gestión del menú móvil
    const menuToggle = document.getElementById('menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');

    if (menuToggle && mobileMenu) {
        console.log('Menú toggle y mobile menu encontrados'); // Debug
        
        // Asegurarse que el menú comienza cerrado
        mobileMenu.classList.remove('open');
        menuToggle.classList.remove('open');
        
        menuToggle.addEventListener('click', function(e) {
            console.log('Botón hamburguesa clickeado'); // Debug
            e.preventDefault();
            
            // Toggle de estado
            const isOpen = mobileMenu.classList.contains('open');
            
            // Cambiar al estado opuesto
            if (isOpen) {
                // Cerrar menú
                mobileMenu.classList.remove('open');
                menuToggle.classList.remove('open');
                menuToggle.setAttribute('aria-expanded', 'false');
                
                // Manejar overlay solo si el carrito no está abierto
                const cartPanel = document.getElementById('cart-panel');
                if (!cartPanel || !cartPanel.classList.contains('open')) {
                    if (cartOverlay) cartOverlay.classList.remove('open');
                    document.body.style.overflow = '';
                }
            } else {
                // Abrir menú
                mobileMenu.classList.add('open');
                menuToggle.classList.add('open');
                menuToggle.setAttribute('aria-expanded', 'true');
                
                // Activar overlay
                if (cartOverlay) cartOverlay.classList.add('open');
                document.body.style.overflow = 'hidden';
            }
        });
    }
    
    // Opcional: Cerrar el menú si se hace clic en un enlace dentro de él (para SPAs o si los enlaces son anclas)
    if (mobileMenu) {
        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function() {
                // No cerrar si es el botón del carrito, ya que ese abre otro panel
                if (this.parentElement.classList.contains('cart-icon')) {
                    // La lógica del carrito se encargará de abrir el panel del carrito
                    // Pero sí queremos cerrar el menú de navegación
                    mobileMenu.classList.remove('open');
                    menuToggle.classList.remove('open');
                    menuToggle.setAttribute('aria-expanded', 'false');
                    // Restaurar scroll si el panel del carrito no está abierto
                    const cartPanel = document.getElementById('cart-panel');
                     if (cartOverlay && (!cartPanel || !cartPanel.classList.contains('open'))) {
                        cartOverlay.classList.remove('open');
                    }
                    if (!cartPanel || !cartPanel.classList.contains('open')) {
                        document.body.style.overflow = '';
                    }
                    return; 
                }

                // Para otros enlaces, cerrar el menú
                mobileMenu.classList.remove('open');
                menuToggle.classList.remove('open');
                menuToggle.setAttribute('aria-expanded', 'false');
                 if (cartOverlay) cartOverlay.classList.remove('open');
                document.body.style.overflow = '';
            });
        });
    }
    
    // Opcional: Cerrar menú si se hace clic en el overlay (si el overlay se usa para el menú)
    // Esta lógica debe coexistir con la del carrito.
    // Si el overlay es compartido, asegúrate de que solo cierre el menú si el carrito no está abierto.
    if (cartOverlay && mobileMenu && menuToggle) {
        cartOverlay.addEventListener('click', function() {
            console.log('Overlay clicked'); // Debug
            
            // Comprobar si el carrito está abierto
            const cartPanel = document.getElementById('cart-panel');
            if (cartPanel && cartPanel.classList.contains('open')) {
                cartPanel.classList.remove('open');
            }
            
            // Comprobar si el menú móvil está abierto
            if (mobileMenu && mobileMenu.classList.contains('open')) {
                mobileMenu.classList.remove('open');
                if (menuToggle) menuToggle.classList.remove('open');
            }
            
            // Cerrar overlay y restaurar scroll
            cartOverlay.classList.remove('open');
            document.body.style.overflow = '';
        });
    }

}); // Fin del DOMContentLoaded