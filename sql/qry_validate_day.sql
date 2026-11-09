SELECT marcador_dd_habil
from {prod_bigdwh}.bda_calend
WHERE concat(aa_calend,'-', lpad(mm_calend,2,'0'),'-', lpad(dd_aa_calend,2,'0'))='{value_fch_t}' and fecha like '%{value_year}%'