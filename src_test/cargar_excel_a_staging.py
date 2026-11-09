import os
import glob
from datetime import datetime
import pandas as pd
import pyodbc

# ==============================================================================
# 1. CONFIGURACIÓN DE CONEXIÓN Y RUTAS
# ==============================================================================
DB_CONFIG = {
    'server': 'LOCALHOST',        # Servidor o IP (ej: 'localhost\SQLEXPRESS')
    'database': 'DB_Finanzas',    # Tu base de datos
    'driver': '{ODBC Driver 17 for SQL Server}'
}

CONN_STR = (
    f"DRIVER={DB_CONFIG['driver']};"
    f"SERVER={DB_CONFIG['server']};"
    f"DATABASE={DB_CONFIG['database']};"
    "Trusted_Connection=yes;"
)

# Carpeta donde depositas los archivos Excel diarios
CARPETA_ENTRADA = r'C:\archivos_excel_ingesta'

def obtener_archivo_excel_mas_reciente(carpeta):
    """Obtiene la ruta del último archivo .xlsx o .xls depositado en la carpeta."""
    patron = os.path.join(carpeta, '*.xlsx')
    archivos = glob.glob(patron)
    if not archivos:
        patron_xls = os.path.join(carpeta, '*.xls')
        archivos = glob.glob(patron_xls)
    if not archivos:
        raise FileNotFoundError(f"No se encontraron archivos Excel en la carpeta: {carpeta}")
    
    # Ordenar por fecha de última modificación
    archivos.sort(key=os.path.getmtime, reverse=True)
    return archivos[0]

def procesar_e_ingestar_excel(fecha_reporte=None, ruta_excel=None):
    # Determine el archivo si no se especifica explícitamente
    if ruta_excel is None:
        ruta_excel = obtener_archivo_excel_mas_reciente(CARPETA_ENTRADA)
    
    print(f"Leyendo archivo Excel: {ruta_excel}")

    # Determinar la fecha de la partición (YYYYMMDD)
    if fecha_particion is None:
        # Por defecto toma la fecha de hoy o se puede extraer del nombre del archivo
        fecha_particion = int(datetime.now().strftime('%Y%m%d'))

    # ==============================================================================
    # 2. LECTURA Y MAPEO DEL EXCEL CON PANDAS
    # ==============================================================================
    df = pd.read_excel(ruta_excel)

    # Reemplazar valores ' No aplica ' o vacíos por None (NULL en SQL)
    df = df.replace(r'^\s*"*\s*No aplica\s*"*\s*$', None, regex=True)
    df = df.fillna(value=None)

    # Inyectar la fecha de partición requerida por la tabla Staging[cite: 1]
    df['FechaReporte'] = fecha_particion

    # Mapeo exacto entre encabezados de la plantilla Excel y columnas de dbo.Staging_FactCreditos[cite: 1]
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

    # Renombrar columnas según el mapeo
    df_staging = df[list(mapeo_columnas.keys())].rename(columns=mapeo_columnas)

    # Convertir dataframe a lista de tuplas para inserción limpia
    datos_a_insertar = [tuple(x) for x in df_staging.to_numpy()]

    # ==============================================================================
    # 3. CONSTRUCCIÓN Y EJECUCIÓN DINÁMICA DEL INSERT MASIVO
    # ==============================================================================
    columnas_sql = ", ".join(df_staging.columns)
    placeholders = ", ".join(["?"] * len(df_staging.columns))
    query_insert_masivo = f"INSERT INTO dbo.Staging_FactCreditos ({columnas_sql}) VALUES ({placeholders})"

    conn = None
    try:
        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        cursor.fast_executemany = True # Optimiza la inserción masiva acelerando la carga de datos

        print(f"1. Insertando {len(datos_a_insertar)} filas en dbo.Staging_FactCreditos...")[cite: 1]
        cursor.executemany(query_insert_masivo, datos_a_insertar)

        # Paso 2: Ejecutar el procedimiento de ingesta particionada[cite: 1]
        print("2. Ejecutando dbo.usp_IngresarCreditosDiarios...")[cite: 1]
        ruta_sql_exec = os.path.join(os.path.dirname(__file__), 'scripts_sql', '02_exec_procedimiento.sql')
        
        with open(ruta_sql_exec, 'r', encoding='utf-8') as f:
            query_exec = f.read().format(fecha_reporte=fecha_particion)

        cursor.execute(query_exec)

        conn.commit()
        print(f" SUCCESS: Ingesta particionada completada con éxito para la fecha: {fecha_particion}")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f" ERROR durante el procesamiento: {str(e)}")
        raise e
    finally:
        if conn:
            conn.close()

"""
¿Cómo funciona el paso de datos dinámico?fast_executemany = True: En lugar de concatenar texto plano con miles de cláusulas VALUES,
Python utiliza sentencias preparadas nativas del driver ODBC (?). Esto permite insertar miles de filas del Excel en milisegundos de forma 
segura sin riesgo de inyección SQL.fecha_reporte dinámico: El script añade la columna FechaReporte a cada fila leída del Excel antes de transferirla a SQL Server,
garantizando que todos los registros del archivo queden etiquetados con su fecha de partición correspondiente[cite: 1].

"""


if __name__ == '__main__':
    # Ejemplo: Procesar un archivo especificando la fecha de partición en formato YYYYMMDD
    procesar_e_ingestar_excel(fecha_reporte=20261001)