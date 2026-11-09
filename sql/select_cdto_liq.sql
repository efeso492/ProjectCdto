WITH vigentes as (SELECT
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
  v.id_cdto                         AS id_clte, 
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
  LEFT JOIN complementos as c ON (v.id_cdto=c.id_cdto)
  
  
  
 
