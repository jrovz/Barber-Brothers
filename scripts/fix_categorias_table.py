#!/usr/bin/env python
"""
Script para crear y poblar la tabla de categorías en SQLite o PostgreSQL

Este script soluciona el error "no such table: categorias" verificando si la tabla
existe y creándola si es necesario, con datos iniciales.
"""
import os
import sys
import argparse
import logging
from sqlalchemy import create_engine, text, Table, Column, Integer, String, DateTime, MetaData
from datetime import datetime
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("fix_categorias_table")

def get_db_connection(db_type="sqlite", db_path=None, postgres_url=None):
    """
    Obtiene conexión a SQLite o PostgreSQL según el tipo especificado
    """
    try:
        if db_type.lower() == "sqlite":
            # Determinar la ruta de la base de datos SQLite
            if not db_path:
                basedir = os.path.abspath(os.path.dirname(__file__))
                parent_dir = os.path.dirname(basedir)
                # Buscar en instance/app.db
                db_path = os.path.join(parent_dir, 'instance', 'app.db')
                if not os.path.exists(db_path):
                    # Buscar en la raíz
                    db_path = os.path.join(parent_dir, 'app.db')
                    if not os.path.exists(db_path):
                        logger.error("No se encontró la base de datos SQLite")
                        return None
            
            db_url = f"sqlite:///{db_path}"
            logger.info(f"Conectando a SQLite: {db_path}")
        
        elif db_type.lower() == "postgres":
            # Usar la URL de PostgreSQL proporcionada o construirla
            if postgres_url:
                db_url = postgres_url
            else:
                # Intentar construir la URL con variables de entorno
                db_user = os.environ.get("DB_USER", "barberia_user")
                db_pass = os.environ.get("DB_PASS", "")
                db_name = os.environ.get("DB_NAME", "barberia_db")
                db_host = os.environ.get("DB_HOST", "localhost")
                db_port = os.environ.get("DB_PORT", "5432")
                
                # Construir la URL para PostgreSQL
                db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            
            logger.info(f"Conectando a PostgreSQL: {db_url}")
        
        else:
            logger.error(f"Tipo de base de datos no soportado: {db_type}")
            return None
        
        # Crear el motor y verificar la conexión
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                logger.info("Conexión a la base de datos establecida exitosamente")
                return engine
            else:
                logger.error("Error en la consulta de prueba")
                return None
    
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        traceback.print_exc()
        return None

def check_table_exists(engine, table_name):
    """
    Verifica si una tabla existe en la base de datos
    """
    try:
        with engine.connect() as conn:
            if engine.dialect.name == 'sqlite':
                result = conn.execute(text(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                ))
            elif engine.dialect.name == 'postgresql':
                result = conn.execute(text(
                    f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='{table_name}')"
                ))
            else:
                logger.error(f"Dialecto de base de datos no soportado: {engine.dialect.name}")
                return False
            
            exists = bool(result.scalar())
            if exists:
                logger.info(f"La tabla '{table_name}' existe")
            else:
                logger.warning(f"La tabla '{table_name}' no existe")
            return exists
    
    except Exception as e:
        logger.error(f"Error al verificar si la tabla existe: {e}")
        traceback.print_exc()
        return False

def create_categorias_table(engine):
    """
    Crea la tabla 'categorias' en la base de datos
    """
    try:
        metadata = MetaData()
        
        # Definir la tabla categorias
        categorias = Table(
            'categorias', 
            metadata,
            Column('id', Integer, primary_key=True),
            Column('nombre', String(100), nullable=False, unique=True),
            Column('creado', DateTime, default=datetime.utcnow),
            Column('actualizado', DateTime, default=datetime.utcnow)
        )
        
        # Crear la tabla
        metadata.create_all(engine)
        logger.info("Tabla 'categorias' creada exitosamente")
        
        # Insertar datos iniciales
        with engine.connect() as conn:
            categorias_iniciales = [
                {"nombre": "Productos para el cabello"},
                {"nombre": "Productos para la barba"},
                {"nombre": "Accesorios"},
                {"nombre": "Productos de afeitado"},
                {"nombre": "Cuidado facial"},
                {"nombre": "Otros"}
            ]
            
            for cat in categorias_iniciales:
                conn.execute(
                    text("INSERT INTO categorias (nombre, creado, actualizado) VALUES (:nombre, :creado, :actualizado)"),
                    {"nombre": cat["nombre"], "creado": datetime.utcnow(), "actualizado": datetime.utcnow()}
                )
            
            conn.commit()
        
        logger.info(f"Se insertaron {len(categorias_iniciales)} categorías iniciales")
        return True
    
    except Exception as e:
        logger.error(f"Error al crear la tabla 'categorias': {e}")
        traceback.print_exc()
        return False

def sync_categorias_between_dbs():
    """
    Sincroniza las categorías entre SQLite y PostgreSQL
    """
    try:
        # Conectar a ambas bases de datos
        sqlite_engine = get_db_connection("sqlite")
        postgres_engine = get_db_connection("postgres")
        
        if not sqlite_engine or not postgres_engine:
            logger.error("No se pudo conectar a ambas bases de datos")
            return False
        
        # Verificar si existen las tablas en ambas bases de datos
        sqlite_has_table = check_table_exists(sqlite_engine, "categorias")
        postgres_has_table = check_table_exists(postgres_engine, "categorias")
        
        # Si ninguna tiene la tabla, crearla en ambas
        if not sqlite_has_table and not postgres_has_table:
            logger.info("Creando tabla 'categorias' en ambas bases de datos...")
            create_categorias_table(sqlite_engine)
            create_categorias_table(postgres_engine)
            return True
        
        # Si una tiene la tabla pero la otra no, sincronizar
        if sqlite_has_table and not postgres_has_table:
            logger.info("Sincronizando tabla 'categorias' de SQLite a PostgreSQL...")
            # Obtener datos de SQLite
            with sqlite_engine.connect() as conn:
                result = conn.execute(text("SELECT nombre FROM categorias"))
                categorias = [row[0] for row in result.fetchall()]
            
            # Crear tabla en PostgreSQL
            create_categorias_table(postgres_engine)
            
            # Insertar las categorías adicionales de SQLite que no estén en las iniciales
            with postgres_engine.connect() as conn:
                for nombre in categorias:
                    conn.execute(
                        text("INSERT INTO categorias (nombre, creado, actualizado) VALUES (:nombre, :creado, :actualizado) ON CONFLICT (nombre) DO NOTHING"),
                        {"nombre": nombre, "creado": datetime.utcnow(), "actualizado": datetime.utcnow()}
                    )
                conn.commit()
            
            logger.info("Sincronización completada")
            return True
            
        elif postgres_has_table and not sqlite_has_table:
            logger.info("Sincronizando tabla 'categorias' de PostgreSQL a SQLite...")
            # Obtener datos de PostgreSQL
            with postgres_engine.connect() as conn:
                result = conn.execute(text("SELECT nombre FROM categorias"))
                categorias = [row[0] for row in result.fetchall()]
            
            # Crear tabla en SQLite
            create_categorias_table(sqlite_engine)
            
            # Insertar las categorías adicionales de PostgreSQL
            with sqlite_engine.connect() as conn:
                for nombre in categorias:
                    try:
                        conn.execute(
                            text("INSERT INTO categorias (nombre, creado, actualizado) VALUES (:nombre, :creado, :actualizado)"),
                            {"nombre": nombre, "creado": datetime.utcnow(), "actualizado": datetime.utcnow()}
                        )
                    except Exception as e:
                        logger.warning(f"No se pudo insertar categoría '{nombre}': {e}")
                conn.commit()
            
            logger.info("Sincronización completada")
            return True
        
        # Si ambas tienen la tabla, verificar que tengan los mismos datos
        logger.info("Ambas bases de datos tienen la tabla 'categorias'. Verificando sincronización...")
        
        # Obtener categorías de ambas bases de datos
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT nombre FROM categorias"))
            sqlite_categorias = set([row[0] for row in result.fetchall()])
        
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT nombre FROM categorias"))
            postgres_categorias = set([row[0] for row in result.fetchall()])
        
        # Verificar diferencias
        sqlite_only = sqlite_categorias - postgres_categorias
        postgres_only = postgres_categorias - sqlite_categorias
        
        # Sincronizar diferencias
        if sqlite_only:
            logger.info(f"Categorías en SQLite que no están en PostgreSQL: {', '.join(sqlite_only)}")
            with postgres_engine.connect() as conn:
                for nombre in sqlite_only:
                    conn.execute(
                        text("INSERT INTO categorias (nombre, creado, actualizado) VALUES (:nombre, :creado, :actualizado)"),
                        {"nombre": nombre, "creado": datetime.utcnow(), "actualizado": datetime.utcnow()}
                    )
                conn.commit()
        
        if postgres_only:
            logger.info(f"Categorías en PostgreSQL que no están en SQLite: {', '.join(postgres_only)}")
            with sqlite_engine.connect() as conn:
                for nombre in postgres_only:
                    conn.execute(
                        text("INSERT INTO categorias (nombre, creado, actualizado) VALUES (:nombre, :creado, :actualizado)"),
                        {"nombre": nombre, "creado": datetime.utcnow(), "actualizado": datetime.utcnow()}
                    )
                conn.commit()
        
        if not sqlite_only and not postgres_only:
            logger.info("Las categorías están sincronizadas entre ambas bases de datos")
        else:
            logger.info("Sincronización completada")
        
        return True
    
    except Exception as e:
        logger.error(f"Error al sincronizar categorías: {e}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Crear y poblar la tabla de categorías')
    parser.add_argument('--db-type', choices=['sqlite', 'postgres', 'both'], default='sqlite', 
                      help='Tipo de base de datos a usar (sqlite, postgres o both)')
    parser.add_argument('--db-path', help='Ruta de la base de datos SQLite (opcional)')
    parser.add_argument('--postgres-url', help='URL de conexión a PostgreSQL (opcional)')
    parser.add_argument('--sync', action='store_true', help='Sincronizar categorías entre SQLite y PostgreSQL')
    
    args = parser.parse_args()
    
    if args.sync:
        logger.info("Iniciando sincronización de categorías entre SQLite y PostgreSQL...")
        success = sync_categorias_between_dbs()
        return 0 if success else 1
    
    if args.db_type == 'both':
        # Crear tabla en ambas bases de datos
        sqlite_engine = get_db_connection("sqlite", args.db_path)
        postgres_engine = get_db_connection("postgres", None, args.postgres_url)
        
        if not sqlite_engine or not postgres_engine:
            logger.error("No se pudo conectar a ambas bases de datos")
            return 1
        
        sqlite_success = False
        postgres_success = False
        
        if not check_table_exists(sqlite_engine, "categorias"):
            sqlite_success = create_categorias_table(sqlite_engine)
        else:
            logger.info("La tabla 'categorias' ya existe en SQLite")
            sqlite_success = True
        
        if not check_table_exists(postgres_engine, "categorias"):
            postgres_success = create_categorias_table(postgres_engine)
        else:
            logger.info("La tabla 'categorias' ya existe en PostgreSQL")
            postgres_success = True
        
        return 0 if sqlite_success and postgres_success else 1
    
    else:
        # Crear tabla en la base de datos especificada
        engine = get_db_connection(args.db_type, args.db_path, args.postgres_url)
        
        if not engine:
            logger.error(f"No se pudo conectar a la base de datos {args.db_type}")
            return 1
        
        if not check_table_exists(engine, "categorias"):
            success = create_categorias_table(engine)
            return 0 if success else 1
        else:
            logger.info(f"La tabla 'categorias' ya existe en {args.db_type}")
            return 0

if __name__ == "__main__":
    sys.exit(main())
