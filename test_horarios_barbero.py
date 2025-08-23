#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para probar las funcionalidades de horarios de barberos y bloqueos temporales.

Este script prueba:
1. La existencia de las tablas necesarias
2. La creación de bloqueos temporales
3. La verificación de disponibilidad considerando bloqueos
4. La eliminación de bloqueos
5. La limpieza automática de bloqueos pasados

Uso:
    python test_horarios_barbero.py
"""

import os
import sys
import unittest
from datetime import datetime, date, time, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Asegurarse de que podemos importar la aplicación
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app import create_app, db
    from app.models.barbero import Barbero, DisponibilidadBarbero, BloqueoHorario
    from app.models.tareas import limpiar_bloqueos_pasados
    from sqlalchemy import inspect
except ImportError as e:
    logger.error(f"Error al importar: {e}")
    logger.error("Asegúrate de ejecutar este script desde el directorio raíz del proyecto")
    sys.exit(1)

class TestHorariosBarbero(unittest.TestCase):
    """Pruebas para la funcionalidad de horarios de barberos"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todas las pruebas"""
        cls.app = create_app('testing')
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        cls.client = cls.app.test_client()
        
        # Crear tablas si no existen
        db.create_all()
        
        # Verificar si la tabla BloqueoHorario existe
        inspector = inspect(db.engine)
        cls.tabla_bloqueo_existe = 'bloqueo_horario' in inspector.get_table_names()
        
        if not cls.tabla_bloqueo_existe:
            logger.warning("La tabla bloqueo_horario no existe. Se creará para las pruebas.")
            # Si no existe, intentamos crearla
            try:
                db.create_all()
                cls.tabla_bloqueo_existe = 'bloqueo_horario' in inspector.get_table_names()
            except Exception as e:
                logger.error(f"No se pudo crear la tabla bloqueo_horario: {e}")
        
        # Crear un barbero de prueba
        try:
            cls.barbero_test = Barbero.query.filter_by(nombre="Barbero Test").first()
            if not cls.barbero_test:
                cls.barbero_test = Barbero(
                    nombre="Barbero Test",
                    username="barbero_test",
                    activo=True,
                    tiene_acceso_web=True
                )
                cls.barbero_test.set_password("password123")
                db.session.add(cls.barbero_test)
                db.session.commit()
                logger.info("Barbero de prueba creado")
            
            # Crear disponibilidad para el barbero
            if not cls.barbero_test.disponibilidad.count():
                for dia in range(0, 6):  # Lunes a Sábado
                    disponibilidad = DisponibilidadBarbero(
                        barbero_id=cls.barbero_test.id,
                        dia_semana=dia,
                        hora_inicio=time(9, 0),  # 9:00 AM
                        hora_fin=time(18, 0),    # 6:00 PM
                        activo=True
                    )
                    db.session.add(disponibilidad)
                db.session.commit()
                logger.info("Disponibilidad de prueba creada")
        except Exception as e:
            logger.error(f"Error al crear datos de prueba: {e}")
            db.session.rollback()
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todas las pruebas"""
        try:
            # Eliminar bloqueos de prueba
            if cls.tabla_bloqueo_existe:
                BloqueoHorario.query.filter_by(barbero_id=cls.barbero_test.id).delete()
            
            # No eliminamos el barbero de prueba para poder reutilizarlo
            db.session.commit()
        except Exception as e:
            logger.error(f"Error en la limpieza: {e}")
            db.session.rollback()
        
        db.session.remove()
        cls.app_context.pop()
    
    def setUp(self):
        """Configuración para cada prueba"""
        # Limpiar bloqueos anteriores
        if self.tabla_bloqueo_existe:
            BloqueoHorario.query.filter_by(barbero_id=self.barbero_test.id).delete()
            db.session.commit()
    
    def test_01_verificar_tabla_bloqueo(self):
        """Verificar si la tabla BloqueoHorario existe"""
        logger.info("Prueba 1: Verificando existencia de tabla BloqueoHorario")
        inspector = inspect(db.engine)
        self.assertIn('bloqueo_horario', inspector.get_table_names(),
                     "La tabla bloqueo_horario no existe en la base de datos")
        logger.info("✅ La tabla BloqueoHorario existe")
    
    def test_02_crear_bloqueo_horario(self):
        """Probar la creación de un bloqueo de horario"""
        logger.info("Prueba 2: Creando bloqueo de horario")
        if not self.tabla_bloqueo_existe:
            logger.warning("Omitiendo prueba porque la tabla no existe")
            self.skipTest("La tabla bloqueo_horario no existe")
        
        # Fecha de mañana
        fecha_manana = date.today() + timedelta(days=1)
        hora_inicio = time(10, 0)  # 10:00 AM
        hora_fin = time(12, 0)     # 12:00 PM
        
        # Crear bloqueo
        bloqueo, mensaje = self.barbero_test.crear_bloqueo_horario(
            fecha=fecha_manana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            motivo="Prueba de bloqueo"
        )
        
        self.assertIsNotNone(bloqueo, f"No se pudo crear el bloqueo: {mensaje}")
        self.assertEqual(bloqueo.barbero_id, self.barbero_test.id)
        self.assertEqual(bloqueo.fecha, fecha_manana)
        self.assertEqual(bloqueo.hora_inicio, hora_inicio)
        self.assertEqual(bloqueo.hora_fin, hora_fin)
        self.assertEqual(bloqueo.motivo, "Prueba de bloqueo")
        logger.info("✅ Bloqueo creado correctamente")
    
    def test_03_verificar_disponibilidad_con_bloqueo(self):
        """Verificar que un horario bloqueado aparezca como no disponible"""
        logger.info("Prueba 3: Verificando disponibilidad con bloqueo")
        if not self.tabla_bloqueo_existe:
            logger.warning("Omitiendo prueba porque la tabla no existe")
            self.skipTest("La tabla bloqueo_horario no existe")
        
        # Fecha de mañana
        fecha_manana = date.today() + timedelta(days=1)
        hora_inicio = time(14, 0)  # 2:00 PM
        hora_fin = time(16, 0)     # 4:00 PM
        
        # Crear bloqueo
        self.barbero_test.crear_bloqueo_horario(
            fecha=fecha_manana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            motivo="Prueba de disponibilidad"
        )
        
        # Verificar disponibilidad a las 3:00 PM (debería estar bloqueado)
        fecha_hora_bloqueada = datetime.combine(fecha_manana, time(15, 0))
        disponible = self.barbero_test.esta_disponible(fecha_hora_bloqueada)
        
        self.assertFalse(disponible, "El horario debería estar bloqueado")
        logger.info("✅ El bloqueo afecta correctamente la disponibilidad")
        
        # Verificar disponibilidad a las 9:30 AM (debería estar disponible)
        fecha_hora_disponible = datetime.combine(fecha_manana, time(9, 30))
        disponible = self.barbero_test.esta_disponible(fecha_hora_disponible)
        
        self.assertTrue(disponible, "El horario debería estar disponible")
        logger.info("✅ Los horarios fuera del bloqueo siguen disponibles")
    
    def test_04_obtener_horarios_disponibles(self):
        """Verificar que los horarios disponibles excluyan los bloqueados"""
        logger.info("Prueba 4: Verificando obtención de horarios disponibles")
        if not self.tabla_bloqueo_existe:
            logger.warning("Omitiendo prueba porque la tabla no existe")
            self.skipTest("La tabla bloqueo_horario no existe")
        
        # Fecha de mañana
        fecha_manana = date.today() + timedelta(days=1)
        hora_inicio = time(11, 0)  # 11:00 AM
        hora_fin = time(13, 0)     # 1:00 PM
        
        # Crear bloqueo
        self.barbero_test.crear_bloqueo_horario(
            fecha=fecha_manana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            motivo="Prueba de horarios disponibles"
        )
        
        # Obtener horarios disponibles
        slots = self.barbero_test.obtener_horarios_disponibles(fecha_manana)
        
        # Verificar que existen slots
        self.assertTrue(len(slots) > 0, "Debería haber slots disponibles")
        
        # Verificar que los slots bloqueados no estén disponibles
        for slot in slots:
            hora_slot = datetime.strptime(slot['hora'], '%H:%M').time()
            if hora_inicio <= hora_slot < hora_fin:
                self.assertFalse(slot['disponible'], f"El slot {slot['hora']} debería estar bloqueado")
                self.assertTrue('bloqueado' in slot, "El slot debería tener la marca de bloqueado")
        
        logger.info("✅ Los slots bloqueados se marcan correctamente como no disponibles")
    
    def test_05_eliminar_bloqueo(self):
        """Verificar que se pueda eliminar un bloqueo"""
        logger.info("Prueba 5: Eliminando bloqueo")
        if not self.tabla_bloqueo_existe:
            logger.warning("Omitiendo prueba porque la tabla no existe")
            self.skipTest("La tabla bloqueo_horario no existe")
        
        # Fecha de mañana
        fecha_manana = date.today() + timedelta(days=1)
        
        # Crear bloqueo
        bloqueo, _ = self.barbero_test.crear_bloqueo_horario(
            fecha=fecha_manana,
            hora_inicio=time(16, 0),
            hora_fin=time(17, 0),
            motivo="Bloqueo a eliminar"
        )
        
        # Verificar que existe
        self.assertIsNotNone(bloqueo)
        bloqueo_id = bloqueo.id
        
        # Eliminar bloqueo
        exito, mensaje = self.barbero_test.eliminar_bloqueo_horario(bloqueo_id)
        
        self.assertTrue(exito, f"No se pudo eliminar el bloqueo: {mensaje}")
        
        # Verificar que ya no existe
        bloqueo_eliminado = BloqueoHorario.query.get(bloqueo_id)
        self.assertIsNone(bloqueo_eliminado, "El bloqueo no se eliminó correctamente")
        
        logger.info("✅ Bloqueo eliminado correctamente")
    
    def test_06_limpiar_bloqueos_pasados(self):
        """Verificar la limpieza automática de bloqueos pasados"""
        logger.info("Prueba 6: Limpiando bloqueos pasados")
        if not self.tabla_bloqueo_existe:
            logger.warning("Omitiendo prueba porque la tabla no existe")
            self.skipTest("La tabla bloqueo_horario no existe")
        
        # Fecha de ayer
        fecha_ayer = date.today() - timedelta(days=1)
        
        # Crear bloqueo pasado
        bloqueo, _ = self.barbero_test.crear_bloqueo_horario(
            fecha=fecha_ayer,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            motivo="Bloqueo pasado"
        )
        
        # Forzar la creación (normalmente no se permite crear bloqueos pasados)
        if not bloqueo:
            bloqueo = BloqueoHorario(
                barbero_id=self.barbero_test.id,
                fecha=fecha_ayer,
                hora_inicio=time(10, 0),
                hora_fin=time(11, 0),
                motivo="Bloqueo pasado"
            )
            db.session.add(bloqueo)
            db.session.commit()
        
        # Ejecutar limpieza
        bloqueos_eliminados = limpiar_bloqueos_pasados()
        
        self.assertTrue(bloqueos_eliminados > 0, "No se eliminaron bloqueos pasados")
        
        # Verificar que el bloqueo pasado ya no existe
        bloqueos_pasados = BloqueoHorario.query.filter_by(
            barbero_id=self.barbero_test.id,
            fecha=fecha_ayer
        ).count()
        
        self.assertEqual(bloqueos_pasados, 0, "No se eliminaron todos los bloqueos pasados")
        
        logger.info(f"✅ Se eliminaron {bloqueos_eliminados} bloqueos pasados")
    
    def test_07_manejo_errores_sin_tabla(self):
        """Verificar el manejo de errores cuando la tabla no existe"""
        logger.info("Prueba 7: Verificando manejo de errores sin tabla")
        
        # Simular que la tabla no existe
        inspector = inspect(db.engine)
        tabla_existe = 'bloqueo_horario' in inspector.get_table_names()
        
        if not tabla_existe:
            # Intentar crear un bloqueo
            bloqueo, mensaje = self.barbero_test.crear_bloqueo_horario(
                fecha=date.today() + timedelta(days=1),
                hora_inicio=time(10, 0),
                hora_fin=time(11, 0),
                motivo="Prueba de error"
            )
            
            self.assertIsNone(bloqueo, "Debería fallar al crear un bloqueo sin tabla")
            self.assertIn("no está disponible", mensaje, "El mensaje de error debería ser claro")
            
            logger.info("✅ Manejo correcto de errores cuando la tabla no existe")
        else:
            logger.info("La tabla existe, omitiendo prueba de manejo de errores")
            self.skipTest("La tabla bloqueo_horario existe, no se puede probar el manejo de errores")

def ejecutar_pruebas():
    """Ejecutar todas las pruebas"""
    logger.info("=== INICIANDO PRUEBAS DE HORARIOS DE BARBEROS ===")
    
    # Crear suite de pruebas ordenada
    suite = unittest.TestSuite()
    suite.addTest(TestHorariosBarbero('test_01_verificar_tabla_bloqueo'))
    suite.addTest(TestHorariosBarbero('test_02_crear_bloqueo_horario'))
    suite.addTest(TestHorariosBarbero('test_03_verificar_disponibilidad_con_bloqueo'))
    suite.addTest(TestHorariosBarbero('test_04_obtener_horarios_disponibles'))
    suite.addTest(TestHorariosBarbero('test_05_eliminar_bloqueo'))
    suite.addTest(TestHorariosBarbero('test_06_limpiar_bloqueos_pasados'))
    suite.addTest(TestHorariosBarbero('test_07_manejo_errores_sin_tabla'))
    
    # Ejecutar pruebas
    resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Mostrar resumen
    logger.info("=== RESUMEN DE PRUEBAS ===")
    logger.info(f"Total de pruebas: {resultado.testsRun}")
    logger.info(f"Pruebas exitosas: {resultado.testsRun - len(resultado.errors) - len(resultado.failures)}")
    logger.info(f"Errores: {len(resultado.errors)}")
    logger.info(f"Fallos: {len(resultado.failures)}")
    
    if resultado.errors:
        logger.error("=== ERRORES ===")
        for test, error in resultado.errors:
            logger.error(f"{test}: {error}")
    
    if resultado.failures:
        logger.error("=== FALLOS ===")
        for test, failure in resultado.failures:
            logger.error(f"{test}: {failure}")
    
    logger.info("=== FIN DE PRUEBAS ===")
    
    return len(resultado.errors) == 0 and len(resultado.failures) == 0

def verificar_migraciones():
    """Verificar si se necesitan migraciones"""
    logger.info("=== VERIFICANDO MIGRACIONES ===")
    
    try:
        inspector = inspect(db.engine)
        if 'bloqueo_horario' not in inspector.get_table_names():
            logger.warning("La tabla bloqueo_horario no existe en la base de datos.")
            logger.warning("Es necesario ejecutar migraciones para crear esta tabla.")
            logger.warning("Ejecuta los siguientes comandos:")
            logger.warning("1. flask db migrate -m 'Agregar tabla BloqueoHorario'")
            logger.warning("2. flask db upgrade")
            return False
        else:
            logger.info("✅ La tabla bloqueo_horario existe en la base de datos")
            return True
    except Exception as e:
        logger.error(f"Error al verificar migraciones: {e}")
        return False

def verificar_interfaz_movil():
    """Verificar configuración de interfaz móvil"""
    logger.info("=== VERIFICANDO INTERFAZ MÓVIL ===")
    
    try:
        # Verificar si existen las clases CSS necesarias
        with open('app/static/css/admin_styles.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        clases_necesarias = [
            '.desktop-only',
            '.mobile-only',
            '.mobile-card',
            '.mobile-card-header',
            '.mobile-card-body',
            '.mobile-card-field.full-width'
        ]
        
        for clase in clases_necesarias:
            if clase not in css_content:
                logger.warning(f"No se encontró la clase CSS '{clase}' en admin_styles.css")
                return False
        
        # Verificar si la plantilla usa las clases
        with open('app/templates/barbero/horarios.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        elementos_necesarios = [
            'desktop-only',
            'mobile-only',
            'mobile-card',
            'mobile-card-header',
            'mobile-card-body',
            'mobile-card-field'
        ]
        
        for elemento in elementos_necesarios:
            if elemento not in template_content:
                logger.warning(f"No se encontró el elemento '{elemento}' en la plantilla horarios.html")
                return False
        
        logger.info("✅ La interfaz móvil está configurada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al verificar la interfaz móvil: {e}")
        return False

if __name__ == '__main__':
    # Verificar migraciones
    migraciones_ok = verificar_migraciones()
    
    # Verificar interfaz móvil
    interfaz_movil_ok = verificar_interfaz_movil()
    
    # Ejecutar pruebas
    pruebas_ok = ejecutar_pruebas()
    
    # Mostrar resumen final
    logger.info("\n=== RESUMEN FINAL ===")
    logger.info(f"Migraciones: {'✅ OK' if migraciones_ok else '❌ Se requieren migraciones'}")
    logger.info(f"Interfaz móvil: {'✅ OK' if interfaz_movil_ok else '❌ Configuración incompleta'}")
    logger.info(f"Pruebas unitarias: {'✅ OK' if pruebas_ok else '❌ Hay errores o fallos'}")
    
    # Salir con código de error si algo falló
    if not (migraciones_ok and interfaz_movil_ok and pruebas_ok):
        sys.exit(1)
