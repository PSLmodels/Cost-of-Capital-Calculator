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
_IND_NAICS = os.path.join(_BEA_DIR, 'Industries.csv')
_NAICS_PATH = os.path.join(_BEA_DIR, 'NAICS_SOI_crosswalk.csv')
_ECON_DEPR_FILE = os.path.join(_RATE_DIR, 'Economic Depreciation Rates.csv')
_TAX_DEPR_FILE = os.path.join(_RATE_DIR, 'depr_allow_ads.csv')

def asset_calcs(params, fixed_assets):

	# grabs the constant values from the parameters dictionary
	inflation_rate = params['inflation rate']
	stat_tax = params['tax rate']
	discount_rate = params['discount rate']
	save_rate = params['return to savers']
	delta = params['econ depreciation']
	r_prime = params['after-tax rate']
	inv_credit = params['inv_credit']
	w = params['prop tax']
	# reshapes the economic depreciation parameter to a 96x3x2 matrix by first reshaping it into a 96x1x1 matrix then copying those values
	delta = np.tile(np.reshape(delta,(delta.shape[0],1,1)),(1,discount_rate.shape[0],discount_rate.shape[1]))
	z = params['depr allow']
	# calculates the cost of capital
	rho = ((discount_rate - inflation_rate) + delta) * (1- inv_credit- stat_tax * z) / (1- stat_tax) + w - delta
	# calculates the marginal effective tax rate
	metr = (rho - (r_prime - inflation_rate)) / rho
	# calculates the marginal effective total tax rate
	mettr = ((rho-save_rate)/rho)
	# aggregates all the fixed assets to the two digit naics code level
	agg_fa = aggregate_fixed_assets(fixed_assets)
	# calculates all the previous values: rho, metr, mettr at the industry level
	ind_rho, ind_metr, ind_mettr = industry_calcs(agg_fa, rho, metr, mettr)

	return rho, metr, mettr, ind_rho, ind_metr, ind_mettr

def industry_calcs(agg_fa, rho, metr, mettr):

	industries = pd.read_csv(_IND_NAICS)
	rho_data = np.zeros((len(industries), rho.shape[1], rho.shape[2]))
	metr_data = np.zeros((len(industries), rho.shape[1], rho.shape[2]))
	mettr_data = np.zeros((len(industries), rho.shape[1], rho.shape[2]))
	k=0
	for inds, assets in agg_fa.iteritems(): 
		ind_assets = np.tile(np.reshape(assets.T,(assets.shape[1],1,2)),((1,rho.shape[1],1)))
		rho_data[k] = sum(ind_assets * rho) / sum(assets.T)
		metr_data[k] = sum(ind_assets * metr) / sum(assets.T)
		mettr_data[k] = sum(ind_assets * mettr) / sum(assets.T)
		k+=1

	return rho_data, metr_data, mettr_data

def aggregate_fixed_assets(fixed_assets):

	keys = fixed_assets.keys()
	# aggregates the sub industries up to the 2 digit NAICS code level
	agg_fa = {}
	for key in keys:
		if(agg_fa.has_key(key[:2])):
			agg_fa[key[:2]] += fixed_assets[key]
		else:
			agg_fa[key[:2]] = fixed_assets[key]

	# handles the exceptions where an industry code covers multiple sub industries, summing them together
	exceptions = {'31-33': ['31','32','33'], '44-45': ['44'], '48-49': ['48', '49']}			
	for exc, children in exceptions.iteritems():
		for child_ind in children:
			if(agg_fa.has_key(exc)):
				agg_fa[exc] += agg_fa[child_ind]
			else:
				agg_fa[exc] = agg_fa[child_ind]
			del agg_fa[child_ind]

	return agg_fa