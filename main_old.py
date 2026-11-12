import logging
from logging.handlers import RotatingFileHandler
from typing import Any, Iterable, List, Tuple
from src.connection_impala import *
#from impala.dbapi import connect
#from impala.util import as_pandas

#credentials_conn = dicc_main["credentials_conn_impala"]

credentials_conn_impala= {
        "SERVER"          : "pro",   
        "KINIT_USER"      : "B729515",
        "KINIT_PASSWORD"  : "Mercantilbanco2033*"
    }


jsonData = {
        "logFilePath": "./logs",
        "logFile_Name":"ATlogfile.log",
        "max_logfile_size":10000000,
        "backupCount":3,
    }
os.makedirs(
    jsonData["logFilePath"],
    exist_ok=True
)

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
        handlers=[
            RotatingFileHandler(
                os.path.join(jsonData["logFilePath"], jsonData['logFile_Name']),
                maxBytes = jsonData["max_logfile_size"],
                backupCount = jsonData["backupCount"]
            ),
            logging.StreamHandler()
        ]
    )

connection  = Connection_hive_impala(credentials_conn_impala,logging)

sql ="""WITH vigentes as (SELECT
  current_date()                    AS fch_proc, 
  a.nro_per                         AS nro_per, 
  a.tipo_id                         AS tipo_id, 
  a.id_cdto                         AS id_cdto, 
  a.fch_liq_cdto                    AS fch_liq_cdto, 
  a.fch_vcto_cdto                   AS fch_vcto_cdto, 
  a.mto_original_moneda_reporte     AS mto_original_moneda_reporte,
  a.cod_produc                      AS cod_produc,
  '1'                               AS vigentes,       
  CASE
    WHEN cta_contb_asoc_mto_vig='000013108102001' THEN '1310810200'
    ELSE  SUBSTR(SUBSTR(TRIM(cta_contb_asoc_mto_vig), -11),1,10)
  END                                           AS cta_contb
FROM prod_bigdwh.bda_cdto as a 
WHERE a.fecha="20261015" 
AND a.cod_produc IN ("CLPAC","CLPAG","PRSHP","CLPMT","CLPMI")
AND SUBSTR(TRIM(a.cta_contb_asoc_mto_vig),5,5) IN ("13135","13137","13147","13157","13357")),
complementos AS (
 SELECT
  a.id_cdto                    AS id_cdto, 
  a.entidad                    AS entidad,
  a.clte_empdedor              AS clte_empdedor,  
  a.clte_comuna                AS clte_comuna, 
  a.fch_aprob                  AS fch_aprob,
  a.rubro                      AS rubro,
  a.destino_recurso            AS destino_recurso,
  a.mto_liquid_dolar           AS mto_liquid_dolar, 
  a.origen_fondos              AS origen_fondos, 
  a.cant_uvc_liquid            AS cant_uvc_liquid, 
  a.uvc_cpun                   AS uvc_cpun, 
  a.fch_desemb_cdto            AS fch_desemb_cdto, 
  a.mto_cdto_usd               AS mto_cdto_usd, 
  a.mto_cdto_bs                AS mto_cdto_bs, 
  a.cta_ctble_cdto             AS cta_ctble_cdto
  FROM prod_bigdwh.bda_cdto_complemento as a 
  WHERE a.fecha="20261015" 
 )
 
 SELECT 
  v.fch_proc                    AS fch_proc, 
  v.nro_per                         AS nro_per, 
  v.tipo_id                         AS tipo_id, 
  v.id_cdto                         AS id_cdto, 
  v.fch_liq_cdto                    AS fch_liq_cdto, 
  v.fch_vcto_cdto                   AS fch_vcto_cdto, 
  v.mto_original_moneda_reporte     AS mto_original_moneda_reporte,
  v.cod_produc                      AS cod_produc,
  '1'                               AS vigentes,
  c.entidad                         AS entidad,
  c.clte_empdedor                   AS clte_empdedor,  
  c.clte_comuna                     AS clte_comuna, 
  c.fch_aprob                       AS fch_aprob,
  c.rubro                           AS rubro,
  c.destino_recurso                 AS destino_recurso,
  c.mto_liquid_dolar                AS mto_liquid_dolar, 
  c.origen_fondos                   AS origen_fondos, 
  c.cant_uvc_liquid                 AS cant_uvc_liquid, 
  c.uvc_cpun                        AS uvc_cpun, 
  c.fch_desemb_cdto                 AS fch_desemb_cdto, 
  c.mto_cdto_usd                    AS mto_cdto_usd, 
  c.mto_cdto_bs                     AS mto_cdto_bs, 
  c.cta_ctble_cdto                  AS cta_ctble_cdto
  FROM vigentes as v
  LEFT JOIN complementos as c ON (v.id_cdto=c.id_cdto)"""

if (connection):
    logging.info("Conexion True")
    data: List[Tuple[Any, ...]] = connection.impala_hive_consult_all(sql)


valid_rows: List[Tuple[Any, ...]] = []
append_row = valid_rows.append  # micro-optimizacin
total_rows = 0
expected_len=23

if (data is not None):
    logging.info("Consulta realizada con exito")
    for idx, row in enumerate(data):
            total_rows += 1

            # Validar longitud (r�pido)
            if len(row) != expected_len:
                raise ValueError(
                    f"Fila {idx} invalida: longitud {len(row)} != {expected_len}"
                )

            # Validar nulos (m�s eficiente que str conversion)
            #if any(col is None for col in row):
            #    raise ValueError(f"Fila {idx} contiene NULL: {row}")
            #append_row(row)
            for col in row:
                if col is None or  len(str(col).strip())==0:
                    raise ValueError(f"Fila {idx} contiene NULL o vacio : {row}")    
                else:    
                    append_row(row)

    logging.info(f"Registros procesados: {total_rows}")
    logging.info(f"Registros validos: {len(valid_rows)}")
    