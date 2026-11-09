DB_CONFIG = {
    'server': 'LOCALHOST',        # Tu servidor o instancia (ej: 'localhost\SQLEXPRESS')
    'database': 'DB_Creditos',    # Nombre correcto de tu base de datos
    'driver': '{ODBC Driver 17 for SQL Server}'
} 
////////////////////////////////////////////////////////////////////////////////////////////////////
DB_CONFIG = {
    'server': 'LOCALHOST',        # Tu servidor o instancia (ej: 'localhost\SQLEXPRESS')
    'database': 'DB_Creditos',    # Nombre correcto de tu base de datos
    'driver': '{ODBC Driver 17 for SQL Server}'
}


//////////////////////////////////////////////////////////////////////////////////////////////////
USE DB_Creditos;
GO

-- Agregar la columna para almacenar la huella SHA-256 (64 caracteres hexadecimales)
ALTER TABLE dbo.ETL_Log 
ADD ChecksumHash VARCHAR(64) NULL;
GO

import hashlib

def calcular_checksum_archivo(ruta_archivo):
    """Calcula el hash SHA-256 de un archivo leyéndolo en bloques de 4KB."""
    sha256_hash = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def archivo_ya_procesado(conn, checksum_hash):
    """Consulta si el checksum ya fue registrado con estado EXITO previamente."""
    query = """
        SELECT COUNT(1) 
        FROM dbo.ETL_Log 
        WHERE ChecksumHash = ? AND Estado = 'EXITO';
    """
    cursor = conn.cursor()
    cursor.execute(query, (checksum_hash,))
    count = cursor.fetchone()[0]
    return count > 0

def ejecutar_pipeline_etl(fecha_particion=None, ruta_excel=None):
    tiempo_inicio = time.time()
    
    if ruta_excel is None:
        ruta_excel = obtener_archivo_excel(CARPETA_ENTRADA)
        
    if ruta_excel is None:
        print("No se encontraron archivos Excel para procesar.")
        return

    nombre_archivo = os.path.basename(ruta_excel)
    
    # 1. Calcular el checksum del archivo
    checksum = calcular_checksum_archivo(ruta_excel)
    print(f"--- Procesando archivo: {nombre_archivo} | SHA256: {checksum[:10]}... ---")

    conn = pyodbc.connect(CONN_STR)
    
    # 2. Validar si el archivo ya fue ingestado previamente
    if archivo_ya_procesado(conn, checksum):
        print(f" WARN: El archivo {nombre_archivo} (Checksum: {checksum}) ya fue procesado anteriormente con éxito. Se omite la carga.")
        conn.close()
        # Opcional: Mover a carpeta procesados
        mover_archivo(ruta_excel, CARPETA_PROCESADOS)
        return

    # 3. Continuar con la ingesta y pasar el 'checksum' al momento de registrar el log
    # registrar_log(conn, nombre_archivo, fecha_particion, reg_leidos, reg_insertados, 'EXITO', 'Ingesta exitosa', tiempo_total, checksum)

    3. Ajuste a la función registrar_log
Actualiza la llamada SQL para incluir el campo ChecksumHash:

def registrar_log(conn, nombre_archivo, fecha_reporte, reg_leidos, reg_insertados, estado, mensaje, tiempo_sec, checksum):
    query_log = """
        INSERT INTO dbo.ETL_Log 
        (NombreArchivo, FechaReporte, RegistrosLeidos, RegistrosInsertados, Estado, MensajeDetalle, TiempoEjecucionSegundos, ChecksumHash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """
    cursor = conn.cursor()
    cursor.execute(query_log, (nombre_archivo, fecha_reporte, reg_leidos, reg_insertados, estado, mensaje, tiempo_sec, checksum))
    conn.commit()


    USE [master];
GO

RESTORE DATABASE [DB_Creditos]
FROM DISK = N'C:\Temp\DB_Creditos_Backup.bak'
WITH FILE = 1, 
     NOUNLOAD, 
     STATS = 5;
GO