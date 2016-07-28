"""
Runner Script (run_btax.py):
-------------------------------------------------------------------------------
Initial module that contains the method to start the calculations in B-Tax. Makes function calls to split out fixed assets by entity type
(pull_soi_data), allocate fixed assets to industries (read_bea), grab all the parameters for the final calculations (get_params), and 
calculate the Cost of Capital, Marginal Effective Tax Rates, and Marginal Effective Total Tax Rates (asset_calcs). Additionally, this 
method compares the calculated values with those produced by the CBO.
Last updated: 7/25/2016.

"""
# Import packages
import os.path
import sys
import pandas as pd
import numpy as np
import cPickle as pickle
# Create file paths
_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
_MAIN_DIR = os.path.dirname(_CUR_DIR)
_REF_DIR = os.path.join(_MAIN_DIR, 'References')
_BTAX_DIR = os.path.join(_CUR_DIR, 'btax')
_DATA_DIR = os.path.join(_BTAX_DIR, 'data')
_RATE_DIR = os.path.join(_DATA_DIR, 'depreciation_rates')
_RAW_DIR = os.path.join(_DATA_DIR, 'raw_data')
_BEA_DIR = os.path.join(_RAW_DIR, 'BEA')
_OUT_DIR = os.path.join(_BTAX_DIR, 'output')
_TAX_DEPR = os.path.join(_RATE_DIR, 'BEA_IRS_Crosswalk.csv')
_IND_NAICS = os.path.join(_BEA_DIR, 'Industries.csv')
sys.path.append(_BTAX_DIR)
# Import custom modules and methods
from btax.soi_processing import pull_soi_data
from btax.calc_final_outputs import asset_calcs
from btax.check_output import check_output
import read_bea
import soi_processing as soi
import parameters as params

def run_btax(user_params):
	"""Runner script that kicks off the calculations for B-Tax

		:param user_params: The user input for implementing reforms
		:type user_params: dictionary
		:returns: METR (by industry and asset) and METTR (by asset)
		:rtype: DataFrame
	"""
	# break out the asset data by entity type (c corp, s corp, sole proprietorships, and partners)
	entity_dfs = pull_soi_data()
	# read in the BEA data on fixed assets and separate them by corp and non-corp
	fixed_assets = read_bea.read_bea(entity_dfs)
	# get parameters
	parameters = params.get_params()

	# make calculations
	rho, metr, mettr, ind_rho, ind_metr = asset_calcs(parameters, fixed_assets)

	# format output
	numberOfRows = (parameters['econ depreciation']).shape[0]
	column_list = ['Asset Type', 'delta', 'z_c', 'z_c_d', 'z_c_e', 'z_nc',
		'rho_c', 'rho_c_d', 'rho_c_e', 'rho_nc', 'metr_c', 'metr_c_d', 'metr_c_e',
		'metr_nc', 'mettr_c', 'mettr_c_d', 'mettr_c_e', 'mettr_nc']
	vars_by_asset = pd.DataFrame(index=np.arange(0, numberOfRows), columns=column_list)
	# fills out columns for asset names and economic depreciation
	tax_depr = pd.read_csv(_TAX_DEPR)
	vars_by_asset['Asset Type'] = tax_depr['Asset Type']
	vars_by_asset['delta'] = parameters['econ depreciation']

	# format output
	ind_naics = pd.read_csv(_IND_NAICS)
	ind_columns = ['Industry', 'NAICS', 'rho_c', 'rho_c_d', 'rho_c_e', 'rho_nc', 'metr_c', 'metr_c_d', 'metr_c_e',
		'metr_nc']
	vars_by_industry = pd.DataFrame(index=np.arange(0, len(ind_naics)), columns=ind_columns)
	# fills out columns for NAICS codes and industry names
	vars_by_industry['Industry'] = ind_naics['Industry']
	vars_by_industry['NAICS'] = ind_naics['NAICS']

	new_rho = np.zeros((len(ind_rho), rho.shape[1], rho.shape[2]))
	new_metr = np.zeros((len(ind_metr), rho.shape[1], rho.shape[2]))
	for i,array in enumerate(np.array(ind_rho['Data Array'])):
		new_rho[i] = array

	for i, array in enumerate(np.array(ind_metr['Data Array'])):
		new_metr[i] = array	

	# fills in the output columns on the dataframe from the output arrays 
	vars_by_asset['z_nc'] = parameters['depr allow'][:,0,1]
	vars_by_asset['rho_nc'] = rho[:,0,1]
	vars_by_asset['metr_nc'] = metr[:,0,1]
	vars_by_asset['mettr_nc'] = mettr[:,0,1]
	vars_by_industry['rho_nc'] = new_rho[:,0,1]
	vars_by_industry['metr_nc'] = new_metr[:,0,1]

	# continues to fill out the output DataFrame for a mix, debt, and equity financing
	suffix_list = ['', '_d', '_e']
	for i in range(rho.shape[1]):
	    vars_by_asset['z_c'+suffix_list[i]] = parameters['depr allow'][:,i,0]
	    vars_by_asset['rho_c'+suffix_list[i]] = rho[:,i,0]
	    vars_by_asset['metr_c'+suffix_list[i]] = metr[:,i,0]
	    vars_by_asset['mettr_c'+suffix_list[i]] = mettr[:,i,0]
	    vars_by_industry['rho_c'+suffix_list[i]] = new_rho[:,i,0]
	    vars_by_industry['metr_c'+suffix_list[i]] = new_metr[:,i,0]

	vars_by_industry = vars_by_industry.fillna(0)
	# save to csv for comparison to CBO
	vars_by_industry.to_csv(os.path.join(_OUT_DIR,'calculations_by_industry.csv'), index=False)
	vars_by_asset.to_csv(_OUT_DIR+'/calculations_by_asset.csv', index=False)

	# read in CBO file
	CBO_data = pd.read_excel(os.path.join(_REF_DIR, 'effective_taxrates.xls'),
		sheetname='Full detail', header=1, skiprows=0, skip_footer=8)
	CBO_data.columns = [col.encode('ascii', 'ignore') for col in CBO_data]
	CBO_data.rename(columns = {'Top page (Rows 3-35): Equipment        Bottom page (Rows 36-62): All Other ':'Asset Type'}, inplace = True)
	CBO_data.to_csv(_OUT_DIR+'/CBO_data.csv',encoding='utf-8')
	# creates a DataFrame for the intersection of the CBO and our calculations (joined on the asset name)
	CBO_v_OSPC = vars_by_asset.merge(CBO_data,how='inner',on='Asset Type')


	OSPC_list = ['delta','z_c','z_c_d','z_c_e','z_nc','rho_c','rho_c_d','rho_c_e','rho_nc',
	       'metr_c', 'metr_c_d', 'metr_c_e', 'mettr_c', 'mettr_c_d', 'mettr_c_e', 
	       'mettr_nc']
	CBO_list = ['Economic deprecia- tion rate []','Corporate: total [z(c)]',
	      'Corporate: debt-financed [z(c,d)]', 'Corporate: equity-financed [z(c,e)]', 
	      'Non-corporate [z(n)]', 'Corporate: total [(c)]', 'Corporate: debt-financed [(c,d)]', 
	      'Corporate: equity-financed [(c,e)]', 'Non-corporate [(n)]', 'Corporate: total [ETR(c)]', 
	      'Corporate: debt-financed [ETR(c,d)]', 'Corporate: equity-financed [ETR(c,e)]',
	      'Corporate: total [ETTR(c)]', 'Corporate: debt-financed [ETTR(c,d)]', 
	      'Corporate: equity-financed [ETTR(c,e)]', 'Non-corporate [ETTR(n)]']
	CBO_v_OSPC = CBO_v_OSPC.T.drop_duplicates().T

	# compares the CBO's calculations with our calculations and calculates the difference
	diff_list = [None] * len(OSPC_list)
	for i in xrange(0,len(OSPC_list)):
		CBO_v_OSPC[OSPC_list[i]+'_diff'] = CBO_v_OSPC[OSPC_list[i]] - CBO_v_OSPC[CBO_list[i]]
		diff_list[i] = OSPC_list[i]+'_diff'

	# prints the comparison data
	cols_to_print = ['Asset Type']+OSPC_list + CBO_list + diff_list
	CBO_v_OSPC[cols_to_print].to_csv(_OUT_DIR+'/CBO_v_OSPC.csv',encoding='utf-8')

	# creates a .pkl file of the output DataFrame
	with open(os.path.join(_OUT_DIR, 'final_output.pkl'), 'wb') as handle:
		pickle.dump(vars_by_asset, handle)

	return vars_by_asset, vars_by_industry

if __name__ == '__main__':
	run_btax(user_params={})

	