USE master;
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = N'DB_Creditos')
    DROP DATABASE DB_Creditos;
GO

CREATE DATABASE DB_Creditos;
GO

USE DB_Creditos;
GO

-- 1. Crear la Función de Partición basada en fecha numérica (YYYYMMDD)
-- Se inicializa con valores de frontera base
CREATE PARTITION FUNCTION PF_Creditos_Fecha (INT)
AS RANGE RIGHT FOR VALUES (20261001, 20261002);
GO

-- 2. Crear el Esquema de Partición asociado al Filegroup primario
CREATE PARTITION SCHEME PS_Creditos_Fecha
AS PARTITION PF_Creditos_Fecha
ALL TO ([PRIMARY]);
GO

--Paso 2: Crear la Tabla Particionada y la Tabla Staging
--Creamos el modelo de datos basado en las columnas de la muestra del reporte de créditos recibida,
--incorporando la columna FechaReporte INT como clave de partición.

SQL


CREATE TABLE dbo.FactCreditos
(
    FechaReporte INT NOT NULL, -- Campo de Partición (Ej: 20261001)
    TipoPersonaRIF VARCHAR(5),
    IdentificacionTipoPersonaRIF BIGINT,
    NombreRazonSocial VARCHAR(255),
    ActividadCliente VARCHAR(50),
    TipoCredito INT,
    FechaAprobacionCredito INT,
    FechaVencimientoCredito INT,
    NumeroCredito BIGINT NOT NULL,
    CodigoCuentaContable BIGINT,
    MontoOriginalBolivares DECIMAL(18,2),
    MontoOriginalPetro VARCHAR(50),
    DestinoRecursos VARCHAR(100),
    Rubro VARCHAR(100),
    EntidadFederal VARCHAR(100),
    NumeroDesembolsos INT,
    MontoLiquidadoBolivares DECIMAL(18,2),
    MontoLiquidadoPetro VARCHAR(50),
    UnidadValorCreditoCantidad VARCHAR(50),
    FechaLiquidacion INT,
    SituacionCredito VARCHAR(50),
    FechaSituacionCredito INT,
    PorcentajeAmortizacion DECIMAL(5,2),
    MontoAmortizacionBolivares DECIMAL(18,2),
    MontoAmortizacionPetro VARCHAR(50),
    SaldoCreditoBolivares DECIMAL(18,2),
    SaldoCreditoPetro VARCHAR(50),
    
    -- La clave primaria DEBE incluir el campo de partición
    CONSTRAINT PK_FactCreditos PRIMARY KEY CLUSTERED (FechaReporte, NumeroCredito)
) ON PS_Creditos_Fecha(FechaReporte);
GO


-- 2. Tabla Staging (Estructura idéntica, no particionada, para carga temporal)
CREATE TABLE dbo.Staging_FactCreditos
(
    FechaReporte INT NOT NULL,
    TipoPersonaRIF VARCHAR(5),
    IdentificacionTipoPersonaRIF BIGINT,
    NombreRazonSocial VARCHAR(255),
    ActividadCliente VARCHAR(50),
    TipoCredito INT,
    FechaAprobacionCredito INT,
    FechaVencimientoCredito INT,
    NumeroCredito BIGINT NOT NULL,
    CodigoCuentaContable BIGINT,
    MontoOriginalBolivares DECIMAL(18,2),
    MontoOriginalPetro VARCHAR(50),
    DestinoRecursos VARCHAR(100),
    Rubro VARCHAR(100),
    EntidadFederal VARCHAR(100),
    NumeroDesembolsos INT,
    MontoLiquidadoBolivares DECIMAL(18,2),
    MontoLiquidadoPetro VARCHAR(50),
    UnidadValorCreditoCantidad VARCHAR(50),
    FechaLiquidacion INT,
    SituacionCredito VARCHAR(50),
    FechaSituacionCredito INT,
    PorcentajeAmortizacion DECIMAL(5,2),
    MontoAmortizacionBolivares DECIMAL(18,2),
    MontoAmortizacionPetro VARCHAR(50),
    SaldoCreditoBolivares DECIMAL(18,2),
    SaldoCreditoPetro VARCHAR(50)
);
GO

--Paso 3: Crear el Procedimiento Almacenado de Ingesta y Reemplazo de Particiones
--Este procedimiento automatiza completamente el flujo estilo Hive:
--Comprueba si la fecha enviada existe como partición. Si no existe, realiza un SPLIT RANGE para crearla.
--Si se activa @ModoSobrescribir = 1 (INSERT OVERWRITE), ejecuta un TRUNCATE exclusivo sobre esa partición mediante metadatos para vaciarla al instante sin afectar otras fechas.
--Copia los datos desde la tabla Staging_FactCreditos a FactCreditos.

CREATE OR ALTER PROCEDURE dbo.usp_IngresarCreditosDiarios
    @FechaReporte INT,           -- Fecha en formato YYYYMMDD (Ej: 20261001)
    @ModoSobrescribir BIT = 1    -- 1: Reemplazar partición (Hive OVERWRITE) | 0: Solo insertar
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @NombreFuncion NVARCHAR(128) = N'PF_Creditos_Fecha';
    DECLARE @NombreEsquema NVARCHAR(128) = N'PS_Creditos_Fecha';
    DECLARE @NombreFilegroup NVARCHAR(128) = N'PRIMARY';
    DECLARE @NumParticion INT;
    DECLARE @SQL NVARCHAR(MAX);

    BEGIN TRY
        BEGIN TRANSACTION;

        -------------------------------------------------------------------
        -- 1. Garantizar la existencia de la partición (SPLIT dinámico)
        -------------------------------------------------------------------
        IF NOT EXISTS (
            SELECT 1 FROM sys.partition_range_values rv
            INNER JOIN sys.partition_functions pf ON rv.function_id = pf.function_id
            WHERE pf.name = @NombreFuncion AND CAST(rv.value AS INT) = @FechaReporte
        )
        BEGIN
            -- Indicar el siguiente Filegroup a utilizar
            SET @SQL = N'ALTER PARTITION SCHEME ' + QUOTENAME(@NombreEsquema) + N' NEXT USED ' + QUOTENAME(@NombreFilegroup) + N';';
            EXEC sp_executesql @SQL;

            -- Crear la nueva frontera de la partición
            SET @SQL = N'ALTER PARTITION FUNCTION ' + QUOTENAME(@NombreFuncion) + N'() SPLIT RANGE (' + CAST(@FechaReporte AS VARCHAR(8)) + N');';
            EXEC sp_executesql @SQL;
        END

        -------------------------------------------------------------------
        -- 2. Reemplazo/Sobrescritura de la partición si ya contenía datos
        -------------------------------------------------------------------
        IF @ModoSobrescribir = 1
        BEGIN
            -- Obtener el número físico de la partición asignada a la fecha
            SELECT @NumParticion = $PARTITION.PF_Creditos_Fecha(@FechaReporte);

            -- Truncar únicamente los datos de esa partición específica (operación instantánea)
            SET @SQL = N'TRUNCATE TABLE dbo.FactCreditos WITH (PARTITIONS (' + CAST(@NumParticion AS VARCHAR) + N'));';
            EXEC sp_executesql @SQL;
        END

        -------------------------------------------------------------------
        -- 3. Inserción de los datos cargados desde la Staging
        -------------------------------------------------------------------
        INSERT INTO dbo.FactCreditos
        SELECT * FROM dbo.Staging_FactCreditos
        WHERE FechaReporte = @FechaReporte;

        -- Limpieza de la tabla de trabajo
        TRUNCATE TABLE dbo.Staging_FactCreditos;

        COMMIT TRANSACTION;
        PRINT 'Ingesta completada exitosamente para la partición: ' + CAST(@FechaReporte AS VARCHAR(8));
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 
            ROLLBACK TRANSACTION;
            
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END;
GO

--Paso 4: Ejemplo de Uso Práctico (Carga y Reemplazo)
--1. Ingesta Inicial del archivo con fecha 20261001:


-- Cargas la nueva versión del archivo a la Staging
INSERT INTO dbo.Staging_FactCreditos (FechaReporte, TipoPersonaRIF, IdentificacionTipoPersonaRIF, NombreRazonSocial, NumeroCredito, MontoOriginalBolivares)
VALUES (20261001, 'J', 15822, 'THE FACTORY HKA, C.A CORREGIDO', 17607, 2500000.00);

SELECT * from dbo.Staging_FactCreditos

DECLARE @NumParticion INT = $PARTITION.PF_Creditos_Fecha(20261001);
-- Elimina los registros de esa fecha en milisegundos sin afectar el resto de la tabla
TRUNCATE TABLE dbo.FactCreditos WITH (PARTITIONS (@NumParticion));

SELECT * FROM sys.tables WHERE name = 'FactCreditos';

--Codigo que ingresa los datos de la tabla Staging_FactCreditos a la tabla FactCreditos
EXEC dbo.usp_IngresarCreditosDiarios 
    @FechaReporte = 20261001, 
    @ModoSobrescribir = 1;

--Quita duplicados de la tabla Staging_FactCreditos
WITH CTE_Duplicados AS (
    SELECT *, 
           ROW_NUMBER() OVER (
               PARTITION BY FechaReporte, NumeroCredito 
               ORDER BY (SELECT NULL)
           ) AS RowNum
    FROM dbo.Staging_FactCreditos
)
DELETE FROM CTE_Duplicados WHERE RowNum > 1;

INSERT INTO dbo.Staging_FactCreditos 
(
    FechaReporte, TipoPersonaRIF, IdentificacionTipoPersonaRIF, NombreRazonSocial, 
    TipoCredito, NumeroCredito, MontoOriginalBolivares
)
VALUES 
(20261001, 'J', 15822, 'THE FACTORY HKA, C.A (REVISION 2)', 2, 17607, 3000000.00),
(20261001, 'V', 1422,  'MARTIN MARTINEZ (NUEVO REGISTRO)', 5, 58767, 150000.00),
(20261001, 'V', 1453,  'RAUL (NUEVO REGISTRO)', 5, 58768, 250000.00),
(20261001, 'V', 1489,  'JOSE (NUEVO REGISTRO)', 5, 58769, 250000.00);

USE DB_Creditos;
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

ALTER TABLE dbo.ETL_Log 
ADD ChecksumHash VARCHAR(64) NULL;
GO

BACKUP DATABASE [DB_Creditos]
TO DISK = N'C:\Users\Adiestramiento.MXL3061XXX\Documents\ProjeCdto\Backup_Restore\DB_Creditos_Backup.bak'
WITH FORMAT, INIT, 
     NAME = N'Respaldado Completo DB_Creditos', 
     STATS = 10;
GO


USE [master];
GO

RESTORE DATABASE [DB_Creditos]
FROM DISK = N'C:\Users\Adiestramiento.MXL3061XXX\Documents\ProjeCdto\Backup_Restore\DB_Creditos_Backup.bak'
WITH FILE = 1, 
     NOUNLOAD, 
     STATS = 5;
GO

BACKUP DATABASE [DB_Creditos]
TO DISK = N'C:\Temp\DB_Creditos_Backup.bak'
WITH FORMAT, INIT, 
     NAME = N'Respaldado Completo DB_Creditos', 
     STATS = 10;
GO



