// Crear un archivo nuevo llamado menu.js con este contenido

document.addEventListener('DOMContentLoaded', function() {
    console.log('Menu script loaded');
    
    const menuToggle = document.getElementById('menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    // Añadir log de comprobación
    console.log('Menu toggle found:', !!menuToggle);
    console.log('Mobile menu found:', !!mobileMenu);
    
    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', function() {
            console.log('Toggle clicked');
            mobileMenu.classList.toggle('open');
            menuToggle.classList.toggle('open');
            
            const overlay = document.getElementById('cart-overlay');
            if (overlay) {
                overlay.classList.toggle('open');
            }
        });
    }
});