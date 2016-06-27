'''
Script (script_firm_calibration.py):
-------------------------------------------------------------------------------
Last updated: 6/24/2015.

This script calibrates parameters for firms on all NAICS levels.
This module splits up the calibration tasks into
various functions, specifically, there is a function for each set of
parameters that need to be calibrated. The script uses these functions to
generate :term:`NAICS trees<NAICS tree>` with all firm parameters calibrated for each NAICS
code. The script outputs these parameter calibrations and processed data to
csv files.
'''
import os.path
import sys
import pandas as pd
import numpy as np
_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
_BTAX_DIR = os.path.join(_CUR_DIR, 'btax')
_DEPR_DIR = os.path.join(_BTAX_DIR,'depreciation')
_DATA_DIR = os.path.join(_DEPR_DIR, 'data')
_RATE_DIR = os.path.join(_DATA_DIR, 'depreciation_rates')
_FIN_DIR = os.path.join(_BTAX_DIR, 'financial_policy')
_FOUT_DIR = os.path.join(_FIN_DIR, 'output')
_OUT_DIR = os.path.join(_DEPR_DIR, 'output')
_TAX_DEPR_IN_PATH = os.path.join(_RATE_DIR, 'depr_allow.csv')
sys.path.append(_DEPR_DIR)
sys.path.append(_BTAX_DIR)
from btax.depreciation.parameter_calibrations import calibrate_depr_rates, calc_soi_assets
from btax.financial_policy.calibrate_financing import calibrate_financing
from btax.cost_of_capital import calc_cost_of_capital, asst_cost_of_capital
from btax.financial_policy.calc_discount_rate import calc_real_discount_rate
import naics_processing as naics
import soi_processing as soi
from btax.depreciation.parameter_calibrations import pull_soi_data

def run_btax(user_params):
	#calculates the depreciation rates
	sector_dfs = pull_soi_data(get_all=True, from_out=False,
	                               output_data=True)
	depr_rates = calibrate_depr_rates(sector_dfs)
	debt_ratios = calibrate_financing()
	discount_rates = calc_real_discount_rate(debt_ratios)
	calc_cost_of_capital(depr_rates, discount_rates)	

run_btax(user_params={})
'''
if __name__ == '__main__':
	run_firm_calibration(user_params={})
'''
	