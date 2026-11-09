SELECT fecha_1 as fch_max
from (
    SELECT concat(aa_calend,'-', lpad(mm_calend,2,'0'),'-', lpad(dd_aa_calend,2,'0')) as fecha_1, marcador_dd_habil
    FROM {prod_bigdwh}.bda_calend
    WHERE  fecha like '%${value_year}%') as tmp
WHERE  fecha_1 <= '${value_fch}'
order by fch_max DESC limit 7


