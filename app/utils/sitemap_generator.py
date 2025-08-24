# -*- coding: utf-8 -*-
"""
Generador de Sitemap para Barber Brothers
=========================================

Utilidad para generar dinámicamente el sitemap.xml de la aplicación.

Author: AI Assistant
Version: 1.0
"""

from flask import url_for, request, current_app
from datetime import datetime
from typing import List, Dict, Any

class SitemapGenerator:
    """Generador de sitemap.xml para la aplicación"""
    
    @staticmethod
    def generate_sitemap(base_url: str = None) -> str:
        """
        Genera el contenido del archivo sitemap.xml
        
        Args:
            base_url: URL base del sitio. Si no se proporciona, se usa request.url_root
            
        Returns:
            str: Contenido XML del sitemap
        """
        if not base_url:
            base_url = request.url_root.rstrip('/')
        
        # Lista de todas las URLs públicas del sitio
        urls = SitemapGenerator._get_public_urls(base_url)
        
        # Generar el XML
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for url in urls:
            xml += '  <url>\n'
            xml += f'    <loc>{url["loc"]}</loc>\n'
            if url.get("lastmod"):
                xml += f'    <lastmod>{url["lastmod"]}</lastmod>\n'
            if url.get("changefreq"):
                xml += f'    <changefreq>{url["changefreq"]}</changefreq>\n'
            if url.get("priority"):
                xml += f'    <priority>{url["priority"]}</priority>\n'
            xml += '  </url>\n'
            
        xml += '</urlset>'
        return xml
    
    @staticmethod
    def _get_public_urls(base_url: str) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de todas las URLs públicas del sitio
        
        Args:
            base_url: URL base del sitio
            
        Returns:
            List[Dict]: Lista de diccionarios con datos de cada URL
        """
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        # URLs estáticas principales
        main_pages = [
            {
                "endpoint": "public.home",
                "lastmod": today,
                "changefreq": "weekly",
                "priority": "1.0"
            },
            {
                "endpoint": "public.servicios",
                "lastmod": today,
                "changefreq": "weekly",
                "priority": "0.8"
            },
            {
                "endpoint": "public.productos",
                "lastmod": today,
                "changefreq": "daily",
                "priority": "0.8"
            },
            {
                "endpoint": "public.contact",
                "lastmod": today,
                "changefreq": "monthly",
                "priority": "0.6"
            }
        ]
        
        # Páginas legales
        legal_pages = [
            {
                "endpoint": "public.privacidad",
                "lastmod": today,
                "changefreq": "monthly",
                "priority": "0.3"
            },
            {
                "endpoint": "public.terminos",
                "lastmod": today,
                "changefreq": "monthly",
                "priority": "0.3"
            },
            {
                "endpoint": "public.cookies",
                "lastmod": today,
                "changefreq": "monthly",
                "priority": "0.3"
            }
        ]
        
        # Combinar todas las URLs
        all_urls = []
        
        # Procesar páginas principales
        for page in main_pages + legal_pages:
            try:
                # Generar URL absoluta
                url = base_url + url_for(page["endpoint"])
                
                all_urls.append({
                    "loc": url,
                    "lastmod": page.get("lastmod"),
                    "changefreq": page.get("changefreq"),
                    "priority": page.get("priority")
                })
            except Exception as e:
                current_app.logger.error(f"Error generando URL para {page['endpoint']}: {str(e)}")
        
        # Aquí se pueden agregar URLs dinámicas (productos, servicios, etc.)
        # En una implementación más avanzada, se consultaría la base de datos
        
        return all_urls