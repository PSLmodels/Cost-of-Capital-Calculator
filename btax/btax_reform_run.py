"""
Runs a paricular reform against the baseline policy:
-------------------------------------------------------------------------------
"""
# Import packages
from btax.run_btax import run_btax_with_baseline_delta as run_btax

# run btax
run_btax(btax_betr_pass=0.23, btax_betr_corp=0.25, btax_depr_allyr_exp=1.,
         btax_other_hair=1.)
