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
from util import get_paths

globals().update(get_paths())


def asset_calcs(params):
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
	z = params['depr allow']
	financing_list = params['financing_list']
	entity_list = params['entity_list']

	# initialize dataframe - start w/ z output
	output_by_asset = z.copy()

	# merge in econ depreciation rates
	output_by_asset = pd.merge(output_by_asset, delta, how='left', left_on=['Asset Type'],
      right_on=['Asset'], left_index=False, right_index=False, sort=False,
      copy=True, indicator=False)

	# calculate the cost of capital, metr, mettr
	for i in range(save_rate.shape[0]):
		for j in range(save_rate.shape[1]):
			output_by_asset['rho'+entity_list[j]+financing_list[i]] = \
				((((discount_rate[i,j] - inflation_rate) +
				output_by_asset['delta']) * (1- inv_credit- (stat_tax[j] *
				output_by_asset['z'+entity_list[j]+financing_list[i]])) /
				(1-stat_tax[j])) + w - output_by_asset['delta'])
			output_by_asset['metr'+entity_list[j]+financing_list[i]] = \
				(output_by_asset['rho'+entity_list[j]+financing_list[i]] -
				(r_prime[i,j] - inflation_rate))/ output_by_asset['rho'+entity_list[j]+financing_list[i]]
			output_by_asset['mettr'+entity_list[j]+financing_list[i]] = \
				(output_by_asset['rho'+entity_list[j]+financing_list[i]] -
				save_rate[i,j])/ output_by_asset['rho'+entity_list[j]+financing_list[i]]

	return output_by_asset


def industry_calcs(params, fixed_assets, output_by_asset):
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
	# grabs the constant values from the parameters dictionary
	inflation_rate = params['inflation rate']
	stat_tax = params['tax rate']
	discount_rate = params['discount rate']
	save_rate = params['return to savers']
	delta = params['econ depreciation']
	r_prime = params['after-tax rate']
	inv_credit = params['inv_credit']
	w = params['prop tax']
	z = params['depr allow']
	financing_list = params['financing_list']
	entity_list = params['entity_list']

	# initialize dataframe - start w/ z output
	by_industry_asset = fixed_assets.copy()

	# merge cost of capital, depreciation rates by asset
	df2 = output_by_asset[['bea_asset_code', 'delta','z_c','z_c_d','z_c_e','z_nc', 'z_nc_d',
						'z_nc_e', 'rho_c','rho_c_d','rho_c_e','rho_nc',
						'rho_nc_d', 'rho_nc_e']]
	by_industry_asset = pd.merge(by_industry_asset, df2, how='left', left_on=['bea_asset_code'],
      right_on=['bea_asset_code'], left_index=False, right_index=False, sort=False,
      copy=True, indicator=False)

	# create weighted averages by industry/tax treatment
	by_industry = pd.DataFrame({'delta' : by_industry_asset.groupby( ['bea_ind_code'] ).apply(wavg, "delta", "assets")}).reset_index()
	col_list = ['z_c','z_c_d','z_c_e','z_nc', 'z_nc_d',
						'z_nc_e', 'rho_c','rho_c_d','rho_c_e','rho_nc',
						'rho_nc_d', 'rho_nc_e']
	for item in col_list:
		by_industry[item] = (pd.DataFrame({item : by_industry_asset.groupby('bea_ind_code').apply(wavg, item, "assets")})).reset_index()[item]


	## Why giving same means for all industries???

	# merge in industry names
	df3 = fixed_assets[['Industry','bea_ind_code']]
	by_industry = pd.merge(by_industry, df3, how='left', left_on=['bea_ind_code'],
      right_on=['bea_ind_code'], left_index=False, right_index=False, sort=False,
      copy=True, indicator=False)


	return by_industry

def wavg(group, avg_name, weight_name):
    """
    Computes a weighted average
    """
    d = group[avg_name]
    w = group[weight_name]
    try:
        #return (d * w).sum() / w.sum()
		return d.mean()
    except ZeroDivisionError:
        return d.mean()

def industry_calcs_old(agg_fa, rho_asset, parameters):
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

	return rho, metr, mettr, delta, z

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
