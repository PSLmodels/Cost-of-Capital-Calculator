"""
Runs a paricular reform against the baseline policy:
-------------------------------------------------------------------------------
"""
# Import packages
from ccc.run_ccc import run_ccc, run_ccc_with_baseline_delta

test_run = False # flag for test run (for Travis CI)
start_year = 2016
iit_reform = {}


#2018 law
# run_ccc_with_baseline_delta(test_run,start_year,iit_reform,ccc_depr_3yr_exp=40.,
#          ccc_depr_5yr_exp=40.,ccc_depr_7yr_exp=40.,ccc_depr_10yr_exp=40.,
#          ccc_depr_15yr_exp=40.,ccc_depr_20yr_exp=40.)
#2019 law
run_ccc_with_baseline_delta(test_run,start_year,iit_reform,ccc_depr_3yr_exp=30.,
         ccc_depr_5yr_exp=30.,ccc_depr_7yr_exp=30.,ccc_depr_10yr_exp=30.,
         ccc_depr_15yr_exp=30.,ccc_depr_20yr_exp=30.)
#2020 law
# run_ccc_with_baseline_delta(test_run,start_year,iit_reform,ccc_depr_3yr_exp=0.,
#          ccc_depr_5yr_exp=0.,ccc_depr_7yr_exp=0.,ccc_depr_10yr_exp=0.,
#          ccc_depr_15yr_exp=0.,ccc_depr_20yr_exp=0.)
