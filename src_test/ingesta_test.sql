import os
from datetime import datetime
import pyodbc

# ==============================================================================
# 1. CONFIGURACIÓN DE CONEXIÓN A SQL SERVER
# ==============================================================================
DB_CONFIG = {
    'server': 'LOCALHOST',         # Nombre del servidor o dirección IP (ej: '127.0.0.1' o 'localhost\SQLEXPRESS')
    'database': 'DB_Finanzas',     # Nombre de tu base de datos
    'driver': '{ODBC Driver 17 for SQL Server}'  # Asegúrate de tener instalado este driver de ODBC
    # Para autenticación de SQL Server usa: 'user': 'tu_usuario', 'password': 'tu_password'
}

# Cadena de conexión usando Autenticación de Windows (Trusted_Connection=yes)
CONN_STR = (
    f"DRIVER={DB_CONFIG['driver']};"
    f"SERVER={DB_CONFIG['server']};"
    f"DATABASE={DB_CONFIG['database']};"
    "Trusted_Connection=yes;"
)

def leer_archivo_sql(ruta_archivo):
    """Lee el contenido de un archivo .sql"""
    with open(ruta_archivo, 'r', encoding='utf-8') as file:
        return file.read()

def ejecutar_ingesta_diaria(fecha_particion=None):
    # ==============================================================================
    # 2. MANEJO DINÁMICO DE LA FECHA DE LA PARTICIÓN
    # ==============================================================================
    # Si no se pasa fecha, toma la fecha de hoy en formato entero YYYYMMDD (Ej: 20261106)
    if fecha_particion is None:
        fecha_particion = int(datetime.now().strftime('%Y%m%d'))

    print(f"--- Iniciando ingesta para la fecha de partición: {fecha_particion} ---")

    # Rutas a los archivos .sql
    base_dir = os.path.dirname(__file__)
    sql_insert_path = os.path.join(base_dir, 'scripts_sql', '01_insert_staging.sql')
    sql_exec_path = os.path.join(base_dir, 'scripts_sql', '02_exec_procedimiento.sql')

    # Cargar las plantillas de consultas SQL
    query_insert_template = leer_archivo_sql(sql_insert_path)
    query_exec_template = leer_archivo_sql(sql_exec_path)

    # Inyectar el valor de la fecha dinámica en las consultas
    query_insert = query_insert_template.format(fecha_reporte=fecha_particion)
    query_exec = query_exec_template.format(fecha_reporte=fecha_particion)

    # ==============================================================================
    # 3. EJECUCIÓN EN SQL SERVER CON TRANSACCIÓN
    # ==============================================================================
    conn = None
    try:
        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()

        # Paso A: Insertar los registros en la tabla Staging[cite: 1]
        print("1. Insertando registros en dbo.Staging_FactCreditos...")
        cursor.execute(query_insert)

        # Paso B: Ejecutar el procedimiento de ingesta particionada[cite: 1]
        print("2. Ejecutando dbo.usp_IngresarCreditosDiarios...")
        cursor.execute(query_exec)

        # Confirmar los cambios de forma atómica en la base de datos
        conn.commit()
        print(f" SUCCESS: Ingesta completada con éxito para la partición {fecha_particion}.")

    except Exception as e:
        if conn:
            conn.rollback() # Si algo falla, revierte todos los cambios
        print(f" ERROR durante la ejecución: {str(e)}")
        raise e

    finally:
        if conn:
            conn.close()

# ==============================================================================
# EJECUCIÓN DEL SCRIPT
# ==============================================================================
if __name__ == '__main__':
    # Opción 1: Ejecutar dinámicamente con la fecha actual del sistema
    ejecutar_ingesta_diaria()
    
    # Opción 2: O pasar explícitamente cualquier fecha en formato YYYYMMDD
    # ejecutar_ingesta_diaria(fecha_particion=20261001)