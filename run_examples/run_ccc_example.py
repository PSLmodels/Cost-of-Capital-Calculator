"""
Runs Cost-of-Capital-Calculator with TCJA as baseline and 2017 law as
the reform.
------------------------------------------------------------------------
"""
# Import packages
from ccc.run_ccc import run_ccc_with_baseline_delta
from taxcalc import *
from ccc.parameters import Specifications

test_run = False  # flag for test run (for Travis CI)
start_year = 2018

# Note that TCJA is current law baseline in TC 0.16+
# Thus to compare TCJA to 2017 law, we'll use 2017 law as the reform
reform_url = ('https://raw.githubusercontent.com/'
              'PSLmodels/Tax-Calculator/master/taxcalc/'
              'reforms/2017_law.json')
ref = Calculator.read_json_param_objects(reform_url, None)
iit_reform = ref['policy']

# Initialize Cost-of-Capital-Calculator parameters
baseline_parameters = Specifications(year=2018, call_tc=True,
                                     iit_reform={})
reform_parameters = Specifications(year=2018, call_tc=True,
                                   iit_reform=iit_reform)

reform_params = {'CIT_rate': 0.35, 'BonusDeprec_3yr': 0.50,
                 'BonusDeprec_5yr': 0.50, 'BonusDeprec_7yr': 0.50,
                 'BonusDeprec_10yr': 0.50, 'BonusDeprec_15yr': 0.50,
                 'BonusDeprec_20yr': 0.50}
reform_parameters.update_specifications(reform_params)

# Run Cost-of-Capital-Calculator
run_ccc_with_baseline_delta(baseline_parameters, reform_parameters,
                            data='cps')
