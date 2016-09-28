"""
Runs a paricular reform against the baseline policy:
-------------------------------------------------------------------------------
"""
# Import packages
from btax.run_btax import run_btax, run_btax_with_baseline_delta, run_btax_to_json_tables

test_run = False # flag for test run (for Travis CI)
start_year = 2016
iit_reform = {}


#2018 law
# run_btax_with_baseline_delta(test_run,start_year,iit_reform,btax_depr_3yr_exp=40.,
#          btax_depr_5yr_exp=40.,btax_depr_7yr_exp=40.,btax_depr_10yr_exp=40.,
#          btax_depr_15yr_exp=40.,btax_depr_20yr_exp=40.)
#2019 law
run_btax_to_json_tables(test_run,start_year,iit_reform,btax_depr_3yr_exp=30.,
         btax_depr_5yr_exp=30.,btax_depr_7yr_exp=30.,btax_depr_10yr_exp=30.,
         btax_depr_15yr_exp=30.,btax_depr_20yr_exp=30.)
#2020 law
# run_btax_with_baseline_delta(test_run,start_year,iit_reform,btax_depr_3yr_exp=0.,
#          btax_depr_5yr_exp=0.,btax_depr_7yr_exp=0.,btax_depr_10yr_exp=0.,
#          btax_depr_15yr_exp=0.,btax_depr_20yr_exp=0.)
