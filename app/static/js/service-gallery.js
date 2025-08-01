// Service Gallery Modal JavaScript
// Funcionalidad para mostrar servicios en una ventana flotante con galería y carrusel

class ServiceGallery {
    constructor() {
        this.modal = document.getElementById('service-modal');
        this.currentImageIndex = 0;
        this.images = [];
        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEvents());
        } else {
            this.setupEvents();
        }
    }

    setupEvents() {
        this.setupServiceItems();
        
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    setupServiceItems() {
        const serviceItems = document.querySelectorAll('.service-item');
        serviceItems.forEach(item => {
            item.removeAttribute('onclick');
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const serviceId = item.getAttribute('data-service-id');
                if (serviceId) {
                    this.openModal(serviceId);
                }
            });
        });
    }

    async openModal(serviceId) {
        if (!this.modal) return;

        try {
            this.showLoading();
            this.modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            
            const response = await fetch(`/api/servicio/${serviceId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const service = await response.json();
            this.updateModalContent(service);
            
        } catch (error) {
            console.error('Error al cargar el servicio:', error);
            this.showError('Error al cargar la información del servicio');
        }
    }

    closeModal() {
        if (this.modal) {
            this.modal.style.display = 'none';
            document.body.style.overflow = '';
            this.resetCarousel();
        }
    }

    showLoading() {
        const modalContent = this.modal?.querySelector('.modal-content');
        if (modalContent) {
            modalContent.innerHTML = `
                <div class="modal-loading" style="text-align: center; padding: 3rem;">
                    <div class="loading-spinner" style="
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #b39656;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 1rem;
                    "></div>
                    <p>Cargando servicio...</p>
                </div>
                <style>
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            `;
        }
    }

    showError(message) {
        const modalContent = this.modal?.querySelector('.modal-content');
        if (modalContent) {
            modalContent.innerHTML = `
                <div class="modal-error" style="text-align: center; padding: 3rem;">
                    <h3 style="color: #e74c3c; margin-bottom: 1rem;">Error</h3>
                    <p>${message}</p>
                    <button onclick="serviceGallery.closeModal()" style="
                        background: #e74c3c;
                        color: white;
                        border: none;
                        padding: 0.5rem 1rem;
                        border-radius: 4px;
                        cursor: pointer;
                        margin-top: 1rem;
                    ">Cerrar</button>
                </div>
            `;
        }
    }

    updateModalContent(service) {
        if (!this.modal) return;

        this.images = service.imagenes || [];
        if (this.images.length === 0 && service.imagen_url) {
            this.images = [service.imagen_url];
        }
        this.currentImageIndex = 0;

        const modalContent = `
            <div class="modal-header">
                <h2>${service.nombre}</h2>
                <button class="modal-close" onclick="serviceGallery.closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="modal-image-container">
                    ${this.createCarousel()}
                </div>
                <div class="modal-info">
                    <div class="service-details">
                        <h3>Descripción</h3>
                        <p>${service.descripcion}</p>
                    </div>
                    <div class="service-meta">
                        <div class="meta-item">
                            <span class="meta-icon">💰</span>
                            <div class="meta-content">
                                <span class="meta-label">Precio</span>
                                <span class="meta-value">${service.precio_formateado}</span>
                            </div>
                        </div>
                        ${service.duracion_estimada ? `
                        <div class="meta-item">
                            <span class="meta-icon">⏱️</span>
                            <div class="meta-content">
                                <span class="meta-label">Duración</span>
                                <span class="meta-value">${service.duracion_estimada}</span>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    <div class="modal-actions">
                        <a href="/#availability" class="btn book-service-btn">Agendar Cita</a>
                        <button class="btn btn-secondary" onclick="serviceGallery.closeModal()">Cerrar</button>
                    </div>
                </div>
            </div>
        `;

        this.modal.querySelector('.modal-content').innerHTML = modalContent;
        this.setupCarouselEvents();
    }

    createCarousel() {
        if (this.images.length === 0) {
            return `
                <div class="image-placeholder" style="
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 300px;
                    background: #f5f5f5;
                    border-radius: 8px;
                    color: #666;
                ">
                    <div style="text-align: center;">
                        <span style="font-size: 3rem; display: block; margin-bottom: 1rem;">✂️</span>
                        <p>Imagen no disponible</p>
                    </div>
                </div>
            `;
        }

        if (this.images.length === 1) {
            return `
                <div class="single-image">
                    <img src="${this.images[0]}" alt="Imagen del servicio" style="
                        width: 100%;
                        height: 300px;
                        object-fit: cover;
                        border-radius: 8px;
                    ">
                </div>
            `;
        }

        return `
            <div class="image-carousel">
                <div class="carousel-container" style="position: relative; height: 300px; overflow: hidden; border-radius: 8px;">
                    <div class="carousel-track" style="
                        display: flex;
                        transition: transform 0.3s ease;
                        height: 100%;
                    ">
                        ${this.images.map((img, index) => `
                            <div class="carousel-slide" style="min-width: 100%; height: 100%;">
                                <img src="${img}" alt="Imagen ${index + 1}" style="
                                    width: 100%;
                                    height: 100%;
                                    object-fit: cover;
                                ">
                            </div>
                        `).join('')}
                    </div>
                    
                    <button class="carousel-btn prev-btn" style="
                        position: absolute;
                        left: 10px;
                        top: 50%;
                        transform: translateY(-50%);
                        background: rgba(0,0,0,0.7);
                        color: white;
                        border: none;
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        font-size: 18px;
                        cursor: pointer;
                        z-index: 10;
                    ">‹</button>
                    <button class="carousel-btn next-btn" style="
                        position: absolute;
                        right: 10px;
                        top: 50%;
                        transform: translateY(-50%);
                        background: rgba(0,0,0,0.7);
                        color: white;
                        border: none;
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        font-size: 18px;
                        cursor: pointer;
                        z-index: 10;
                    ">›</button>
                    
                    <div class="carousel-indicators" style="
                        position: absolute;
                        bottom: 15px;
                        left: 50%;
                        transform: translateX(-50%);
                        display: flex;
                        gap: 8px;
                        z-index: 10;
                    ">
                        ${this.images.map((_, index) => `
                            <button class="carousel-indicator ${index === 0 ? 'active' : ''}" data-index="${index}" style="
                                width: 12px;
                                height: 12px;
                                border-radius: 50%;
                                border: none;
                                background: ${index === 0 ? '#b39656' : 'rgba(255,255,255,0.7)'};
                                cursor: pointer;
                                transition: background 0.3s ease;
                            "></button>
                        `).join('')}
                    </div>
                </div>
                
                <div class="image-counter" style="
                    text-align: center;
                    margin-top: 10px;
                    color: #666;
                    font-size: 14px;
                ">
                    <span id="current-image-number">1</span> de ${this.images.length}
                </div>
            </div>
        `;
    }

    setupCarouselEvents() {
        const prevBtn = this.modal?.querySelector('.prev-btn');
        const nextBtn = this.modal?.querySelector('.next-btn');
        const indicators = this.modal?.querySelectorAll('.carousel-indicator');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.previousImage());
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextImage());
        }

        indicators?.forEach((indicator, index) => {
            indicator.addEventListener('click', () => this.goToImage(index));
        });
    }

    previousImage() {
        if (this.images.length <= 1) return;
        this.currentImageIndex = (this.currentImageIndex - 1 + this.images.length) % this.images.length;
        this.updateCarousel();
    }

    nextImage() {
        if (this.images.length <= 1) return;
        this.currentImageIndex = (this.currentImageIndex + 1) % this.images.length;
        this.updateCarousel();
    }

    goToImage(index) {
        if (index >= 0 && index < this.images.length) {
            this.currentImageIndex = index;
            this.updateCarousel();
        }
    }

    updateCarousel() {
        const track = this.modal?.querySelector('.carousel-track');
        const indicators = this.modal?.querySelectorAll('.carousel-indicator');
        const counter = this.modal?.querySelector('#current-image-number');

        if (track) {
            track.style.transform = `translateX(-${this.currentImageIndex * 100}%)`;
        }

        indicators?.forEach((indicator, index) => {
            indicator.style.background = index === this.currentImageIndex ? '#b39656' : 'rgba(255,255,255,0.7)';
        });

        if (counter) {
            counter.textContent = this.currentImageIndex + 1;
        }
    }

    resetCarousel() {
        this.currentImageIndex = 0;
        this.images = [];
    }
}

// Crear instancia global
const serviceGallery = new ServiceGallery();

// Funciones globales para compatibilidad
window.openServiceModal = (serviceId) => serviceGallery.openModal(serviceId);
window.closeServiceModal = () => serviceGallery.closeModal();
