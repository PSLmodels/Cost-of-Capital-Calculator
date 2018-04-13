"""
Runs B-Tax with TCJA as baseline and 2017 law as the reform.
------------------------------------------------------------------------
"""
# Import packages
from btax.run_btax import run_btax, run_btax_with_baseline_delta
from taxcalc import *

test_run = False  # flag for test run (for Travis CI)
start_year = 2018

# Note that TCJA is current law baseline in TC 0.16+
# Thus to compare TCJA to 2017 law, we'll use 2017 law as the reform
rec = Records.cps_constructor()
pol = Policy()
calc = Calculator(policy=pol, records=rec)
ref = calc.read_json_param_objects('2017_law.json', None)
iit_reform = ref['policy']

# Run B-Tax
run_btax_with_baseline_delta(test_run, start_year, iit_reform, data='cps',
                             btax_betr_corp=0.35, btax_depr_3yr_exp=50.,
                             btax_depr_5yr_exp=50.,
                             btax_depr_7yr_exp=50.,
                             btax_depr_10yr_exp=50.,
                             btax_depr_15yr_exp=50.,
                             btax_depr_20yr_exp=50.)
