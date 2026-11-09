SELECT tmp.fecha_1 AS fch_max
FROM
  (SELECT concat(aa_calend, '-', lpad(mm_calend, 2, '0'), '-', lpad(dd_aa_calend, 2, '0')) AS fecha_1,
          marcador_dd_habil
   FROM {prod_bigdwh}.bda_calend
   WHERE marcador_dd_habil=1
     AND concat(aa_calend, '-', lpad(mm_calend, 2, '0'), '-', lpad(dd_aa_calend, 2, '0')) like '%${fch_mes_cort}%') AS tmp 
     WHERE  fecha_1 < current_date()
ORDER BY fch_max