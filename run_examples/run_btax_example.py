"""
Runs Cost-of-Capital-Calculator with TCJA as baseline and 2017 law as the reform.
------------------------------------------------------------------------
"""
# Import packages
from ccc.run_ccc import run_ccc, run_ccc_with_baseline_delta
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

# Run Cost-of-Capital-Calculator
run_ccc_with_baseline_delta(test_run, start_year, iit_reform, data='cps',
                             ccc_betr_corp=0.35, ccc_depr_3yr_exp=50.,
                             ccc_depr_5yr_exp=50.,
                             ccc_depr_7yr_exp=50.,
                             ccc_depr_10yr_exp=50.,
                             ccc_depr_15yr_exp=50.,
                             ccc_depr_20yr_exp=50.)
