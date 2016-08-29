"""
Runs a paricular reform against the baseline policy:
-------------------------------------------------------------------------------
"""
# Import packages
from btax.run_btax import run_btax_with_baseline_delta as run_btax

start_year = 2016
iit_reform = {
start_year: {
    '_II_rt5': [.3],
    '_II_rt6': [.3],
    '_II_rt7': [0.3],
}, }

# run btax
run_btax(start_year,iit_reform,btax_betr_pass=0.23, btax_betr_corp=0.25, btax_depr_allyr_exp=1.,
         btax_other_hair=1.)
