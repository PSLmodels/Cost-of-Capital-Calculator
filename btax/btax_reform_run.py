"""
Runs a paricular reform against the baseline policy:
-------------------------------------------------------------------------------
"""
# Import packages
from btax.run_btax import run_btax_with_baseline_delta as run_btax
from btax.get_taxcalc_rates import get_rates

reform = {
2016: {
    '_II_rt5': [.3],
    '_II_rt6': [.3],
    '_II_rt7': [0.3],
}, }

baseline_indiv_rates = get_rates(True, 2016, reform={})
reform_indiv_rates = get_rates(False,2016,reform=reform)
print baseline_indiv_rates
print reform_indiv_rates
quit()
# run btax
run_btax(btax_betr_pass=0.23, btax_betr_corp=0.25, btax_depr_allyr_exp=1.,
         btax_other_hair=1.)
