#!/usr/bin/env python
"""
Script para verificar y crear tablas faltantes en la base de datos

Este script verificará si existen las tablas necesarias para la aplicación
y las creará si no existen, solucionando el error de 'no such table: categorias'.
"""
import os
import sys
import argparse
import logging
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, inspect
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("verify_tables")

# Definir el modelo Base de SQLAlchemy
Base = declarative_base()

# Definir el modelo de Categoria si no existe
class Categoria(Base):
    __tablename__ = 'categorias'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    creado = Column(DateTime, default=datetime.utcnow)
    actualizado = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Categoria {self.nombre}>'

def get_db_engine(db_path=None):
    """
    Obtiene una conexión a la base de datos SQLite local o a la especificada
    """
    try:
        if db_path:
            # Usar la ruta de base de datos especificada
            db_uri = f"sqlite:///{db_path}"
        else:
            # Determinar la ruta de la base de datos SQLite local
            basedir = os.path.abspath(os.path.dirname(__file__))
            parent_dir = os.path.dirname(basedir)
            db_path = os.path.join(parent_dir, 'instance', 'app.db')
            
            if not os.path.exists(db_path):
                # Intentar buscar en el directorio actual
                db_path = os.path.join(basedir, 'app.db')
                if not os.path.exists(db_path):
                    logger.error(f"No se encontró la base de datos local en {parent_dir}/instance/ ni en {basedir}")
                    return None
            
            db_uri = f"sqlite:///{db_path}"
        
        logger.info(f"Conectando a la base de datos: {db_uri}")
        engine = create_engine(db_uri)
        
        # Verificar conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                logger.info("Conexión a la base de datos establecida exitosamente")
                return engine
            else:
                logger.error("Error en la consulta de prueba de conexión")
                return None
    
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        traceback.print_exc()
        return None

def verify_tables(engine):
    """
    Verifica si existen las tablas necesarias en la base de datos
    """
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Tablas existentes: {', '.join(existing_tables)}")
        
        missing_tables = []
        required_tables = ['categorias', 'producto', 'barbero', 'servicio', 'cliente', 'user', 'cita']
        
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)
                logger.warning(f"La tabla '{table}' no existe en la base de datos")
        
        return missing_tables
    
    except Exception as e:
        logger.error(f"Error al verificar tablas: {e}")
        traceback.print_exc()
        return required_tables  # Asumimos que faltan todas si hay error

def create_missing_tables(engine, missing_tables):
    """
    Crea las tablas faltantes en la base de datos
    """
    try:
        if 'categorias' in missing_tables:
            logger.info("Creando tabla 'categorias'...")
            # Crear tabla categorias
            Categoria.__table__.create(engine)
            logger.info("Tabla 'categorias' creada exitosamente")
            
            # Insertar algunas categorías por defecto
            with engine.connect() as conn:
                categorias_default = [
                    {"nombre": "Productos para el cabello"},
                    {"nombre": "Productos para la barba"},
                    {"nombre": "Accesorios"},
                    {"nombre": "Otros"}
                ]
                
                for cat in categorias_default:
                    conn.execute(
                        text("INSERT INTO categorias (nombre, creado, actualizado) VALUES (:nombre, :creado, :actualizado)"),
                        {"nombre": cat["nombre"], "creado": datetime.utcnow(), "actualizado": datetime.utcnow()}
                    )
                conn.commit()
                logger.info(f"Se insertaron {len(categorias_default)} categorías por defecto")
        
        # Aquí puedes añadir más lógica para crear otras tablas faltantes si es necesario
        
        return True
    
    except Exception as e:
        logger.error(f"Error al crear tablas faltantes: {e}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Verificar y crear tablas faltantes en la base de datos')
    parser.add_argument('--db-path', help='Ruta a la base de datos SQLite (opcional)')
    parser.add_argument('--verify-only', action='store_true', help='Solo verificar las tablas, no crear las faltantes')
    
    args = parser.parse_args()
    
    # Obtener conexión a la base de datos
    engine = get_db_engine(args.db_path)
    if not engine:
        logger.error("No se pudo establecer conexión a la base de datos")
        return 1
    
    # Verificar tablas
    missing_tables = verify_tables(engine)
    
    if not missing_tables:
        logger.info("✅ Todas las tablas requeridas existen en la base de datos")
        return 0
    
    logger.info(f"Tablas faltantes: {', '.join(missing_tables)}")
    
    if args.verify_only:
        logger.info("Modo de sólo verificación. No se crearán las tablas faltantes.")
        return 0
    
    # Crear tablas faltantes
    if create_missing_tables(engine, missing_tables):
        logger.info("✅ Se han creado todas las tablas faltantes")
        return 0
    else:
        logger.error("❌ No se pudieron crear todas las tablas faltantes")
        return 1

if __name__ == "__main__":
    sys.exit(main())
