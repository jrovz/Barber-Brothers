document.addEventListener('DOMContentLoaded', function() {
    console.log('Menu script loaded');
    
    const menuToggle = document.getElementById('menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    // Añadir log de comprobación
    console.log('Menu toggle found:', !!menuToggle);
    console.log('Mobile menu found:', !!mobileMenu);
    
    // Crear un overlay específico para el menú móvil
    let menuOverlay = document.getElementById('menu-overlay');
    if (!menuOverlay) {
        menuOverlay = document.createElement('div');
        menuOverlay.id = 'menu-overlay';
        menuOverlay.className = 'menu-overlay';
        document.body.appendChild(menuOverlay);
    }
    
    // Agregar botón de cierre al menú móvil si no existe
    if (mobileMenu && !mobileMenu.querySelector('.close-menu')) {
        const closeMenuButton = document.createElement('button');
        closeMenuButton.className = 'close-menu';
        closeMenuButton.innerHTML = '&times;';
        closeMenuButton.setAttribute('aria-label', 'Cerrar menú');
        mobileMenu.prepend(closeMenuButton);
        
        // Agregar evento para cerrar el menú
        closeMenuButton.addEventListener('click', function() {
            closeMobileMenu();
        });
    }
    
    // Función para verificar si el carrito está abierto
    function isCartOpen() {
        const cartPanel = document.getElementById('cart-panel');
        return cartPanel && cartPanel.classList.contains('open');
    }
    
    // Función para abrir el menú móvil
    function openMobileMenu() {
        // No abrir el menú si el carrito está abierto
        if (isCartOpen()) return;
        
        mobileMenu.classList.add('open');
        menuToggle.classList.add('open');
        menuOverlay.classList.add('open');
        document.body.classList.add('menu-open'); // Impide el scroll en el body
    }
    
    // Función para cerrar el menú móvil
    function closeMobileMenu() {
        mobileMenu.classList.remove('open');
        menuToggle.classList.remove('open');
        menuOverlay.classList.remove('open');
        
        // Solo restaurar el scroll si el carrito no está abierto
        if (!isCartOpen()) {
            document.body.classList.remove('menu-open');
        }
    }
      if (menuToggle && mobileMenu) {
        // Alternar el menú al hacer clic en el botón
        menuToggle.addEventListener('click', function(e) {
            e.preventDefault(); // Prevenir comportamiento predeterminado
            console.log('Toggle clicked');
            
            if (mobileMenu.classList.contains('open')) {
                closeMobileMenu();
            } else {
                openMobileMenu();
            }
        });
        
        // Cerrar el menú al hacer clic en el overlay
        menuOverlay.addEventListener('click', closeMobileMenu);
        
        // Manejar enlaces dentro del menú móvil
        const menuLinks = mobileMenu.querySelectorAll('a');
        menuLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Si es el enlace del carrito, permitir que el evento de carrito se ejecute
                if (this.id === 'cart-button-mobile' || this.closest('.cart-icon')) {
                    // Solo cerramos el menú pero no prevenimos la acción predeterminada
                    closeMobileMenu();
                } else {
                    // Para los demás enlaces, cerramos el menú
                    closeMobileMenu();
                }
            });
        });
    }
});