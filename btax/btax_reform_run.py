"""
Runs a paricular reform against the baseline policy:
-------------------------------------------------------------------------------
"""
# Import packages
from btax.run_btax import run_btax

test_run = False # flag for test run (for Travis CI)
start_year = 2016
iit_reform = {}

# run btax
run_btax(test_run,False,start_year,iit_reform,btax_other_corpeq=0.5)
