"""
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
"""
import os.path
import sys
_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
_BTAX_DIR = os.path.join(_CUR_DIR, 'btax')
_DEPR_DIR = os.path.join(_BTAX_DIR,'depreciation')
_OUT_DIR = os.path.join(_DEPR_DIR, 'output')
sys.path.append(_DEPR_DIR)
sys.path.append(_BTAX_DIR)
from btax.depreciation.parameter_calibrations import calibrate_depr_rates

def run_firm_calibration(user_params):
	#calculates the depreciation rates
	depr_rates = calibrate_depr_rates(get_all = True)
	#prints out the data for relevant industries only. Could be changed to allow users the ability to pick output format
	depr_rates = depr_rates[(depr_rates.NAICS=='11')|(depr_rates.NAICS=='211')|(depr_rates.NAICS=='212')|(depr_rates.NAICS=='213') 
	|(depr_rates.NAICS=='22')|(depr_rates.NAICS=='23')|(depr_rates.NAICS=='31-33')|(depr_rates.NAICS=='32411')|(depr_rates.NAICS == '336')
	|(depr_rates.NAICS=='3391')|(depr_rates.NAICS=='42')|(depr_rates.NAICS=='44-45')|(depr_rates.NAICS=='48-49')|(depr_rates.NAICS == '51')
	|(depr_rates.NAICS=='52')|(depr_rates.NAICS=='531')|(depr_rates.NAICS=='532')|(depr_rates.NAICS=='533')|(depr_rates.NAICS=='54')
	|(depr_rates.NAICS=='55')|(depr_rates.NAICS=='56')|(depr_rates.NAICS=='61')|(depr_rates.NAICS=='62')|(depr_rates.NAICS=='71')
	|(depr_rates.NAICS=='72')|(depr_rates.NAICS=='81')|(depr_rates.NAICS=='92')]
	depr_rates.to_csv(os.path.join(_OUT_DIR,'depreciation.csv'), index = False)

run_firm_calibration(user_params={})
'''
if __name__ == '__main__':
	run_firm_calibration(user_params={})
'''
	