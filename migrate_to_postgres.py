"""
Script para migrar datos de MySQL a PostgreSQL 

Este script realiza una migración de datos desde una base de datos MySQL
a una base de datos PostgreSQL.

Uso:
    python migrate_to_postgres.py

Requisitos:
    - Variables de entorno configuradas para ambas bases de datos
    - Estructura de tablas compatible entre ambas bases de datos
"""

import os
import sys
import json
import time
import logging
import pandas as pd
import sqlalchemy

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("migrate_to_postgres")

# Configuración de variables de entorno
MYSQL_DATABASE_URL = os.environ.get('MYSQL_DATABASE_URL')
POSTGRES_DATABASE_URL = os.environ.get('DATABASE_URL')  # La nueva URL de PostgreSQL

def get_table_names(engine):
    """Obtiene la lista de tablas de la base de datos"""
    try:
        inspector = sqlalchemy.inspect(engine)
        return inspector.get_table_names()
    except Exception as e:
        logger.error(f"Error obteniendo tablas: {e}")
        return []

def migrate_table(mysql_engine, postgres_engine, table_name, batch_size=1000):
    """Migra los datos de una tabla de MySQL a PostgreSQL"""
    logger.info(f"Migrando tabla: {table_name}")
    
    try:
        # Obtener la estructura de columnas para manejar tipos de datos
        mysql_inspector = sqlalchemy.inspect(mysql_engine)
        columns = mysql_inspector.get_columns(table_name)
        column_names = [col['name'] for col in columns]
        
        # Contar registros para estimar el progreso
        count_query = f"SELECT COUNT(*) FROM {table_name}"
        count_result = mysql_engine.execute(count_query).scalar()
        logger.info(f"Total de registros a migrar: {count_result}")
        
        # Realizar la migración por lotes para tablas grandes
        offset = 0
        migrated_count = 0
        
        while True:
            query = f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}"
            df = pd.read_sql(query, mysql_engine)
            
            if df.empty:
                break
                
            # Reemplazar valores NaN por NULL en el DataFrame
            df = df.where(pd.notnull(df), None)
            
            # Insertar los datos en PostgreSQL
            df.to_sql(
                table_name, 
                postgres_engine, 
                if_exists='append', 
                index=False,
                method='multi'
            )
            
            rows_migrated = len(df)
            migrated_count += rows_migrated
            logger.info(f"Migrados {migrated_count}/{count_result} registros de {table_name}")
            
            if rows_migrated < batch_size:
                break
                
            offset += batch_size
            
        logger.info(f"Migración de tabla {table_name} completada. {migrated_count} registros migrados.")
        return True
        
    except Exception as e:
        logger.error(f"Error migrando tabla {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_data():
    """Función principal para migrar todos los datos"""
    if not MYSQL_DATABASE_URL:
        logger.error("MYSQL_DATABASE_URL no está definida")
        return False
        
    if not POSTGRES_DATABASE_URL:
        logger.error("DATABASE_URL (PostgreSQL) no está definida")
        return False
    
    try:
        logger.info("Iniciando proceso de migración de datos...")
        
        # Conectar a ambas bases de datos
        mysql_engine = sqlalchemy.create_engine(MYSQL_DATABASE_URL)
        postgres_engine = sqlalchemy.create_engine(POSTGRES_DATABASE_URL)
        
        # Verificar conexiones
        mysql_engine.execute("SELECT 1")
        postgres_engine.execute("SELECT 1")
        
        # Obtener tablas de MySQL
        tables = get_table_names(mysql_engine)
        logger.info(f"Tablas encontradas en MySQL: {tables}")
        
        if not tables:
            logger.error("No se encontraron tablas para migrar")
            return False
        
        # Realizar migración por cada tabla
        results = {}
        for table in tables:
            success = migrate_table(mysql_engine, postgres_engine, table)
            results[table] = "OK" if success else "ERROR"
        
        # Mostrar resumen
        logger.info("Resumen de migración:")
        for table, status in results.items():
            logger.info(f"  {table}: {status}")
        
        return all(status == "OK" for status in results.values())
        
    except Exception as e:
        logger.error(f"Error en el proceso de migración: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Iniciando script de migración de MySQL a PostgreSQL")
    success = migrate_data()
    if success:
        logger.info("Migración de datos completada con éxito")
        sys.exit(0)
    else:
        logger.error("Migración de datos falló")
        sys.exit(1)
