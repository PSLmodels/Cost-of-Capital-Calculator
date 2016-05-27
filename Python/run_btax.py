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
_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
_BTAX_DIR = os.path.join(_CUR_DIR, 'btax')
_DEPR_DIR = os.path.join(_BTAX_DIR,'depreciation')
_FIN_DIR = os.path.join(_BTAX_DIR, 'financial_policy')
_FOUT_DIR = os.path.join(_FIN_DIR, 'output')
_OUT_DIR = os.path.join(_DEPR_DIR, 'output')
sys.path.append(_DEPR_DIR)
sys.path.append(_BTAX_DIR)
from btax.depreciation.parameter_calibrations import calibrate_depr_rates
from btax.financial_policy.calibrate_financing import calibrate_financing

def run_firm_calibration(user_params):
	#calculates the depreciation rates
	depr_rates = calibrate_depr_rates(get_all = True)
	debt_ratios = calibrate_financing()
	#prints out the data for relevant industries only. Could be changed to allow users the ability to pick output format
	depr_rates = depr_rates[(depr_rates.NAICS=='11')|(depr_rates.NAICS=='211')|(depr_rates.NAICS=='212')|(depr_rates.NAICS=='213') 
	|(depr_rates.NAICS=='22')|(depr_rates.NAICS=='23')|(depr_rates.NAICS=='31-33')|(depr_rates.NAICS=='32411')|(depr_rates.NAICS == '336')
	|(depr_rates.NAICS=='3391')|(depr_rates.NAICS=='42')|(depr_rates.NAICS=='44-45')|(depr_rates.NAICS=='48-49')|(depr_rates.NAICS == '51')
	|(depr_rates.NAICS=='52')|(depr_rates.NAICS=='531')|(depr_rates.NAICS=='532')|(depr_rates.NAICS=='533')|(depr_rates.NAICS=='54')
	|(depr_rates.NAICS=='55')|(depr_rates.NAICS=='56')|(depr_rates.NAICS=='61')|(depr_rates.NAICS=='62')|(depr_rates.NAICS=='71')
	|(depr_rates.NAICS=='72')|(depr_rates.NAICS=='81')|(depr_rates.NAICS=='92')]

	debt_ratios = debt_ratios[(debt_ratios.NAICS=='11')|(debt_ratios.NAICS=='211')|(debt_ratios.NAICS=='212')|(debt_ratios.NAICS=='213') 
	|(debt_ratios.NAICS=='22')|(debt_ratios.NAICS=='23')|(debt_ratios.NAICS=='31-33')|(debt_ratios.NAICS=='32411')|(debt_ratios.NAICS == '336')
	|(debt_ratios.NAICS=='3391')|(debt_ratios.NAICS=='42')|(debt_ratios.NAICS=='44-45')|(debt_ratios.NAICS=='48-49')|(debt_ratios.NAICS == '51')
	|(debt_ratios.NAICS=='52')|(debt_ratios.NAICS=='531')|(debt_ratios.NAICS=='532')|(debt_ratios.NAICS=='533')|(debt_ratios.NAICS=='54')
	|(debt_ratios.NAICS=='55')|(debt_ratios.NAICS=='56')|(debt_ratios.NAICS=='61')|(debt_ratios.NAICS=='62')|(debt_ratios.NAICS=='71')
	|(debt_ratios.NAICS=='72')|(debt_ratios.NAICS=='81')|(debt_ratios.NAICS=='92')]
	depr_rates.to_csv(os.path.join(_OUT_DIR,'depreciation.csv'), index = False)
	debt_ratios.to_csv(os.path.join(_FOUT_DIR,'debt.csv'), index = False)

run_firm_calibration(user_params={})
'''
if __name__ == '__main__':
	run_firm_calibration(user_params={})
'''
	