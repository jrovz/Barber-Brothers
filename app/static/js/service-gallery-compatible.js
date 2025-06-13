// Service Gallery Modal JavaScript - Compatible Version
// Versión compatible con navegadores más antiguos (IE11+, Chrome 49+, Firefox 44+)

(function() {
    'use strict';
    
    function ServiceGallery() {
        this.modal = document.getElementById('service-modal');
        this.currentImageIndex = 0;
        this.images = [];
        this.init();
    }

    ServiceGallery.prototype.init = function() {
        var self = this;
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                self.setupEvents();
            });
        } else {
            this.setupEvents();
        }
    };

    ServiceGallery.prototype.setupEvents = function() {
        var self = this;
        this.setupServiceItems();
        
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' || event.keyCode === 27) {
                self.closeModal();
            }
        });
    };

    ServiceGallery.prototype.setupServiceItems = function() {
        var self = this;
        var serviceItems = document.querySelectorAll('.service-item');
        
        for (var i = 0; i < serviceItems.length; i++) {
            var item = serviceItems[i];
            item.removeAttribute('onclick');
            
            (function(serviceItem) {
                serviceItem.addEventListener('click', function(e) {
                    e.preventDefault();
                    var serviceId = serviceItem.getAttribute('data-service-id');
                    if (serviceId) {
                        self.openModal(serviceId);
                    }
                });
            })(item);
        }
    };

    ServiceGallery.prototype.openModal = function(serviceId) {
        var self = this;
        if (!this.modal) return;

        try {
            this.showLoading();
            this.modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/api/servicio/' + serviceId, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        try {
                            var service = JSON.parse(xhr.responseText);
                            self.updateModalContent(service);
                        } catch (parseError) {
                            console.error('Error al parsear respuesta JSON:', parseError);
                            self.showError('Error al procesar la información del servicio');
                        }
                    } else {
                        console.error('Error HTTP:', xhr.status);
                        self.showError('Error al cargar la información del servicio');
                    }
                }
            };
            
            xhr.onerror = function() {
                console.error('Error de conexión');
                self.showError('Error de conexión al servidor');
            };
            
            xhr.send();
            
        } catch (error) {
            console.error('Error al cargar el servicio:', error);
            this.showError('Error al cargar la información del servicio');
        }
    };

    ServiceGallery.prototype.closeModal = function() {
        if (this.modal) {
            this.modal.style.display = 'none';
            document.body.style.overflow = '';
            this.resetCarousel();
        }
    };

    ServiceGallery.prototype.showLoading = function() {
        var modalContent = this.modal && this.modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.innerHTML = '<div class="modal-loading" style="text-align: center; padding: 3rem;"><div class="loading-spinner" style="border: 4px solid #f3f3f3; border-top: 4px solid #b39656; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 1rem;"></div><p>Cargando servicio...</p></div><style>@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>';
        }
    };

    ServiceGallery.prototype.showError = function(message) {
        var modalContent = this.modal && this.modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.innerHTML = '<div class="modal-error" style="text-align: center; padding: 3rem;"><h3 style="color: #e74c3c; margin-bottom: 1rem;">Error</h3><p>' + message + '</p><button onclick="window.serviceGallery.closeModal()" style="background: #e74c3c; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; margin-top: 1rem;">Cerrar</button></div>';
        }
    };

    ServiceGallery.prototype.updateModalContent = function(service) {
        if (!this.modal) return;

        this.images = service.imagenes || [];
        if (this.images.length === 0 && service.imagen_url) {
            this.images = [service.imagen_url];
        }
        this.currentImageIndex = 0;

        var durationHtml = service.duracion_estimada ? '<div class="meta-item"><span class="meta-icon">⏱️</span><div class="meta-content"><span class="meta-label">Duración</span><span class="meta-value">' + service.duracion_estimada + '</span></div></div>' : '';

        var modalContent = '<div class="modal-header"><h2>' + service.nombre + '</h2><button class="modal-close" onclick="window.serviceGallery.closeModal()">&times;</button></div><div class="modal-body"><div class="modal-image-container">' + this.createCarousel() + '</div><div class="modal-info"><div class="service-details"><h3>Descripción</h3><p>' + service.descripcion + '</p></div><div class="service-meta"><div class="meta-item"><span class="meta-icon">💰</span><div class="meta-content"><span class="meta-label">Precio</span><span class="meta-value">' + service.precio_formateado + '</span></div></div>' + durationHtml + '</div><div class="modal-actions"><a href="/#availability" class="btn book-service-btn">Agendar Cita</a><button class="btn btn-secondary" onclick="window.serviceGallery.closeModal()">Cerrar</button></div></div></div>';

        this.modal.querySelector('.modal-content').innerHTML = modalContent;
        this.setupCarouselEvents();
    };

    ServiceGallery.prototype.createCarousel = function() {
        if (this.images.length === 0) {
            return '<div class="image-placeholder" style="display: flex; align-items: center; justify-content: center; height: 300px; background: #f5f5f5; border-radius: 8px; color: #666;"><div style="text-align: center;"><span style="font-size: 3rem; display: block; margin-bottom: 1rem;">✂️</span><p>Imagen no disponible</p></div></div>';
        }

        if (this.images.length === 1) {
            return '<div class="single-image"><img src="' + this.images[0] + '" alt="Imagen del servicio" style="width: 100%; height: 300px; object-fit: cover; border-radius: 8px;"></div>';
        }

        var slides = '';
        var indicators = '';
        
        for (var i = 0; i < this.images.length; i++) {
            slides += '<div class="carousel-slide" style="min-width: 100%; height: 100%;"><img src="' + this.images[i] + '" alt="Imagen ' + (i + 1) + '" style="width: 100%; height: 100%; object-fit: cover;"></div>';
            indicators += '<button class="carousel-indicator ' + (i === 0 ? 'active' : '') + '" data-index="' + i + '" style="width: 12px; height: 12px; border-radius: 50%; border: none; background: ' + (i === 0 ? '#b39656' : 'rgba(255,255,255,0.7)') + '; cursor: pointer; transition: background 0.3s ease;"></button>';
        }

        return '<div class="image-carousel"><div class="carousel-container" style="position: relative; height: 300px; overflow: hidden; border-radius: 8px;"><div class="carousel-track" style="display: flex; transition: transform 0.3s ease; height: 100%;">' + slides + '</div><button class="carousel-btn prev-btn" style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); background: rgba(0,0,0,0.7); color: white; border: none; width: 40px; height: 40px; border-radius: 50%; font-size: 18px; cursor: pointer; z-index: 10;">‹</button><button class="carousel-btn next-btn" style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: rgba(0,0,0,0.7); color: white; border: none; width: 40px; height: 40px; border-radius: 50%; font-size: 18px; cursor: pointer; z-index: 10;">›</button><div class="carousel-indicators" style="position: absolute; bottom: 15px; left: 50%; transform: translateX(-50%); display: flex; gap: 8px; z-index: 10;">' + indicators + '</div></div><div class="image-counter" style="text-align: center; margin-top: 10px; color: #666; font-size: 14px;"><span id="current-image-number">1</span> de ' + this.images.length + '</div></div>';
    };

    ServiceGallery.prototype.setupCarouselEvents = function() {
        var self = this;
        var prevBtn = this.modal && this.modal.querySelector('.prev-btn');
        var nextBtn = this.modal && this.modal.querySelector('.next-btn');
        var indicators = this.modal && this.modal.querySelectorAll('.carousel-indicator');

        if (prevBtn) {
            prevBtn.addEventListener('click', function() { self.previousImage(); });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', function() { self.nextImage(); });
        }

        if (indicators) {
            for (var i = 0; i < indicators.length; i++) {
                (function(index) {
                    indicators[index].addEventListener('click', function() { self.goToImage(index); });
                })(i);
            }
        }
    };

    ServiceGallery.prototype.previousImage = function() {
        if (this.images.length <= 1) return;
        this.currentImageIndex = (this.currentImageIndex - 1 + this.images.length) % this.images.length;
        this.updateCarousel();
    };

    ServiceGallery.prototype.nextImage = function() {
        if (this.images.length <= 1) return;
        this.currentImageIndex = (this.currentImageIndex + 1) % this.images.length;
        this.updateCarousel();
    };

    ServiceGallery.prototype.goToImage = function(index) {
        if (index >= 0 && index < this.images.length) {
            this.currentImageIndex = index;
            this.updateCarousel();
        }
    };

    ServiceGallery.prototype.updateCarousel = function() {
        var track = this.modal && this.modal.querySelector('.carousel-track');
        var indicators = this.modal && this.modal.querySelectorAll('.carousel-indicator');
        var counter = this.modal && this.modal.querySelector('#current-image-number');

        if (track) {
            track.style.transform = 'translateX(-' + (this.currentImageIndex * 100) + '%)';
        }

        if (indicators) {
            for (var i = 0; i < indicators.length; i++) {
                indicators[i].style.background = i === this.currentImageIndex ? '#b39656' : 'rgba(255,255,255,0.7)';
            }
        }

        if (counter) {
            counter.textContent = this.currentImageIndex + 1;
        }
    };

    ServiceGallery.prototype.resetCarousel = function() {
        this.currentImageIndex = 0;
        this.images = [];
    };

    window.serviceGallery = new ServiceGallery();
    window.openServiceModal = function(serviceId) { window.serviceGallery.openModal(serviceId); };
    window.closeServiceModal = function() { window.serviceGallery.closeModal(); };

})(); 