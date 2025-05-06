document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const cartButton = document.getElementById('cart-button');
    const cartPanel = document.getElementById('cart-panel');
    const cartOverlay = document.getElementById('cart-overlay');
    const closeCart = document.getElementById('close-cart');
    const cartItems = document.getElementById('cart-items');
    const cartCount = document.querySelector('.cart-count');
    const cartTotal = document.getElementById('cart-total');
    const checkoutButton = document.querySelector('.checkout-button'); // Asegúrate de que este botón exista en tu HTML

    // Carrito de compras
    let cart = JSON.parse(localStorage.getItem('cart')) || [];

    // Formatear precio en formato colombiano
    function formatCOP(price) {
        // Asegurarse de que el precio sea un número
        const numericPrice = Number(price);
        if (isNaN(numericPrice)) {
            console.error("Invalid price for formatting:", price);
            return 'COP 0'; // O algún valor predeterminado
        }
        // Usar toLocaleString para formato local, especificando 'es-CO' para Colombia
        // y style: 'currency' para formato de moneda.
        return numericPrice.toLocaleString('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 });
    }


    // Actualizar contador del carrito
    function updateCartCount() {
        const count = cart.reduce((total, item) => total + item.quantity, 0);
        if (cartCount) {
            cartCount.textContent = count;
        }
    }

    // Calcular total del carrito
    function calculateTotal() {
        const total = cart.reduce((sum, item) => sum + (Number(item.price) * item.quantity), 0);
         if (cartTotal) {
            cartTotal.textContent = formatCOP(total);
        }
    }

    // Renderizar los productos en el carrito
    function renderCart() {
        if (!cartItems) return; // Salir si el contenedor de items no existe

        if (cart.length === 0) {
            cartItems.innerHTML = '<div class="empty-cart">Tu carrito está vacío</div>';
            if (checkoutButton) checkoutButton.disabled = true; // Deshabilitar botón si el carrito está vacío
            return;
        }

        cartItems.innerHTML = cart.map(item => `
            <div class="cart-item" data-id="${item.id}">
                <img src="${item.image}" alt="${item.name}" class="cart-item-img">
                <div class="cart-item-details">
                    <div class="cart-item-name">${item.name}</div>
                    <div class="cart-item-price">${formatCOP(item.price)}</div>
                    <div class="cart-item-quantity">
                        <button class="quantity-btn decrease" data-id="${item.id}">-</button>
                        <input type="text" class="quantity-input" value="${item.quantity}" readonly>
                        <button class="quantity-btn increase" data-id="${item.id}">+</button>
                    </div>
                </div>
                <button class="remove-item" data-id="${item.id}">&times;</button>
            </div>
        `).join('');

        if (checkoutButton) checkoutButton.disabled = false; // Habilitar botón si hay items

        // Añadir event listeners después de renderizar
        addCartItemEventListeners();
    }

    // Añadir event listeners a los elementos del carrito
    function addCartItemEventListeners() {
        document.querySelectorAll('.increase').forEach(button => {
            button.removeEventListener('click', handleIncreaseQuantity); // Prevenir duplicados
            button.addEventListener('click', handleIncreaseQuantity);
        });

        document.querySelectorAll('.decrease').forEach(button => {
            button.removeEventListener('click', handleDecreaseQuantity); // Prevenir duplicados
            button.addEventListener('click', handleDecreaseQuantity);
        });

        document.querySelectorAll('.remove-item').forEach(button => {
            button.removeEventListener('click', handleRemoveItem); // Prevenir duplicados
            button.addEventListener('click', handleRemoveItem);
        });
    }

    // Manejadores de eventos para botones del carrito
    function handleIncreaseQuantity() {
        const id = this.dataset.id;
        const item = cart.find(item => item.id === id);
        if (item) {
            item.quantity++;
            updateCart();
        }
    }

    function handleDecreaseQuantity() {
        const id = this.dataset.id;
        const item = cart.find(item => item.id === id);
        if (item && item.quantity > 1) {
            item.quantity--;
            updateCart();
        } else if (item && item.quantity === 1) {
            // Opcional: remover si la cantidad llega a 0, o simplemente no hacer nada
             cart = cart.filter(item => item.id !== id);
             updateCart();
        }
    }

    function handleRemoveItem() {
        const id = this.dataset.id;
        cart = cart.filter(item => item.id !== id);
        updateCart();
    }


    // Actualizar el carrito y localStorage
    function updateCart() {
        localStorage.setItem('cart', JSON.stringify(cart));
        renderCart();
        updateCartCount();
        calculateTotal();
    }

    // Abrir panel del carrito
    function openCartPanel() {
        if (cartPanel && cartOverlay) {
            cartPanel.classList.add('open');
            cartOverlay.classList.add('open');
            renderCart();
            calculateTotal();
        }
    }

    // Cerrar panel del carrito
    function closeCartPanel() {
         if (cartPanel && cartOverlay) {
            cartPanel.classList.remove('open');
            cartOverlay.classList.remove('open');
        }
    }

    // Event listeners principales
    if (cartButton) {
        cartButton.addEventListener('click', function(e) {
            e.preventDefault();
            openCartPanel();
        });
    }

    if (closeCart) {
        closeCart.addEventListener('click', closeCartPanel);
    }

    if (cartOverlay) {
        cartOverlay.addEventListener('click', closeCartPanel);
    }

    // Añadir productos al carrito (listener para botones .add-to-cart)
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.dataset.id;
            const name = this.dataset.name;
            const price = parseFloat(this.dataset.price);
            const image = this.dataset.image;

            if (!id || !name || isNaN(price) || !image) {
                console.error('Product data missing or invalid:', this.dataset);
                return; // No añadir si faltan datos
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
                    image,
                    quantity: 1
                });
            }

            // Efecto visual de confirmación
            const originalText = this.textContent;
            this.textContent = '¡Añadido!';
            this.classList.add('added');

            setTimeout(() => {
                // Solo restaurar si el botón todavía existe y no ha sido reemplazado
                const currentButton = document.querySelector(`.add-to-cart[data-id="${id}"]`);
                if (currentButton) {
                    currentButton.textContent = originalText;
                    currentButton.classList.remove('added');
                }
            }, 1500);

            updateCart();
            openCartPanel(); // Opcional: abrir el carrito al añadir un item
        });
    });

    // Inicializar estado del carrito al cargar la página
    updateCartCount();
    // Si el panel del carrito debe mostrarse inicialmente (p.ej., si ya hay items), descomentar:
    // if (cart.length > 0) {
    //     renderCart();
    //     calculateTotal();
    // }

    // Listener para el botón de finalizar compra (ejemplo básico)
    if (checkoutButton) {
        checkoutButton.addEventListener('click', () => {
            if (cart.length > 0) {
                // Aquí iría la lógica para procesar el pago o redirigir a una página de checkout
                console.log('Proceeding to checkout with:', cart);
                alert('Redirigiendo a la página de finalización de compra...');
                // window.location.href = '/checkout'; // Descomentar para redirigir
                 // Vaciar carrito después de "finalizar" (simulado)
                // cart = [];
                // updateCart();
                // closeCartPanel();
            } else {
                alert('Tu carrito está vacío.');
            }
        });
    }

});
