'''
Script (run_btax.py):
-------------------------------------------------------------------------------
Last updated: 7/11/2016.

'''
import os.path
import sys
import pandas as pd
import numpy as np
import cPickle as pickle
from btax.soi_processing import pull_soi_data
from btax.calc_final_outputs import asset_calcs, get_paths
from btax.check_output import check_output
from btax.util import get_paths, read_from_egg
import btax.read_bea as read_bea
import btax.soi_processing as soi
import btax.parameters as params

globals().update(get_paths())

def run_btax(user_params):
	sector_dfs = pull_soi_data()
	fixed_assets = read_bea.read_bea(sector_dfs)
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

	tax_depr = pd.read_csv(_TAX_DEPR)
	vars_by_asset['Asset Type'] = tax_depr['Asset Type']
	vars_by_asset['delta'] = parameters['econ depreciation']

	ind_naics = pd.read_csv(_IND_NAICS)
	ind_columns = ['Industry', 'NAICS', 'rho_c', 'rho_c_d', 'rho_c_e', 'rho_nc', 'metr_c', 'metr_c_d', 'metr_c_e',
		'metr_nc']
	vars_by_industry = pd.DataFrame(index=np.arange(0, len(ind_naics)), columns=ind_columns)
	vars_by_industry['Industry'] = ind_naics['Industry']
	vars_by_industry['NAICS'] = ind_naics['NAICS']

	vars_by_asset['z_nc'] = parameters['depr allow'][:,0,1]
	vars_by_asset['rho_nc'] = rho[:,0,1]
	vars_by_asset['metr_nc'] = metr[:,0,1]
	vars_by_asset['mettr_nc'] = mettr[:,0,1]
	vars_by_industry['rho_nc'] = ind_rho[:,0,1]
	vars_by_industry['metr_nc'] = ind_metr[:,0,1]

	suffix_list = ['', '_d', '_e']
	for i in range(rho.shape[1]):
	    vars_by_asset['z_c'+suffix_list[i]] = parameters['depr allow'][:,i,0]
	    vars_by_asset['rho_c'+suffix_list[i]] = rho[:,i,0]
	    vars_by_asset['metr_c'+suffix_list[i]] = metr[:,i,0]
	    vars_by_asset['mettr_c'+suffix_list[i]] = mettr[:,i,0]
	    vars_by_industry['rho_c'+suffix_list[i]] = ind_rho[:,i,0]
	    vars_by_industry['metr_c'+suffix_list[i]] = ind_metr[:,i,0]

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

	# join CBO data to ours
	# import difflib
	# df2 = vars_by_asset.copy()
	# df1 = CBO_data.copy()
	# df2['Asset Type'] = df2['Asset Type'].apply(lambda x: difflib.get_close_matches(x, df1['Asset Type'])[0])
	# df1.merge(df2)
	# print df1.head(n=5)
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

	#print CBO_v_OSPC.index
	# print CBO_v_OSPC.columns
	# print CBO_v_OSPC.shape
	# print CBO_v_OSPC.T.drop_duplicates().T

	# quit()

	CBO_v_OSPC = CBO_v_OSPC.T.drop_duplicates().T


	diff_list = [None] * len(OSPC_list)
	for i in xrange(0,len(OSPC_list)):
		CBO_v_OSPC[OSPC_list[i]+'_diff'] = CBO_v_OSPC[OSPC_list[i]] - CBO_v_OSPC[CBO_list[i]]
		diff_list[i] = OSPC_list[i]+'_diff'

	cols_to_print = ['Asset Type']+OSPC_list + CBO_list + diff_list

	CBO_v_OSPC[cols_to_print].to_csv(_OUT_DIR+'/CBO_v_OSPC.csv',encoding='utf-8')

	with open(os.path.join(_OUT_DIR, 'final_output.pkl'), 'wb') as handle:
		pickle.dump(vars_by_asset, handle)

	return vars_by_asset

def main():
    run_btax(user_params={})

if __name__ == '__main__':
	main()

