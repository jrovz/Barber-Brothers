/**
 * Barber Brothers Slider - Optimized
 * ===============================
 * Script optimizado para el slider de la página principal
 * con lazy loading, IntersectionObserver y manejo eficiente de recursos
 */

// Función principal autoejecutable para evitar contaminación del scope global
(function() {
    'use strict';
    
    // Configuración del slider
    const CONFIG = {
        SLIDE_DURATION: 6000,       // 6 segundos entre slides
        TRANSITION_DURATION: 800,   // 0.8 segundos de transición
        THROTTLE_DELAY: 100,        // 100ms para throttling de eventos
        OBSERVER_THRESHOLD: 0.1     // 10% de visibilidad para activar observer
    };
    
    // Variables para controlar el estado
    let currentSlide = 0;
    let slideInterval = null;
    let isTransitioning = false;
    let slidesLoaded = false;
    let isVisible = true;
    
    // Función de inicialización principal
    function initSlider() {
        // Elementos DOM
        const slider = {
            container: document.querySelector('.hero-slider'),
            slides: document.querySelectorAll('.slide'),
            dots: document.querySelectorAll('.dot'),
            prevArrow: document.querySelector('.prev-arrow'),
            nextArrow: document.querySelector('.next-arrow')
        };
        
        // Salir si no hay slider
        if (!slider.container || !slider.slides.length) return;
        
        // Inicializar optimizaciones avanzadas
        initLazyLoading(slider);
        initIntersectionObserver(slider);
        
        // Configurar eventos del slider
        setupEventListeners(slider);
        
        // Inicializar el estado
        showSlide(0, true);
        
        // Iniciar rotación automática si hay más de un slide
        if (slider.slides.length > 1) {
            startSlideInterval();
        }
        
        // Manejar cambios de visibilidad
        handleVisibilityChanges();

        // LCP: eliminar la clase 'initial' tras el primer frame para permitir animaciones posteriores
        requestAnimationFrame(() => {
            const hero = document.querySelector('.hero-slider.initial');
            if (hero) {
                hero.classList.remove('initial');
            }
        });
    }
    
    // Inicializar lazy loading para imágenes de fondo
    function initLazyLoading(slider) {
        // Para cada slide, usar el atributo data-img para cargar la imagen
        slider.slides.forEach((slide, index) => {
            const slideBg = slide.querySelector('.slide-bg');
            if (!slideBg) return;
            
            // Obtener la URL de la imagen del atributo data-img
            const imageUrl = slideBg.getAttribute('data-img');
            if (!imageUrl) return;
            
            // Configurar background-image
            if (index < 2) {
                // Para los primeros dos slides, carga inmediata
                slideBg.style.backgroundImage = `url('${imageUrl}')`;
                preloadImage(imageUrl, () => {
                    slideBg.classList.add('image-loaded');
                });
            } else {
                // Para el resto, usar lazy loading
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            slideBg.style.backgroundImage = `url('${imageUrl}')`;
                            preloadImage(imageUrl, () => {
                                slideBg.classList.add('image-loaded');
                            });
                            observer.disconnect();
                        }
                    });
                }, { rootMargin: '200px' });
                
                observer.observe(slideBg);
            }
        });
    }
    
    // Precarga de imagen con callback
    function preloadImage(src, callback) {
        const img = new Image();
        img.onload = callback;
        img.src = src;
    }
    
    // Inicializar IntersectionObserver para optimizar renderizado
    function initIntersectionObserver(slider) {
        if (!('IntersectionObserver' in window)) return;
        
        const sliderObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                isVisible = entry.isIntersecting;
                
                if (entry.isIntersecting) {
                    // Optimizar para renderizado
                    slider.container.style.willChange = 'transform';
                    
                    // Reiniciar intervalo si estaba visible
                    if (slidesLoaded && !slideInterval) {
                        startSlideInterval();
                    }
                } else {
                    // Reducir overhead cuando no es visible
                    slider.container.style.willChange = 'auto';
                    
                    // Pausar intervalo cuando no es visible
                    stopSlideInterval();
                }
            });
        }, { threshold: CONFIG.OBSERVER_THRESHOLD });
        
        sliderObserver.observe(slider.container);
    }
    
    // Configurar todos los event listeners
    function setupEventListeners(slider) {
        // Navegación con flechas
        if (slider.prevArrow) {
            slider.prevArrow.addEventListener('click', function(e) {
                e.preventDefault();
                prevSlide();
                resetSlideInterval();
            });
        }
        
        if (slider.nextArrow) {
            slider.nextArrow.addEventListener('click', function(e) {
                e.preventDefault();
                nextSlide();
                resetSlideInterval();
            });
        }
        
        // Navegación con dots
        if (slider.dots.length) {
            slider.dots.forEach((dot, index) => {
                dot.addEventListener('click', function(e) {
                    e.preventDefault();
                    const slideIndex = parseInt(this.dataset.slide);
                    if (!isNaN(slideIndex)) {
                        goToSlide(slideIndex);
                        resetSlideInterval();
                    }
                });
            });
        }
        
        // Pausar en hover
        slider.container.addEventListener('mouseenter', stopSlideInterval);
        slider.container.addEventListener('mouseleave', function() {
            if (isVisible) {
                startSlideInterval();
            }
        });
        
        // Accesibilidad - pausa en foco
        slider.container.addEventListener('focusin', stopSlideInterval);
        slider.container.addEventListener('focusout', function() {
            if (isVisible) {
                startSlideInterval();
            }
        });
        
        // Limpiar recursos al salir
        window.addEventListener('beforeunload', cleanup);
    }
    
    // Manejar cambios de visibilidad de la página
    function handleVisibilityChanges() {
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                stopSlideInterval();
            } else if (isVisible) {
                startSlideInterval();
            }
        });
    }
    
    // Función para mostrar un slide específico
    function showSlide(index, skipTransition = false) {
        // Prevenir transiciones rápidas consecutivas
        if (isTransitioning && !skipTransition) return;
        
        const slides = document.querySelectorAll('.slide');
        const dots = document.querySelectorAll('.dot');
        
        // Validar índice
        if (index < 0 || index >= slides.length) return;
        
        // Establecer bandera de transición
        if (!skipTransition) {
            isTransitioning = true;
        }
        
        const previousSlide = currentSlide;
        currentSlide = index;
        
        // Actualizar slides
        slides.forEach((slide, idx) => {
            if (idx === currentSlide) {
                slide.classList.add('active');
                
                // Aplicar content-visibility para optimizar
                slide.style.contentVisibility = 'visible';
                slide.style.containIntrinsicSize = 'none';
            } else {
                slide.classList.remove('active');
                
                // Optimizar slides no activos
                slide.style.contentVisibility = 'auto';
                slide.style.containIntrinsicSize = '0 500px'; // Altura aproximada
            }
        });
        
        // Actualizar dots
        dots.forEach((dot, idx) => {
            dot.classList.toggle('active', idx === currentSlide);
        });
        
        // Inicializar embebidos de Instagram si es necesario
        const currentSlideElement = slides[currentSlide];
        if (currentSlideElement && currentSlideElement.classList.contains('instagram-embed-slide')) {
            refreshInstagramEmbed();
        }
        
        // Limpiar bandera de transición después de la animación
        if (!skipTransition) {
            setTimeout(() => {
                isTransitioning = false;
            }, CONFIG.TRANSITION_DURATION);
        }
    }
    
    // Funciones de navegación
    function nextSlide() {
        const slides = document.querySelectorAll('.slide');
        const newIndex = (currentSlide + 1) % slides.length;
        showSlide(newIndex);
    }
    
    function prevSlide() {
        const slides = document.querySelectorAll('.slide');
        const newIndex = (currentSlide - 1 + slides.length) % slides.length;
        showSlide(newIndex);
    }
    
    function goToSlide(index) {
        const slides = document.querySelectorAll('.slide');
        if (index >= 0 && index < slides.length && index !== currentSlide) {
            showSlide(index);
        }
    }
    
    // Gestión del intervalo
    function startSlideInterval() {
        // Limpiar intervalo existente
        stopSlideInterval();
        
        // Crear nuevo intervalo
        slideInterval = setInterval(() => {
            if (!isTransitioning && isVisible) {
                nextSlide();
            }
        }, CONFIG.SLIDE_DURATION);
        
        slidesLoaded = true;
    }
    
    function stopSlideInterval() {
        if (slideInterval) {
            clearInterval(slideInterval);
            slideInterval = null;
        }
    }
    
    function resetSlideInterval() {
        stopSlideInterval();
        if (isVisible) {
            startSlideInterval();
        }
    }
    
    // Cargar Instagram embeds solo cuando son visibles
    function refreshInstagramEmbed() {
        if (window.instgrm && window.instgrm.Embeds) {
            setTimeout(() => window.instgrm.Embeds.process(), 100);
        }
    }
    
    // Liberar recursos
    function cleanup() {
        stopSlideInterval();
    }
    
    // Inicializar slider cuando DOM está listo
    document.addEventListener('DOMContentLoaded', initSlider);
})();
