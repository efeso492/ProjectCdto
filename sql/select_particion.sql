SELECT DISTINCT
a.fecha as fecha,
a.tabla as tabla
FROM (
SELECT max(j.fecha) as fecha, ("bda_journal_mn") as tabla FROM {prod_bigdwh}.bda_journal_mn as j
UNION ALL
SELECT max(p.fecha) as fecha, ("bda_pos_b24") as tabla FROM {prod_bigdwh}.bda_pos_b24 as p 
UNION ALL
SELECT max(y.fecha) as fecha, ("bda_afili_estab") as tabla FROM {prod_bigdwh}.bda_afili_estab as y
UNION ALL
SELECT max(es.fecha) as fecha, ("bda_espejo_persona") as tabla FROM {prod_bigdwh}.bda_espejo_persona as es
UNION ALL
SELECT max(ad.fecha) as fecha, ("bda_adquiriente_tarjeta_dd") as tabla FROM {prod_bigdwh}.bda_adquiriente_tarjeta_dd as ad
UNION ALL
SELECT max(pt.fecha) as fecha, ("bda_espejo_producto") as tabla FROM {prod_bigdwh}.bda_espejo_producto as pt
UNION ALL
SELECT max(b.fecha) as fecha, ("bda_bin") as tabla FROM {prod_bigdwh}.bda_bin as b
UNION ALL
SELECT max(f.fecha) as fecha, ("bda_franquicia") as tabla FROM {prod_bigdwh}.bda_franquicia as f
UNION ALL
SELECT max(pla.fecha) as fecha, ("bda_plastico") as tabla FROM {prod_bigdwh}.bda_plastico as pla
UNION ALL
SELECT max(l.fecha) as fecha, ("bda_lote_emisor") as tabla FROM {prod_bigdwh}.bda_lote_emisor as l
UNION ALL
SELECT max(t.fecha) as fecha, ("bda_tdc_emisor_otro_adquiriente") as tabla FROM {prod_bigdwh}.bda_tdc_emisor_otro_adquiriente as t
UNION ALL
SELECT max(pr.fecha) as fecha, ("bda_produc") as tabla FROM {prod_bigdwh}.bda_produc as pr ) as a
