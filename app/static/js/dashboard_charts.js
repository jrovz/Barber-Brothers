/**
 * Dashboard Charts - Barber Brothers
 * Script para visualizar métricas en el panel de administración
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar todos los gráficos si existen los contenedores
    if (document.getElementById('appointmentsChart')) {
        initAppointmentsChart();
    }
    
    if (document.getElementById('barberPerformanceChart')) {
        initBarberPerformanceChart();
    }
    
    if (document.getElementById('servicePopularityChart')) {
        initServicePopularityChart();
    }
    
    if (document.getElementById('clientSegmentationChart')) {
        initClientSegmentationChart();
    }
});

/**
 * Inicializa gráfico de citas por día de la semana
 */
function initAppointmentsChart() {
    const ctx = document.getElementById('appointmentsChart').getContext('2d');
    
    // Los datos vendrán del elemento data o de una API
    const chartData = JSON.parse(document.getElementById('appointmentsData').textContent);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Citas',
                data: chartData.data,
                backgroundColor: 'rgba(210, 184, 131, 0.2)',
                borderColor: '#d2b883',
                borderWidth: 2,
                pointBackgroundColor: '#d2b883',
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(200, 200, 200, 0.1)'
                    },
                    ticks: {
                        color: '#e3d9c6'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(200, 200, 200, 0.1)'
                    },
                    ticks: {
                        color: '#e3d9c6'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#f5f0e6'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 9, 8, 0.8)',
                    titleColor: '#f5f0e6',
                    bodyColor: '#e3d9c6',
                    borderColor: '#d2b883',
                    borderWidth: 1
                }
            }
        }
    });
}

/**
 * Inicializa gráfico de rendimiento de barberos
 */
function initBarberPerformanceChart() {
    const ctx = document.getElementById('barberPerformanceChart').getContext('2d');
    
    // Los datos vendrán del elemento data o de una API
    const chartData = JSON.parse(document.getElementById('barberPerformanceData').textContent);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.names,
            datasets: [{
                label: 'Citas Atendidas',
                data: chartData.appointments,
                backgroundColor: 'rgba(23, 162, 184, 0.7)',
                borderColor: '#17a2b8',
                borderWidth: 1
            },
            {
                label: 'Ocupación (%)',
                data: chartData.occupation,
                backgroundColor: 'rgba(210, 184, 131, 0.7)',
                borderColor: '#d2b883',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(200, 200, 200, 0.1)'
                    },
                    ticks: {
                        color: '#e3d9c6'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(200, 200, 200, 0.1)'
                    },
                    ticks: {
                        color: '#e3d9c6'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#f5f0e6'
                    }
                }
            }
        }
    });
}

/**
 * Inicializa gráfico de popularidad de servicios
 */
function initServicePopularityChart() {
    const ctx = document.getElementById('servicePopularityChart').getContext('2d');
    
    // Los datos vendrán del elemento data o de una API
    const chartData = JSON.parse(document.getElementById('serviceData').textContent);
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: chartData.labels,
            datasets: [{
                data: chartData.data,
                backgroundColor: [
                    '#d2b883', // Color primario
                    '#17a2b8', // Info
                    '#28a745', // Success
                    '#ffc107', // Warning
                    '#dc3545'  // Danger
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#f5f0e6',
                        padding: 15
                    }
                }
            }
        }
    });
}

/**
 * Inicializa gráfico de segmentación de clientes
 */
function initClientSegmentationChart() {
    const ctx = document.getElementById('clientSegmentationChart').getContext('2d');
    
    // Los datos vendrán del elemento data
    const segmentData = JSON.parse(document.getElementById('clientSegmentationData').textContent);
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: segmentData.labels,
            datasets: [{
                data: segmentData.data,
                backgroundColor: [
                    '#17a2b8', // Info (Nuevos)
                    '#d2b883', // Primary (Ocasionales)
                    '#28a745', // Success (Recurrentes)
                    '#ffc107', // Warning (VIP)
                    '#dc3545'  // Danger (Inactivos)
                ],
                borderColor: '#0a0908',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#e3d9c6',
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 9, 8, 0.8)',
                    titleColor: '#f5f0e6',
                    bodyColor: '#e3d9c6',
                    borderColor: '#d2b883',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}
