CREATE TABLE dbo.bda_cdto_liquidados_ejemplo
(
    id          BIGINT         NOT NULL,
    fecha       DATE           NOT NULL,
    contrato    VARCHAR(30)    NULL,
    monto       DECIMAL(18,2)  NULL
);

INSERT INTO dbo.bda_cdto_liquidados_ejemplo
    (id, fecha, contrato, monto)
VALUES
    (1, '2026-11-01', 'C001', 100.00),
    (2, '2026-11-01', 'C002', 200.00),
    (3, '2026-11-02', 'C003', 300.00),
    (4, '2026-11-02', 'C004', 400.00),
    (5, '2026-11-03', 'C005', 500.00);

SELECT * FROM  dbo.bda_cdto_liquidados_ejemplo

SELECT
    fecha,
    COUNT(*) AS cantidad,
    SUM(monto) AS monto_total
FROM dbo.bda_cdto_liquidados_ejemplo
GROUP BY fecha
ORDER BY fecha;

CREATE PARTITION FUNCTION PF_bda_cdto_liquidados_fecha (DATE)
AS RANGE RIGHT
FOR VALUES
(
    '2026-11-01',
    '2026-11-02',
    '2026-11-03',
    '2026-11-04'
);

--DROP TABLE dbo.bda_cdto_liquidados_ejemplo;

CREATE TABLE dbo.bda_cdto_liquidados_ejemplo
(
    id          BIGINT         NOT NULL,
    fecha       DATE           NOT NULL,
    contrato    VARCHAR(30)    NULL,
    monto       DECIMAL(18,2)  NULL
)
ON PS_bda_cdto_liquidados_fecha(fecha);

SELECT DB_NAME() AS BaseActual;

SELECT
    ps.name AS PartitionScheme,
    pf.name AS PartitionFunction
FROM sys.partition_schemes AS ps
JOIN sys.partition_functions AS pf
  ON ps.function_id = pf.function_id
WHERE ps.name = 'PS_bda_cdto_liquidados_fecha';

SELECT
    name
FROM sys.partition_functions
WHERE name = 'PF_bda_cdto_liquidados_fecha';

SELECT
    name,
    type_desc,
    is_default
FROM sys.filegroups
ORDER BY data_space_id;