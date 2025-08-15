// filepath: app/static/js/admin_dashboard.js
/**
 * JavaScript para el dashboard de administradores con cookies de personalización
 * 
 * Funcionalidades:
 * - Configuración personalizada de widgets
 * - Guardado automático de preferencias
 * - Métricas dinámicas
 * - Interfaz adaptable
 */

class AdminDashboard {
    constructor() {
        this.config = this.loadDashboardConfig();
        this.metricsRefreshInterval = null;
        this.init();
    }

    init() {
        this.setupWidgetControls();
        this.setupMetricsControls();
        this.setupInterfaceControls();
        this.startAutoRefresh();
        this.loadUserPreferences();
        
        console.log('📊 Admin Dashboard initialized with personalized settings');
    }

    // ==========================================
    // CONFIGURACIÓN DE WIDGETS
    // ==========================================

    setupWidgetControls() {
        // Botones para mostrar/ocultar widgets
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('widget-toggle')) {
                this.toggleWidget(e.target.dataset.widget);
            }
            
            if (e.target.classList.contains('widget-config')) {
                this.openWidgetConfig(e.target.dataset.widget);
            }
            
            if (e.target.classList.contains('dashboard-customize')) {
                this.openDashboardCustomizer();
            }
        });

        // Drag & Drop para reordenar widgets
        this.setupWidgetDragDrop();
    }

    toggleWidget(widgetName) {
        const widget = document.querySelector(`[data-widget="${widgetName}"]`);
        if (!widget) return;

        const isVisible = !widget.style.display || widget.style.display !== 'none';
        
        if (isVisible) {
            widget.style.display = 'none';
            this.config.widgets = this.config.widgets.filter(w => w !== widgetName);
        } else {
            widget.style.display = 'block';
            if (!this.config.widgets.includes(widgetName)) {
                this.config.widgets.push(widgetName);
            }
        }

        this.saveDashboardConfig();
        this.showToast(`Widget ${widgetName} ${isVisible ? 'ocultado' : 'mostrado'}`, 'info');
    }

    openDashboardCustomizer() {
        // Crear modal de personalización
        const modal = this.createModal('Personalizar Dashboard', this.getDashboardCustomizerHTML());
        document.body.appendChild(modal);

        // Setup event listeners del modal
        this.setupCustomizerEvents(modal);
    }

    getDashboardCustomizerHTML() {
        const availableWidgets = [
            { id: 'stats', name: 'Estadísticas Generales', icon: '📊' },
            { id: 'recent_messages', name: 'Mensajes Recientes', icon: '💬' },
            { id: 'upcoming_appointments', name: 'Próximas Citas', icon: '📅' },
            { id: 'low_stock', name: 'Productos Bajo Stock', icon: '📦' },
            { id: 'charts', name: 'Gráficos y Análisis', icon: '📈' }
        ];

        let html = `
            <div class="dashboard-customizer">
                <h3>🎛️ Configurar Widgets</h3>
                <div class="widget-list">
        `;

        availableWidgets.forEach(widget => {
            const isActive = this.config.widgets.includes(widget.id);
            html += `
                <div class="widget-option">
                    <label class="widget-checkbox">
                        <input type="checkbox" value="${widget.id}" ${isActive ? 'checked' : ''}>
                        <span class="checkmark"></span>
                        <span class="widget-info">
                            <span class="widget-icon">${widget.icon}</span>
                            <span class="widget-name">${widget.name}</span>
                        </span>
                    </label>
                </div>
            `;
        });

        html += `
                </div>
                <h3>⚙️ Configuraciones Generales</h3>
                <div class="config-options">
                    <div class="config-row">
                        <label>Período de Métricas:</label>
                        <select id="metrics-period">
                            <option value="day" ${this.config.metrics_period === 'day' ? 'selected' : ''}>Día</option>
                            <option value="week" ${this.config.metrics_period === 'week' ? 'selected' : ''}>Semana</option>
                            <option value="month" ${this.config.metrics_period === 'month' ? 'selected' : ''}>Mes</option>
                            <option value="quarter" ${this.config.metrics_period === 'quarter' ? 'selected' : ''}>Trimestre</option>
                        </select>
                    </div>
                    <div class="config-row">
                        <label>Auto-actualización (minutos):</label>
                        <input type="number" id="refresh-interval" min="1" max="60" 
                               value="${this.config.refresh_interval / 60}" 
                               title="Intervalo en minutos para actualizar métricas">
                    </div>
                    <div class="config-row">
                        <label>
                            <input type="checkbox" id="compact-mode" 
                                   ${this.config.compact_mode ? 'checked' : ''}>
                            Modo Compacto
                        </label>
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-primary" id="save-dashboard-config">💾 Guardar Configuración</button>
                    <button class="btn btn-outline" id="reset-dashboard-config">🔄 Restaurar Predeterminado</button>
                </div>
            </div>
        `;

        return html;
    }

    setupCustomizerEvents(modal) {
        const saveBtn = modal.querySelector('#save-dashboard-config');
        const resetBtn = modal.querySelector('#reset-dashboard-config');
        
        saveBtn.addEventListener('click', () => {
            this.saveDashboardCustomization(modal);
            this.closeModal(modal);
        });
        
        resetBtn.addEventListener('click', () => {
            if (confirm('¿Restaurar configuración predeterminada? Se perderán las personalizaciones.')) {
                this.resetDashboardConfig();
                this.closeModal(modal);
                location.reload();
            }
        });
    }

    saveDashboardCustomization(modal) {
        // Guardar widgets seleccionados
        const selectedWidgets = [];
        modal.querySelectorAll('.widget-option input[type="checkbox"]:checked').forEach(checkbox => {
            selectedWidgets.push(checkbox.value);
        });
        
        this.config.widgets = selectedWidgets;
        this.config.metrics_period = modal.querySelector('#metrics-period').value;
        this.config.refresh_interval = parseInt(modal.querySelector('#refresh-interval').value) * 60;
        this.config.compact_mode = modal.querySelector('#compact-mode').checked;

        this.saveDashboardConfig();
        this.showToast('✅ Configuración guardada. Recargando...', 'success');
        
        setTimeout(() => location.reload(), 1000);
    }

    // ==========================================
    // MÉTRICAS Y KPIs
    // ==========================================

    setupMetricsControls() {
        // Configurar actualización automática de métricas
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('refresh-metrics')) {
                this.refreshMetrics();
            }
            
            if (e.target.classList.contains('export-metrics')) {
                this.exportMetrics();
            }
        });

        // Configurar selectores de período
        const periodSelectors = document.querySelectorAll('.metrics-period-selector');
        periodSelectors.forEach(selector => {
            selector.addEventListener('change', (e) => {
                this.updateMetricsPeriod(e.target.value);
            });
        });
    }

    refreshMetrics() {
        this.showToast('🔄 Actualizando métricas...', 'info');
        
        // Simular actualización de métricas
        fetch('/admin/api/refresh-metrics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.updateMetricsDisplay(data.metrics);
                this.showToast('✅ Métricas actualizadas', 'success');
            } else {
                this.showToast('❌ Error al actualizar métricas', 'error');
            }
        })
        .catch(error => {
            console.error('Error refreshing metrics:', error);
            this.showToast('❌ Error de conexión', 'error');
        });
    }

    updateMetricsDisplay(metrics) {
        // Actualizar contadores en el dashboard
        Object.entries(metrics).forEach(([key, value]) => {
            const element = document.querySelector(`[data-metric="${key}"]`);
            if (element) {
                this.animateCounter(element, value);
            }
        });
    }

    animateCounter(element, targetValue) {
        const startValue = parseInt(element.textContent) || 0;
        const duration = 1000;
        const steps = 30;
        const increment = (targetValue - startValue) / steps;
        
        let currentStep = 0;
        const timer = setInterval(() => {
            currentStep++;
            const currentValue = Math.round(startValue + (increment * currentStep));
            element.textContent = currentValue;
            
            if (currentStep >= steps) {
                clearInterval(timer);
                element.textContent = targetValue;
            }
        }, duration / steps);
    }

    // ==========================================
    // CONFIGURACIONES DE INTERFAZ
    // ==========================================

    setupInterfaceControls() {
        // Sidebar toggle
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('sidebar-toggle')) {
                this.toggleSidebar();
            }
            
            if (e.target.classList.contains('compact-toggle')) {
                this.toggleCompactMode();
            }
        });

        // Aplicar configuraciones guardadas
        this.applyInterfaceSettings();
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const isCollapsed = sidebar.classList.contains('collapsed');
        
        if (isCollapsed) {
            sidebar.classList.remove('collapsed');
        } else {
            sidebar.classList.add('collapsed');
        }

        this.saveInterfaceSetting('sidebar_collapsed', !isCollapsed);
    }

    toggleCompactMode() {
        document.body.classList.toggle('compact-mode');
        const isCompact = document.body.classList.contains('compact-mode');
        
        this.config.compact_mode = isCompact;
        this.saveDashboardConfig();
        this.saveInterfaceSetting('compact_mode', isCompact);
        
        this.showToast(`Modo ${isCompact ? 'compacto' : 'normal'} activado`, 'info');
    }

    applyInterfaceSettings() {
        const settings = this.loadInterfaceSettings();
        
        if (settings.sidebar_collapsed) {
            document.querySelector('.sidebar')?.classList.add('collapsed');
        }
        
        if (settings.compact_mode || this.config.compact_mode) {
            document.body.classList.add('compact-mode');
        }
    }

    // ==========================================
    // AUTO-REFRESH
    // ==========================================

    startAutoRefresh() {
        if (this.metricsRefreshInterval) {
            clearInterval(this.metricsRefreshInterval);
        }

        const intervalMs = this.config.refresh_interval * 1000;
        
        this.metricsRefreshInterval = setInterval(() => {
            this.refreshMetrics();
        }, intervalMs);

        console.log(`🔄 Auto-refresh configurado cada ${this.config.refresh_interval / 60} minutos`);
    }

    // ==========================================
    // PERSISTENCIA DE DATOS
    // ==========================================

    loadDashboardConfig() {
        try {
            // Los datos vienen del middleware, pero podemos usar también localStorage como backup
            const serverConfig = window.dashboardConfig || {};
            const localConfig = JSON.parse(localStorage.getItem('admin_dashboard_config') || '{}');
            
            return {
                widgets: ['stats', 'recent_messages', 'upcoming_appointments'],
                metrics_period: 'month',
                refresh_interval: 300,
                compact_mode: false,
                chart_types: {
                    'client_segmentation': 'doughnut',
                    'barber_performance': 'bar',
                    'service_popularity': 'bar'
                },
                ...serverConfig,
                ...localConfig
            };
        } catch (error) {
            console.error('Error loading dashboard config:', error);
            return this.getDefaultConfig();
        }
    }

    saveDashboardConfig() {
        try {
            // Guardar en cookie via API
            fetch('/admin/api/save-dashboard-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(this.config)
            });

            // Backup en localStorage
            localStorage.setItem('admin_dashboard_config', JSON.stringify(this.config));
            
        } catch (error) {
            console.error('Error saving dashboard config:', error);
        }
    }

    loadInterfaceSettings() {
        try {
            const serverSettings = window.interfaceSettings || {};
            const localSettings = JSON.parse(localStorage.getItem('admin_interface_settings') || '{}');
            
            return {
                sidebar_collapsed: false,
                theme: 'default',
                notifications_enabled: true,
                auto_refresh: true,
                ...serverSettings,
                ...localSettings
            };
        } catch (error) {
            console.error('Error loading interface settings:', error);
            return {};
        }
    }

    saveInterfaceSetting(key, value) {
        try {
            fetch('/admin/api/save-interface-setting', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ [key]: value })
            });

            // Backup en localStorage
            const settings = this.loadInterfaceSettings();
            settings[key] = value;
            localStorage.setItem('admin_interface_settings', JSON.stringify(settings));
            
        } catch (error) {
            console.error('Error saving interface setting:', error);
        }
    }

    resetDashboardConfig() {
        this.config = this.getDefaultConfig();
        this.saveDashboardConfig();
        localStorage.removeItem('admin_dashboard_config');
    }

    getDefaultConfig() {
        return {
            widgets: ['stats', 'recent_messages', 'upcoming_appointments'],
            metrics_period: 'month',
            refresh_interval: 300,
            compact_mode: false,
            chart_types: {
                'client_segmentation': 'doughnut',
                'barber_performance': 'bar',
                'service_popularity': 'bar'
            }
        };
    }

    // ==========================================
    // UTILIDADES
    // ==========================================

    createModal(title, content) {
        const modal = document.createElement('div');
        modal.className = 'admin-modal-overlay';
        modal.innerHTML = `
            <div class="admin-modal">
                <div class="admin-modal-header">
                    <h2>${title}</h2>
                    <button class="modal-close" onclick="this.closest('.admin-modal-overlay').remove()">×</button>
                </div>
                <div class="admin-modal-body">
                    ${content}
                </div>
            </div>
        `;
        
        // Cerrar al hacer click fuera
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        return modal;
    }

    closeModal(modal) {
        modal.remove();
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `admin-toast admin-toast-${type}`;
        
        // Agregar icono según el tipo
        const icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        
        const icon = icons[type] || icons['info'];
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.2rem;">${icon}</span>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Trigger show animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove after delay
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    toast.remove();
                }
            }, 300);
        }, 4000);
        
        // Allow manual close on click
        toast.addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    toast.remove();
                }
            }, 300);
        });
    }

    getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    loadUserPreferences() {
        // Aplicar preferencias del usuario al cargar
        if (this.config.compact_mode) {
            document.body.classList.add('compact-mode');
        }
    }

    // ==========================================
    // DRAG & DROP WIDGETS
    // ==========================================

    setupWidgetDragDrop() {
        const widgets = document.querySelectorAll('.dashboard-widget');
        
        widgets.forEach(widget => {
            widget.draggable = true;
            
            widget.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', widget.dataset.widget);
                widget.classList.add('dragging');
            });
            
            widget.addEventListener('dragend', () => {
                widget.classList.remove('dragging');
            });
            
            widget.addEventListener('dragover', (e) => {
                e.preventDefault();
            });
            
            widget.addEventListener('drop', (e) => {
                e.preventDefault();
                const draggedWidget = e.dataTransfer.getData('text/plain');
                const targetWidget = widget.dataset.widget;
                
                if (draggedWidget !== targetWidget) {
                    this.reorderWidgets(draggedWidget, targetWidget);
                }
            });
        });
    }

    reorderWidgets(draggedWidget, targetWidget) {
        const widgets = [...this.config.widgets];
        const draggedIndex = widgets.indexOf(draggedWidget);
        const targetIndex = widgets.indexOf(targetWidget);
        
        if (draggedIndex > -1 && targetIndex > -1) {
            widgets.splice(draggedIndex, 1);
            widgets.splice(targetIndex, 0, draggedWidget);
            
            this.config.widgets = widgets;
            this.saveDashboardConfig();
            
            this.showToast('✅ Orden de widgets actualizado', 'success');
        }
    }
}

// ==========================================
// INICIALIZACIÓN
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    if (document.body.classList.contains('admin-dashboard')) {
        window.adminDashboard = new AdminDashboard();
    }
});

// Exportar para uso global
window.AdminDashboard = AdminDashboard;
