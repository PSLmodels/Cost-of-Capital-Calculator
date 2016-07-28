"""
Calculate Rho, METR, & METTR (calc_final_output.py):
-------------------------------------------------------------------------------

This module provides functions for calculating the cost of capital (rho), marginal effective tax rate
(METR) and marginal effective total tax rate (METTR). Using the parameters from parameters.py values for
rho, metr, and mettr are calculated for each BEA asset type. Then values are calculated for rho and metr
at the industry level. This script also contains a function which aggregates the fixed asset data to the
two digit NAICS code level. Last Updated 7/27/2016
"""
# Packages
import os.path
import sys
import pandas as pd
import numpy as np
import parameters as param
# File paths
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
	"""Computes rho, METR, and METTR at the asset level.

		:param params: Constants used in the calculation
		:param fixed_assets: Fixed asset data for each industry
		:type params: dictionary
		:type fixed_assets: dictionary
		:returns: rho, METR, METTR, ind_rho, ind_METR
		:rtype: 96x3x2, DataFrame
	"""
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
	ind_rho, ind_metr = industry_calcs(agg_fa, rho, metr)

	return rho, metr, mettr, ind_rho, ind_metr

def industry_calcs(agg_fa, rho, metr):
	"""Calculates the cost of capital and marginal effective tax rates by industry

		:param agg_fa: Fixed assets organized by entity, asset, and industry
		:param rho: Cost of capital by asset
		:param metr: Marginal effective tax rate by asset
		:type agg_fa: dictionary
		:type rho: 96x3x2 Array
		:type metr: 96x3x2 Array
		:returns: The result of the weighted average of the cost of capital and METR for each BEA industry
		:rtype: DataFrame  
	"""
	industries = pd.read_csv(_IND_NAICS)
	rho_df = pd.DataFrame(industries)
	# Creates dataframes with the industry names, NAICS codes and 3x2 Arrays
	rho_df['Data Array'] =  [np.zeros((rho.shape[1], rho.shape[2]))]*len(industries)
	metr_df = pd.DataFrame(industries)
	metr_df['Data Array'] =  [np.zeros((rho.shape[1], rho.shape[2]))]*len(industries)

	for inds, assets in agg_fa.iteritems():
		index=rho_df[rho_df.NAICS==inds].index 
		ind_assets = np.tile(np.reshape(assets.T,(assets.shape[1],1,2)),((1,rho.shape[1],1)))
		# Calculates the weighted average for the cost of capital 
		rho_df['Data Array'][index] = [sum(ind_assets * rho) / sum(assets.T)]
		# Calculates the weighted average for the marginal effective tax rate
		metr_df['Data Array'][index] = [sum(ind_assets * metr) / sum(assets.T)]

	return rho_df, metr_df

def aggregate_fixed_assets(fixed_assets):
	"""Aggregates the fixed assets of the industries to the 2 digit NAICS code level

		:param fixed_assets: Fixed asset data for each industry
		:type fixed_assets: dictionary
		:returns: The aggregation of the fixed assets
		:rtype: dictionary 
	"""
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