// filepath: app/static/js/admin_filters.js
/**
 * JavaScript para gestión automática de filtros en páginas de administración
 * 
 * Funcionalidades:
 * - Guardado automático de filtros utilizados
 * - Carga de filtros frecuentes
 * - Sugerencias de filtros
 * - Historial de filtros por sección
 */

class AdminFilters {
    constructor() {
        this.currentSection = this.detectSection();
        this.filterHistory = [];
        this.init();
    }

    init() {
        this.loadFilterHistory();
        this.setupFilterTracking();
        this.setupFilterSuggestions();
        this.restoreLastFilter();
        
        console.log(`🔍 Admin Filters initialized for section: ${this.currentSection}`);
    }

    // ==========================================
    // DETECCIÓN DE SECCIÓN
    // ==========================================

    detectSection() {
        const path = window.location.pathname;
        
        if (path.includes('productos')) return 'productos';
        if (path.includes('barberos')) return 'barberos';
        if (path.includes('servicios')) return 'servicios';
        if (path.includes('citas')) return 'citas';
        if (path.includes('clientes')) return 'clientes';
        if (path.includes('categorias')) return 'categorias';
        if (path.includes('sliders')) return 'sliders';
        
        return 'general';
    }

    // ==========================================
    // GESTIÓN DE HISTORIAL
    // ==========================================

    loadFilterHistory() {
        try {
            const stored = localStorage.getItem('admin_filter_history');
            if (stored) {
                const allHistory = JSON.parse(stored);
                this.filterHistory = allHistory[this.currentSection] || [];
            }
        } catch (error) {
            console.error('Error loading filter history:', error);
        }
    }

    saveFilterHistory() {
        try {
            const stored = localStorage.getItem('admin_filter_history') || '{}';
            const allHistory = JSON.parse(stored);
            allHistory[this.currentSection] = this.filterHistory;
            localStorage.setItem('admin_filter_history', JSON.stringify(allHistory));
        } catch (error) {
            console.error('Error saving filter history:', error);
        }
    }

    addToHistory(filterData) {
        // Evitar duplicados
        const existing = this.filterHistory.findIndex(item => 
            this.filtersMatch(item, filterData)
        );
        
        if (existing !== -1) {
            // Mover al principio y actualizar contador
            const item = this.filterHistory.splice(existing, 1)[0];
            item.count = (item.count || 1) + 1;
            item.last_used = new Date().toISOString();
            this.filterHistory.unshift(item);
        } else {
            // Agregar nuevo filtro
            const newFilter = {
                ...filterData,
                count: 1,
                last_used: new Date().toISOString(),
                name: this.generateFilterName(filterData)
            };
            this.filterHistory.unshift(newFilter);
        }

        // Mantener solo los últimos 10
        this.filterHistory = this.filterHistory.slice(0, 10);
        this.saveFilterHistory();
    }

    filtersMatch(filter1, filter2) {
        const keys = ['estado', 'fecha', 'barbero_id', 'servicio_id', 'segmento', 'ordenar_por'];
        return keys.every(key => filter1[key] === filter2[key]);
    }

    generateFilterName(filterData) {
        const parts = [];
        
        if (filterData.estado) parts.push(`Estado: ${filterData.estado}`);
        if (filterData.fecha) parts.push(`Fecha: ${filterData.fecha}`);
        if (filterData.barbero_id) parts.push(`Barbero: ${filterData.barbero_id}`);
        if (filterData.servicio_id) parts.push(`Servicio: ${filterData.servicio_id}`);
        if (filterData.segmento) parts.push(`Segmento: ${filterData.segmento}`);
        if (filterData.ordenar_por) parts.push(`Orden: ${filterData.ordenar_por}`);
        
        return parts.join(', ') || 'Filtro personalizado';
    }

    // ==========================================
    // TRACKING AUTOMÁTICO
    // ==========================================

    setupFilterTracking() {
        // Rastrear envío de formularios de filtro
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (this.isFilterForm(form)) {
                this.trackFilterSubmission(form);
            }
        });

        // Rastrear cambios en selectores y campos
        document.addEventListener('change', (e) => {
            if (this.isFilterElement(e.target)) {
                this.scheduleFilterTracking();
            }
        });

        // Rastrear filtros en URL al cargar la página
        this.trackCurrentUrlFilters();
    }

    isFilterForm(form) {
        // Detectar formularios de filtro por clases o contenido
        return form.classList.contains('filter-form') || 
               form.querySelector('[name="estado"], [name="fecha"], [name="segmento"]');
    }

    isFilterElement(element) {
        const filterFields = ['estado', 'fecha', 'barbero_id', 'servicio_id', 'segmento', 'ordenar_por'];
        return filterFields.includes(element.name);
    }

    trackFilterSubmission(form) {
        const formData = new FormData(form);
        const filterData = {};
        
        for (let [key, value] of formData.entries()) {
            if (value && this.isFilterElement({name: key})) {
                filterData[key] = value;
            }
        }

        if (Object.keys(filterData).length > 0) {
            this.addToHistory(filterData);
            this.showFilterToast(`Filtro guardado: ${this.generateFilterName(filterData)}`);
        }
    }

    trackCurrentUrlFilters() {
        const urlParams = new URLSearchParams(window.location.search);
        const filterData = {};
        
        for (let [key, value] of urlParams.entries()) {
            if (value && this.isFilterElement({name: key})) {
                filterData[key] = value;
            }
        }

        if (Object.keys(filterData).length > 0) {
            this.addToHistory(filterData);
        }
    }

    scheduleFilterTracking() {
        // Debounce para evitar tracking excesivo
        clearTimeout(this.trackingTimeout);
        this.trackingTimeout = setTimeout(() => {
            this.trackCurrentFormState();
        }, 1000);
    }

    trackCurrentFormState() {
        const filterElements = document.querySelectorAll('[name="estado"], [name="fecha"], [name="barbero_id"], [name="servicio_id"], [name="segmento"], [name="ordenar_por"]');
        const filterData = {};
        
        filterElements.forEach(element => {
            if (element.value) {
                filterData[element.name] = element.value;
            }
        });

        if (Object.keys(filterData).length > 0) {
            this.addToHistory(filterData);
        }
    }

    // ==========================================
    // SUGERENCIAS DE FILTROS
    // ==========================================

    setupFilterSuggestions() {
        this.createFilterSuggestionsPanel();
        this.populateFilterSuggestions();
    }

    createFilterSuggestionsPanel() {
        // Solo crear si hay filtros en el historial
        if (this.filterHistory.length === 0) return;

        const existingPanel = document.querySelector('.filter-suggestions-panel');
        if (existingPanel) return;

        const filterContainer = document.querySelector('.filters, .filter-form');
        if (!filterContainer) return;

        const panel = document.createElement('div');
        panel.className = 'filter-suggestions-panel';
        panel.innerHTML = `
            <div class="filter-suggestions-header">
                <h4>🔍 Filtros Frecuentes</h4>
                <button class="toggle-suggestions" title="Mostrar/Ocultar">▼</button>
            </div>
            <div class="filter-suggestions-content">
                <div class="filter-suggestions-list"></div>
            </div>
        `;

        filterContainer.appendChild(panel);

        // Toggle functionality
        const toggleBtn = panel.querySelector('.toggle-suggestions');
        const content = panel.querySelector('.filter-suggestions-content');
        
        toggleBtn.addEventListener('click', () => {
            const isHidden = content.style.display === 'none';
            content.style.display = isHidden ? 'block' : 'none';
            toggleBtn.textContent = isHidden ? '▲' : '▼';
        });
    }

    populateFilterSuggestions() {
        const list = document.querySelector('.filter-suggestions-list');
        if (!list) return;

        list.innerHTML = '';

        // Mostrar los 5 filtros más usados
        const topFilters = this.filterHistory.slice(0, 5);
        
        topFilters.forEach((filter, index) => {
            const item = document.createElement('div');
            item.className = 'filter-suggestion-item';
            item.innerHTML = `
                <div class="filter-suggestion-info">
                    <span class="filter-name">${filter.name}</span>
                    <small class="filter-meta">Usado ${filter.count} vez${filter.count !== 1 ? 'es' : ''}</small>
                </div>
                <button class="apply-filter-btn" data-filter-index="${index}" title="Aplicar filtro">
                    ▶️
                </button>
            `;
            
            list.appendChild(item);
        });

        // Event listeners para aplicar filtros
        list.addEventListener('click', (e) => {
            if (e.target.classList.contains('apply-filter-btn')) {
                const index = parseInt(e.target.dataset.filterIndex);
                this.applyFilter(this.filterHistory[index]);
            }
        });
    }

    applyFilter(filter) {
        // Aplicar filtro llenando los campos del formulario
        Object.entries(filter).forEach(([key, value]) => {
            if (key !== 'count' && key !== 'last_used' && key !== 'name') {
                const element = document.querySelector(`[name="${key}"]`);
                if (element) {
                    element.value = value;
                }
            }
        });

        this.showFilterToast(`Filtro aplicado: ${filter.name}`);
        
        // Enviar formulario automáticamente si existe
        const filterForm = document.querySelector('.filter-form, form:has([name="estado"]), form:has([name="segmento"])');
        if (filterForm) {
            filterForm.submit();
        }
    }

    // ==========================================
    // RESTAURAR ÚLTIMO FILTRO
    // ==========================================

    restoreLastFilter() {
        // Solo restaurar si no hay parámetros en la URL
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.toString()) return;

        // Verificar si el usuario quiere restaurar filtros automáticamente
        const autoRestore = localStorage.getItem('admin_auto_restore_filters');
        if (autoRestore !== 'true') return;

        if (this.filterHistory.length > 0) {
            const lastFilter = this.filterHistory[0];
            this.showRestorePrompt(lastFilter);
        }
    }

    showRestorePrompt(filter) {
        const prompt = document.createElement('div');
        prompt.className = 'filter-restore-prompt';
        prompt.innerHTML = `
            <div class="restore-prompt-content">
                <span>🔍 ¿Restaurar último filtro: "${filter.name}"?</span>
                <div class="restore-prompt-actions">
                    <button class="btn btn-sm apply-last-filter">Sí</button>
                    <button class="btn btn-sm btn-outline dismiss-prompt">No</button>
                </div>
            </div>
        `;

        document.body.appendChild(prompt);

        // Auto-dismiss después de 10 segundos
        setTimeout(() => {
            if (document.body.contains(prompt)) {
                prompt.remove();
            }
        }, 10000);

        // Event listeners
        prompt.querySelector('.apply-last-filter').addEventListener('click', () => {
            this.applyFilter(filter);
            prompt.remove();
        });

        prompt.querySelector('.dismiss-prompt').addEventListener('click', () => {
            prompt.remove();
        });
    }

    // ==========================================
    // UI HELPERS
    // ==========================================

    showFilterToast(message) {
        const toast = document.createElement('div');
        toast.className = 'filter-toast';
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ==========================================
    // CONFIGURACIÓN
    // ==========================================

    static enableAutoRestore() {
        localStorage.setItem('admin_auto_restore_filters', 'true');
    }

    static disableAutoRestore() {
        localStorage.setItem('admin_auto_restore_filters', 'false');
    }

    static clearFilterHistory(section = null) {
        if (section) {
            const stored = localStorage.getItem('admin_filter_history') || '{}';
            const allHistory = JSON.parse(stored);
            delete allHistory[section];
            localStorage.setItem('admin_filter_history', JSON.stringify(allHistory));
        } else {
            localStorage.removeItem('admin_filter_history');
        }
    }
}

// ==========================================
// ESTILOS CSS INLINE
// ==========================================

const filterStyles = `
<style>
.filter-suggestions-panel {
    background: var(--color-bg-light, #f8f9fa);
    border: 1px solid var(--color-border, #ddd);
    border-radius: 6px;
    margin: 1rem 0;
    overflow: hidden;
}

.filter-suggestions-header {
    background: var(--color-bg-dark, #343a40);
    color: var(--color-text-primary, #fff);
    padding: 0.75rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.filter-suggestions-header h4 {
    margin: 0;
    font-size: 0.9rem;
}

.toggle-suggestions {
    background: none;
    border: none;
    color: var(--color-text-primary, #fff);
    cursor: pointer;
    font-size: 0.8rem;
}

.filter-suggestions-content {
    padding: 1rem;
}

.filter-suggestion-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: var(--color-bg-medium, #fff);
    border: 1px solid var(--color-border, #eee);
    border-radius: 4px;
    margin-bottom: 0.5rem;
    transition: all 0.2s ease;
}

.filter-suggestion-item:hover {
    border-color: var(--color-accent, #007bff);
    background: var(--color-bg-light, #f8f9fa);
}

.filter-suggestion-info {
    flex: 1;
}

.filter-name {
    font-weight: 500;
    color: var(--color-text-primary, #333);
}

.filter-meta {
    display: block;
    color: var(--color-text-muted, #666);
    font-size: 0.8rem;
    margin-top: 0.25rem;
}

.apply-filter-btn {
    background: var(--color-accent, #007bff);
    border: none;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 3px;
    cursor: pointer;
    font-size: 0.8rem;
}

.apply-filter-btn:hover {
    background: var(--color-accent-hover, #0056b3);
}

.filter-restore-prompt {
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--color-bg-light, #fff);
    border: 2px solid var(--color-accent, #007bff);
    border-radius: 6px;
    padding: 1rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 9999;
    max-width: 300px;
}

.restore-prompt-content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.restore-prompt-actions {
    display: flex;
    gap: 0.5rem;
}

.filter-toast {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%) translateY(-100px);
    background: var(--color-success, #28a745);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    z-index: 9999;
    transition: transform 0.3s ease;
}

.filter-toast.show {
    transform: translateX(-50%) translateY(0);
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', filterStyles);

// ==========================================
// INICIALIZACIÓN
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar solo en páginas de administración con filtros
    if (window.location.pathname.includes('/admin/') && 
        (document.querySelector('.filter-form') || 
         document.querySelector('[name="estado"], [name="segmento"]'))) {
        
        window.adminFilters = new AdminFilters();
    }
});

// Exportar para uso global
window.AdminFilters = AdminFilters;
