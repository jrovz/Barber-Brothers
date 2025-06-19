/**
 * Admin Mobile Utilities
 * Funcionalidades específicas para el panel de administración en móvil
 */

document.addEventListener('DOMContentLoaded', function() {
    // Detectar si estamos en móvil
    function isMobile() {
        return window.innerWidth <= 768;
    }
    
    // Convertir tablas a cards en móvil
    function convertTablesToCards() {
        if (!isMobile()) return;
        
        const tables = document.querySelectorAll('.data-table');
        
        tables.forEach(table => {
            // Skip if already converted
            if (table.classList.contains('mobile-converted')) return;
            
            const container = table.closest('.data-table-container');
            if (!container) return;
            
            // Create mobile cards container
            const cardsContainer = document.createElement('div');
            cardsContainer.className = 'mobile-cards-container';
            cardsContainer.style.display = 'none';
            
            // Get headers
            const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
            
            // Process each row
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                
                // Create mobile card
                const card = document.createElement('div');
                card.className = 'mobile-card';
                
                // Card header (usually first column)
                const cardHeader = document.createElement('div');
                cardHeader.className = 'mobile-card-header';
                
                const cardTitle = document.createElement('div');
                cardTitle.className = 'mobile-card-title';
                cardTitle.textContent = cells[0]?.textContent.trim() || 'Sin título';
                
                // Card actions (usually last column)
                const actionsCell = cells[cells.length - 1];
                const cardActions = document.createElement('div');
                cardActions.className = 'mobile-card-actions';
                
                if (actionsCell && actionsCell.querySelector('.actions')) {
                    const actionsContent = actionsCell.querySelector('.actions').cloneNode(true);
                    cardActions.appendChild(actionsContent);
                }
                
                cardHeader.appendChild(cardTitle);
                cardHeader.appendChild(cardActions);
                card.appendChild(cardHeader);
                
                // Card body (other columns)
                const cardBody = document.createElement('div');
                cardBody.className = 'mobile-card-body';
                
                headers.forEach((header, index) => {
                    // Skip first column (title) and last column (actions)
                    if (index === 0 || index === headers.length - 1) return;
                    
                    const cell = cells[index];
                    if (!cell) return;
                    
                    const field = document.createElement('div');
                    field.className = 'mobile-card-field';
                    
                    // Check if this should be full width
                    const cellText = cell.textContent.trim();
                    if (cellText.length > 50 || header.toLowerCase().includes('descripcion')) {
                        field.classList.add('full-width');
                    }
                    
                    const label = document.createElement('div');
                    label.className = 'mobile-card-label';
                    label.textContent = header;
                    
                    const value = document.createElement('div');
                    value.className = 'mobile-card-value';
                    
                    // Handle special content (images, badges, etc.)
                    if (cell.querySelector('img')) {
                        const img = cell.querySelector('img').cloneNode(true);
                        img.style.maxWidth = '60px';
                        img.style.height = 'auto';
                        value.appendChild(img);
                    } else if (cell.querySelector('.badge')) {
                        const badge = cell.querySelector('.badge').cloneNode(true);
                        value.appendChild(badge);
                    } else {
                        value.textContent = cellText;
                    }
                    
                    field.appendChild(label);
                    field.appendChild(value);
                    cardBody.appendChild(field);
                });
                
                card.appendChild(cardBody);
                cardsContainer.appendChild(card);
            });
            
            // Insert cards container after table
            container.appendChild(cardsContainer);
            
            // Mark as converted
            table.classList.add('mobile-converted');
            
            // Show appropriate view
            updateTableView();
        });
    }
    
    // Update table/card view based on screen size
    function updateTableView() {
        const tables = document.querySelectorAll('.data-table');
        const cardsContainers = document.querySelectorAll('.mobile-cards-container');
        
        if (isMobile()) {
            tables.forEach(table => {
                if (table.classList.contains('mobile-converted')) {
                    table.style.display = 'none';
                }
            });
            cardsContainers.forEach(container => {
                container.style.display = 'block';
            });
        } else {
            tables.forEach(table => table.style.display = 'table');
            cardsContainers.forEach(container => {
                container.style.display = 'none';
            });
        }
    }
    
    // Enhance form interactions for mobile
    function enhanceMobileForms() {
        if (!isMobile()) return;
        
        // Add better focus states
        const inputs = document.querySelectorAll('.form-input, select.form-select');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
            });
        });
        
        // Improve select dropdowns
        const selects = document.querySelectorAll('select.form-select');
        selects.forEach(select => {
            select.addEventListener('change', function() {
                this.classList.add('has-value');
            });
            
            if (select.value) {
                select.classList.add('has-value');
            }
        });
    }
    
    // Mobile-specific button enhancements
    function enhanceMobileButtons() {
        if (!isMobile()) return;
        
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            // Add ripple effect for better feedback
            button.addEventListener('touchstart', function(e) {
                this.classList.add('btn-pressed');
            });
            
            button.addEventListener('touchend', function(e) {
                setTimeout(() => {
                    this.classList.remove('btn-pressed');
                }, 150);
            });
        });
    }
    
    // Handle orientation changes
    function handleOrientationChange() {
        setTimeout(() => {
            updateTableView();
            if (window.innerWidth > 768) {
                // Close mobile menu if open
                const sidebar = document.getElementById('admin-sidebar');
                const overlay = document.getElementById('mobile-overlay');
                const toggle = document.getElementById('mobile-menu-toggle');
                
                if (sidebar && sidebar.classList.contains('mobile-active')) {
                    sidebar.classList.remove('mobile-active');
                    overlay.classList.remove('active');
                    overlay.style.display = 'none';
                    toggle.classList.remove('open');
                    toggle.innerHTML = '☰';
                    document.body.style.overflow = '';
                }
            }
        }, 100);
    }
    
    // Initialize mobile features
    function initMobileFeatures() {
        convertTablesToCards();
        enhanceMobileForms();
        enhanceMobileButtons();
        updateTableView();
    }
    
    // Event listeners
    window.addEventListener('resize', handleOrientationChange);
    window.addEventListener('orientationchange', handleOrientationChange);
    
    // Initialize on load
    initMobileFeatures();
    
    // Re-initialize when new content is added (for dynamic content)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                setTimeout(initMobileFeatures, 100);
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// Utility functions for other scripts
window.AdminMobile = {
    isMobile: function() {
        return window.innerWidth <= 768;
    },
    
    showToast: function(message, type = 'info') {
        if (!this.isMobile()) return;
        
        const toast = document.createElement('div');
        toast.className = `mobile-toast mobile-toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 5rem;
            left: 50%;
            transform: translateX(-50%);
            background: var(--color-bg-dark);
            color: var(--color-text-primary);
            padding: 1rem 1.5rem;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            opacity: 0;
            transition: opacity 0.3s ease;
            max-width: 90%;
            text-align: center;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.style.opacity = '1', 10);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }
};

// CSS for mobile enhancements
const mobileCSS = `
.btn-pressed {
    transform: scale(0.98) !important;
    opacity: 0.8 !important;
}

.form-group.focused .form-label {
    color: var(--color-primary) !important;
}

select.form-select.has-value {
    color: var(--color-text-primary) !important;
}

@media (max-width: 768px) {
    .mobile-toast {
        font-size: 0.9rem !important;
    }
}
`;

// Inject mobile CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = mobileCSS;
document.head.appendChild(styleSheet); 