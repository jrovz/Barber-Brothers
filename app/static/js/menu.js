/**
 * Script para el menú móvil
 * Versión: 2.0 - Simplificado y mejorado
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Menu.js: Script cargado correctamente');
    
    // Elementos del DOM necesarios para el menú
    const menuToggle = document.getElementById('menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    // Crear overlay específicamente para el menú
    const menuOverlay = document.createElement('div');
    menuOverlay.id = 'menu-overlay';
    menuOverlay.className = 'menu-overlay';
    document.body.appendChild(menuOverlay);
    
    // Verificar que los elementos principales existan
    if (!menuToggle || !mobileMenu) {
        console.error('Menu.js: Error - No se encontraron los elementos necesarios del menú');
        console.error('menuToggle existe:', !!menuToggle);
        console.error('mobileMenu existe:', !!mobileMenu);
        return;
    }
    
    console.log('Menu.js: Elementos del menú encontrados correctamente');
    
    // Función para verificar si el carrito está abierto
    function isCartOpen() {
        const cartPanel = document.getElementById('cart-panel');
        return cartPanel && cartPanel.classList.contains('open');
    }
    
    // Función para abrir el menú
    function openMenu() {
        console.log('Menu.js: Intentando abrir menú...');
        mobileMenu.classList.add('open');
        menuToggle.classList.add('open');
        menuOverlay.classList.add('open');
        document.body.style.overflow = 'hidden';
        menuToggle.setAttribute('aria-expanded', 'true');
        console.log('Menu.js: Menú abierto');
        
        // Forzar repintado del DOM para asegurar que los cambios se aplican
        void mobileMenu.offsetWidth;
    }
    
    // Función para cerrar el menú
    function closeMenu() {
        console.log('Menu.js: Cerrando menú...');
        mobileMenu.classList.remove('open');
        menuToggle.classList.remove('open');
        menuOverlay.classList.remove('open');
        
        // Solo restaurar el scroll si el carrito no está abierto
        if (!isCartOpen()) {
            document.body.style.overflow = '';
        }
        
        menuToggle.setAttribute('aria-expanded', 'false');
        console.log('Menu.js: Menú cerrado');
    }
    
    // Event listener principal para el botón hamburguesa
    menuToggle.addEventListener('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        console.log('Menu.js: Click en botón hamburguesa detectado');
        
        // Toggle del menú
        if (mobileMenu.classList.contains('open')) {
            closeMenu();
        } else {
            openMenu();
        }
    });
    
    // Event listener para cerrar al hacer clic en el overlay
    menuOverlay.addEventListener('click', function() {
        if (mobileMenu.classList.contains('open')) {
            closeMenu();
        }
    });
    
    // Event listener para cerrar con ESC
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && mobileMenu.classList.contains('open')) {
            closeMenu();
        }
    });
    
    // Event listeners para los enlaces del menú
    const menuLinks = mobileMenu.querySelectorAll('a');
    menuLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Si es el carrito, cerrar solo el menú pero no el carrito
            if (this.id === 'cart-button-mobile' || this.closest('.cart-icon')) {
                mobileMenu.classList.remove('open');
                menuToggle.classList.remove('open');
                menuToggle.setAttribute('aria-expanded', 'false');
            } else {
                closeMenu();
            }
        });
    });
    
    // Exponer funciones para el carrito
    window.menuJS = {
        closeMenuForCart: function() {
            mobileMenu.classList.remove('open');
            menuToggle.classList.remove('open');
            menuToggle.setAttribute('aria-expanded', 'false');
        },
        isCartOpen: isCartOpen
    };
    
    // Forzar el estado inicial correcto
    menuToggle.setAttribute('aria-expanded', 'false');
    console.log('Menu.js: Inicialización completa');
});