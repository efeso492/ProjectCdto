USE DB_Finanzas;
GO

IF OBJECT_ID('dbo.ETL_Log', 'U') IS NOT NULL
    DROP TABLE dbo.ETL_Log;
GO

CREATE TABLE dbo.ETL_Log
(
    LogID INT IDENTITY(1,1) CONSTRAINT PK_ETL_Log PRIMARY KEY CLUSTERED,
    FechaEjecucion DATETIME NOT NULL CONSTRAINT DF_ETL_Log_Fecha DEFAULT GETDATE(),
    NombreArchivo VARCHAR(255) NOT NULL,
    FechaReporte INT NULL,
    RegistrosLeidos INT NULL,
    RegistrosInsertados INT NULL,
    Estado VARCHAR(20) NOT NULL, -- 'EXITO' o 'ERROR'
    MensajeDetalle VARCHAR(MAX) NULL,
    TiempoEjecucionSegundos DECIMAL(10,2) NULL
);
GO

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
import os
import glob
import shutil
import time
from datetime import datetime
import pandas as pd
import pyodbc

# ==============================================================================
# 1. CONFIGURACIÓN DE RUTAS Y CONEXIÓN A SQL SERVER
# ==============================================================================
DB_CONFIG = {
    'server': 'LOCALHOST',        # Nombre del servidor o IP (ej: 'localhost\SQLEXPRESS')
    'database': 'DB_Finanzas',    # Base de datos destino[cite: 1]
    'driver': '{ODBC Driver 17 for SQL Server}'
}

CONN_STR = (
    f"DRIVER={DB_CONFIG['driver']};"
    f"SERVER={DB_CONFIG['server']};"
    f"DATABASE={DB_CONFIG['database']};"
    "Trusted_Connection=yes;"
)

# Rutas de carpetas de trabajo
CARPETA_ENTRADA = r'C:\archivos_excel_ingesta'
CARPETA_PROCESADOS = os.path.join(CARPETA_ENTRADA, 'procesados')
CARPETA_ERRORES = os.path.join(CARPETA_ENTRADA, 'errores')

# ==============================================================================
# 2. FUNCIONES DE APOYO
# ==============================================================================
def obtener_archivo_excel(carpeta):
    """Obtiene el archivo Excel más reciente en la carpeta de entrada."""
    patrones = [os.path.join(carpeta, '*.xlsx'), os.path.join(carpeta, '*.xls')]
    archivos = []
    for p in patrones:
        archivos.extend(glob.glob(p))
    
    # Filtrar archivos temporales de Excel que empiezan con ~$
    archivos = [f for f in archivos if not os.path.basename(f).startswith('~$')]
    
    if not archivos:
        return None
    
    archivos.sort(key=os.path.getmtime, reverse=True)
    return archivos[0]

def mover_archivo(ruta_origen, carpeta_destino_base):
    """Mueve el archivo a una subcarpeta YYYY-MM según la fecha actual."""
    subcarpeta_mes = datetime.now().strftime('%Y-%m')
    destino_dir = os.path.join(carpeta_destino_base, subcarpeta_mes)
    os.makedirs(destino_dir, exist_ok=True)
    
    nombre_archivo = os.path.basename(ruta_origen)
    destino_final = os.path.join(destino_dir, nombre_archivo)
    
    # Si ya existe un archivo con el mismo nombre en destino, agregar timestamp
    if os.path.exists(destino_final):
        timestamp = datetime.now().strftime('%H%M%S_')
        destino_final = os.path.join(destino_dir, timestamp + nombre_archivo)
        
    shutil.move(ruta_origen, destino_final)
    return destino_final

def registrar_log(conn, nombre_archivo, fecha_reporte, reg_leidos, reg_insertados, estado, mensaje, tiempo_sec):
    """Guarda el resultado de la ejecución en dbo.ETL_Log."""
    query_log = """
        INSERT INTO dbo.ETL_Log 
        (NombreArchivo, FechaReporte, RegistrosLeidos, RegistrosInsertados, Estado, MensajeDetalle, TiempoEjecucionSegundos)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    cursor = conn.cursor()
    cursor.execute(query_log, (nombre_archivo, fecha_reporte, reg_leidos, reg_insertados, estado, mensaje, tiempo_sec))
    conn.commit()

# ==============================================================================
# 3. FLUJO PRINCIPAL DE INGESTA
# ==============================================================================
def ejecutar_pipeline_etl(fecha_particion=None, ruta_excel=None):
    tiempo_inicio = time.time()
    
    if ruta_excel is None:
        ruta_excel = obtener_archivo_excel(CARPETA_ENTRADA)
        
    if ruta_excel is None:
        print("No se encontraron archivos Excel para procesar.")
        return

    nombre_archivo = os.path.basename(ruta_excel)
    print(f"--- Procesando archivo: {nombre_archivo} ---")

    if fecha_particion is None:
        fecha_particion = int(datetime.now().strftime('%Y%m%d'))

    conn = None
    reg_leidos = 0
    reg_insertados = 0

    try:
        # 1. Leer y limpiar Excel con Pandas
        df = pd.read_excel(ruta_excel)
        reg_leidos = len(df)

        if reg_leidos == 0:
            raise ValueError("El archivo Excel no contiene filas de datos.")

        # Reemplazar leyendas 'No aplica' y nulos por None (NULL en SQL)
        df = df.replace(r'^\s*"*\s*No aplica\s*"*\s*$', None, regex=True)
        df = df.fillna(value=None)
        df['FechaReporte'] = fecha_particion

        # Mapeo de columnas Excel -> dbo.Staging_FactCreditos[cite: 1]
        mapeo_columnas = {
            'FechaReporte': 'FechaReporte',
            'TIPO PERSONA RIF': 'TipoPersonaRIF',
            'IDENTIFICACIÓN TIPO PERSONA RIF': 'IdentificacionTipoPersonaRIF',
            'NOMBRE O RAZÓN SOCIAL': 'NombreRazonSocial',
            'ACTIVIDAD DEL CLIENTE': 'ActividadCliente',
            'TIPO DE CRÉDITO': 'TipoCredito',
            'FECHA DE APROBACIÓN DEL CRÉDITO': 'FechaAprobacionCredito',
            'FECHA DE VENCIMIENTO DEL CRÉDITO': 'FechaVencimientoCredito',
            'NÚMERO DE CRÉDITO': 'NumeroCredito',
            'CÓDIGO CUENTA CONTABLE': 'CodigoCuentaContable',
            'MONTO ORIGINAL\n(BOLÍVARES)': 'MontoOriginalBolivares',
            'MONTO ORIGINAL\n(PETRO)': 'MontoOriginalPetro',
            'DESTINO DE LOS RECURSOS': 'DestinoRecursos',
            'RUBRO ': 'Rubro',
            'ENTIDAD FEDERAL': 'EntidadFederal',
            'NÚMERO DE DESEMBOLSOS': 'NumeroDesembolsos',
            'MONTO LIQUIDADO DURANTE EL DÍA A REPORTAR\n(BOLÍVARES)': 'MontoLiquidadoBolivares',
            'MONTO LIQUIDADO DURANTE EL DÍA A REPORTAR\n(PETRO)': 'MontoLiquidadoPetro',
            'UNIDAD DE VALOR DEL CRÉDITO \n(CANTIDAD)': 'UnidadValorCreditoCantidad',
            'FECHA DE LIQUIDACIÓN': 'FechaLiquidacion',
            'SITUACIÓN DEL CRÉDITO \n': 'SituacionCredito',
            'FECHA DE LA SITUACIÓN DEL CRÉDITO': 'FechaSituacionCredito',
            'PORCENTAJE DE AMORTIZACIÓN\n': 'PorcentajeAmortizacion',
            'MONTO DE LA AMORTIZACIÓN (BOLÍVARES)': 'MontoAmortizacionBolivares',
            'MONTO DE LA AMORTIZACIÓN\n(PETRO)\n': 'MontoAmortizacionPetro',
            'SALDO DEL CRÉDITO\n(BOLÍVARES)': 'SaldoCreditoBolivares',
            'SALDO DEL CRÉDITO\n(PETRO)': 'SaldoCreditoPetro'
        }

        df_staging = df[list(mapeo_columnas.keys())].rename(columns=mapeo_columnas)
        datos_a_insertar = [tuple(x) for x in df_staging.to_numpy()]
        reg_insertados = len(datos_a_insertar)

        # 2. Conexión y transacciones SQL
        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        cursor.fast_executemany = True

        # Paso A: Limpiar Staging previa y cargar nuevos datos[cite: 1]
        cursor.execute("TRUNCATE TABLE dbo.Staging_FactCreditos;")
        
        columnas_sql = ", ".join(df_staging.columns)
        placeholders = ", ".join(["?"] * len(df_staging.columns))
        query_insert = f"INSERT INTO dbo.Staging_FactCreditos ({columnas_sql}) VALUES ({placeholders})"
        
        cursor.executemany(query_insert, datos_a_insertar)

        # Paso B: Ejecutar Procedimiento de Ingesta Particionada[cite: 1]
        query_exec = f"EXEC dbo.usp_IngresarCreditosDiarios @FechaReporte = {fecha_particion}, @ModoSobrescribir = 1;"
        cursor.execute(query_exec)
        
        conn.commit()

        tiempo_total = round(time.time() - tiempo_inicio, 2)
        
        # 3. Registrar éxito y mover archivo a PROCESADOS
        registrar_log(conn, nombre_archivo, fecha_particion, reg_leidos, reg_insertados, 'EXITO', 'Ingesta y reemplazo de partición exitoso.', tiempo_total)
        
        # Cerrar conexión antes de mover el archivo para liberar bloqueos
        conn.close()
        conn = None
        
        nueva_ruta = mover_archivo(ruta_excel, CARPETA_PROCESADOS)
        print(f" SUCCESS: Archivo procesado y movido a: {nueva_ruta}")

    except Exception as e:
        tiempo_total = round(time.time() - tiempo_inicio, 2)
        error_msg = str(e)
        print(f" ERROR: {error_msg}")

        # Intentar registrar el error en SQL Server
        try:
            if conn is None:
                conn = pyodbc.connect(CONN_STR)
            else:
                conn.rollback()
                
            registrar_log(conn, nombre_archivo, fecha_particion, reg_leidos, 0, 'ERROR', error_msg, tiempo_total)
            conn.close()
        except Exception as log_error:
            print(f"No se pudo registrar el error en la tabla de log: {log_error}")

        # Mover archivo a la carpeta de ERRORES
        try:
            nueva_ruta = mover_archivo(ruta_excel, CARPETA_ERRORES)
            print(f" ARCHIVO MOVIDO A ERRORES: {nueva_ruta}")
        except Exception as move_error:
            print(f"No se pudo mover el archivo a errores: {move_error}")

if __name__ == '__main__':
    # Ejemplo de ejecución asignando fecha específica de partición
    ejecutar_pipeline_etl(fecha_particion=20261001)


////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////
""" 
SELECT 
    LogID,
    FechaEjecucion,
    NombreArchivo,
    FechaReporte,
    RegistrosLeidos,
    RegistrosInsertados,
    Estado,
    TiempoEjecucionSegundos,
    MensajeDetalle
FROM dbo.ETL_Log
ORDER BY LogID DESC;
"""    



