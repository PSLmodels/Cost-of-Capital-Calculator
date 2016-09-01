"""
Runs a paricular reform against the baseline policy:
-------------------------------------------------------------------------------
"""
# Import packages
from btax.run_btax import run_btax_to_json_tables as run_btax

test_run = False # flag for test run (for Travis CI)
start_year = 2016
iit_reform = {
start_year: {
    '_II_rt5': [.3],
    '_II_rt6': [.3],
    '_II_rt7': [0.3],
}, }

# run btax
run_btax(test_run,start_year,iit_reform,btax_betr_pass=0.23, btax_betr_corp=0.25, btax_depr_allyr_exp=1.,
         btax_other_hair=1.)
