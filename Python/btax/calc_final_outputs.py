import os.path
import sys
import pandas as pd
import numpy as np
import parameters as param

_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
_OUT_DIR = os.path.join(_CUR_DIR, 'output')
_DATA_DIR = os.path.join(_CUR_DIR, 'data')
_RATE_DIR = os.path.join(_DATA_DIR, 'depreciation_rates')
_RAW_DIR = os.path.join(_DATA_DIR, 'raw_data')
_BEA_DIR = os.path.join(_RAW_DIR, 'BEA')
_NAICS_PATH = os.path.join(_BEA_DIR, 'NAICS_SOI_crosswalk.csv')
_ECON_DEPR_FILE = os.path.join(_RATE_DIR, 'Economic Depreciation Rates.csv')
_TAX_DEPR_FILE = os.path.join(_RATE_DIR, 'depr_allow_ads.csv')

def asset_cost_of_capital(fixed_assets):

	econ_depr = pd.read_csv(_ECON_DEPR_FILE)
	econ_depr = econ_depr.drop('Code',1)
	tax_depr_allow = pd.read_csv(_TAX_DEPR_FILE)
	depr_rates = np.array(econ_depr.merge(tax_depr_allow))
	# grabs the constant values from the parameters dictionary
	params = param.get_params()
	inflation_rate = params['inflation rate']
	stat_tax = params['tax rate']
	discount_rate = params['discount rate']
	save_rate = params['return to savers']
	delta = params['econ depreciation']
	r_prime = params['after-tax rate']
	inv_credit = params['inv_credit']
	w = params['prop tax']
	delta = np.tile(np.reshape(delta,(delta.shape[0],1,1)),(1,discount_rate.shape[0],discount_rate.shape[1]))
	z = params['depr allow']
	rho = ((discount_rate - inflation_rate) + delta) * (1- inv_credit- stat_tax * z) / (1- stat_tax) + w - delta
	metr = (rho - (r_prime - inflation_rate)) / rho
	mettr = ((rho-save_rate)/rho)
	
	return rho, metr, mettr


def aggregate_fixed_assets(fixed_assets, types):

	keys = fixed_assets.keys()

	# aggregates the sub industries up to the 2 digit NAICS code level
	agg_fa = {}
	for i in types:
		for key in keys:
			if(agg_fa.has_key(key[:2]) and agg_fa[key[:2]].has_key(i)):
				agg_fa[key[:2]][i] += fixed_assets[key][i]
			elif(agg_fa.has_key(key[:2]) and not agg_fa[key[:2]].has_key(i)):
				agg_fa[key[:2]].update({i: fixed_assets[key][i]})
			else:
				agg_fa[key[:2]] = {i: fixed_assets[key][i]}

	# handles the exceptions where an industry code covers multiple sub industries, summing them together
	exceptions = {'31-33': ['31','32','33'], '44-45': ['44'], '48-49': ['48', '49']}			
	for exc, children in exceptions.iteritems():
		for child_ind in children:
			for i in types:
				if(agg_fa.has_key(exc)):
					if(agg_fa[exc].has_key(i)):
						agg_fa[exc][i] += agg_fa[child_ind][i]
					else:
						agg_fa[exc].update({i: agg_fa[child_ind][i]})
				else:
					agg_fa[exc] = {i: agg_fa[child_ind][i]}
			del agg_fa[child_ind]

	return agg_fa