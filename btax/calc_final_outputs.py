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
from btax.util import get_paths

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
      copy=True)
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

    '''
    ------------------------------------------
    Define asset categories
    ------------------------------------------
    '''

    asset_categories = {'Computers and Software', 'Office and Residential Equipment',
        'Instruments and Communications Equipment', 'Transportation Equipment',
        'Industrial Machinery', 'Other Industrial Equipment', 'Other Equipment',
        'Residential Buildings', 'Nonresidential Buildings',
        'Mining and Drilling Structures', 'Other Structures'}
    asset_dict = dict.fromkeys(['Mainframes','PCs','DASDs','Printers',
          'Terminals','Tape drives','Storage devices','System integrators',
          'Prepackaged software','Custom software','Own account software'],'Computers and Software')
    asset_dict.update(dict.fromkeys(['Communications','Nonelectro medical instruments',
          'Electro medical instruments','Nonmedical instruments','Photocopy and related equipment',
          'Office and accounting equipment'],'Instruments and Communications Equipment'))
    asset_dict.update(dict.fromkeys(['Household furniture','Other furniture','Household appliances'],
          'Office and Residential Equipment'))
    asset_dict.update(dict.fromkeys(['Light trucks (including utility vehicles)',
          'Other trucks, buses and truck trailers','Autos','Aircraft',
          'Ships and boats','Railroad equipment','Steam engines','Internal combustion engines'],
          'Transportation Equipment'))
    asset_dict.update(dict.fromkeys(['Special industrial machinery','General industrial equipment'],
          'Industrial Machinery'))
    asset_dict.update(dict.fromkeys(['Nuclear fuel','Other fabricated metals',
          'Metalworking machinery','Electric transmission and distribution',
          'Other agricultural machinery','Farm tractors','Other construction machinery',
          'Construction tractors','Mining and oilfield machinery'],
          'Other Industrial Equipment'))
    asset_dict.update(dict.fromkeys(['Service industry machinery','Other electrical','Other'],
          'Other Equipment'))
    # my_dict.update(dict.fromkeys([],
    #       'Residential Buildings'))
    asset_dict.update(dict.fromkeys(['Office','Hospitals','Special care','Medical buildings','Multimerchandise shopping',
          'Food and beverage establishments','Warehouses','Mobile structures','Other commercial',
          'Religious','Educational and vocational','Lodging'],
          'Nonresidential Buildings'))
    asset_dict.update(dict.fromkeys(['Gas','Petroleum pipelines','Communication',
          'Petroleum and natural gas','Mining'],'Mining and Drilling Structures'))
    asset_dict.update(dict.fromkeys(['Manufacturing','Electric','Wind and solar',
          'Amusement and recreation','Air transportation','Other transportation',
          'Other railroad','Track replacement','Local transit structures',
          'Other land transportation','Farm','Water supply','Sewage and waste disposal',
          'Public safety','Highway and conservation and development'],
          'Other Structures'))
    asset_dict.update(dict.fromkeys(['Pharmaceutical and medicine manufacturing',
          'Chemical manufacturing, ex. pharma and med','Semiconductor and other component manufacturing',
          'Computers and peripheral equipment manufacturing','Communications equipment manufacturing',
          'Navigational and other instruments manufacturing','Other computer and electronic manufacturing, n.e.c.',
          'Motor vehicles and parts manufacturing','Aerospace products and parts manufacturing',
          'Other manufacturing','Scientific research and development services','Software publishers',
          'Financial and real estate services','Computer systems design and related services','All other nonmanufacturing, n.e.c.',
          'Private universities and colleges','Other nonprofit institutions','Theatrical movies','Long-lived television programs',
          'Books','Music'],'Intellectual Property'))

    # create asset category variable
    output_by_asset['asset_category'] = output_by_asset['Asset Type']
    output_by_asset['asset_category'].replace(asset_dict,inplace=True)


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
      copy=True)

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
	df3.drop_duplicates(inplace=True)
	by_industry = pd.merge(by_industry, df3, how='left', left_on=['bea_ind_code'],
      right_on=['bea_ind_code'], left_index=False, right_index=False, sort=False,
      copy=True)

	# define major industry groupings
	major_industries = {'Agriculture, forestry, fishing, and hunting', 'Mining',
	    'Utilities', 'Construction',
	    'Manufacturing', 'Wholesale trade', 'Retail trade',
	    'Transportation and warehousing', 'Information',
	    'Finance and insurance', 'Real estate and rental and leasing',
		'Professional, scientific, and technical services',
		'Management of companies and enterprises', 'Administrative and waste management services',
		'Educational services', 'Health care and social assistance',
		'Arts, entertainment, and recreation', 'Accommodation and food services',
		'Other services, except government'}
	ind_dict = dict.fromkeys(['Farms','Forestry, fishing, and related activities'],
								'Agriculture, forestry, fishing, and hunting')
	ind_dict.update(dict.fromkeys(['Oil and gas extraction',
	      'Mining, except oil and gas','Support activities for mining'],'Mining'))
	ind_dict.update(dict.fromkeys(['Utilities'],'Utilities'))
	ind_dict.update(dict.fromkeys(['Construction'],'Construction'))
	ind_dict.update(dict.fromkeys(['Wood products', 'Nonmetallic mineral products',
									'Primary metals', 'Fabricated metal products',
									'Machinery','Computer and electronic products',
									'Electrical equipment, appliances, and components',
									'Motor vehicles, bodies and trailers, and parts',
									'Other transportation equipment',
									'Furniture and related products',
									'Miscellaneous manufacturing',
									'Food, beverage, and tobacco products',
									'Textile mills and textile products',
									'Apparel and leather and allied products',
									'Paper products', 'Printing and related support activities',
									'Petroleum and coal products', 'Chemical products',
									'Plastics and rubber products'],'Manufacturing'))
	ind_dict.update(dict.fromkeys(['Wholesale trade'],'Wholesale trade'))
	ind_dict.update(dict.fromkeys(['Retail trade'],'Retail trade'))
	ind_dict.update(dict.fromkeys(['Air transportation', 'Railroad transportation',
									'Water transportation', 'Truck transportation',
									'Transit and ground passenger transportation',
									'Pipeline transportation',
									'Other transportation and support activitis',
									'Warehousing and storage'],'Transportation and warehousing'))
	ind_dict.update(dict.fromkeys(['Publishing industries (including software)',
									'Motion picture and sound recording industries',
									'Broadcasting and telecommunications',
									'Information and telecommunications'],
									'Information'))
	ind_dict.update(dict.fromkeys(['Federal Reserve banks',
								'Credit intermediation and related activities',
								'Securities, commodity contracts, and investments',
								'Insurance carriers and related activities',
								'Funds, trusts, and other financial vehicles'],
							'Finance and insurance'))
	ind_dict.update(dict.fromkeys(['Real estate',
							'Rental and leasing services and lessors of intangible assets'],
							'Real estate and rental and leasing'))
	ind_dict.update(dict.fromkeys(['Legal services',
							'Computer systems design and related services',
							'Miscellaneous professional, scientific, and technical services'],
							'Professional, scientific, and technical services'))
	ind_dict.update(dict.fromkeys(['Management of companies and enterprises'],
							'Management of companies and enterprises'))
	ind_dict.update(dict.fromkeys(['Administrative and support services',
							'Waster management and remediation services'],
							'Administrative and waste management services'))
	ind_dict.update(dict.fromkeys(['Educational services'],
							'Educational services'))
	ind_dict.update(dict.fromkeys(['Ambulatory health care services',
							'Hospitals', 'Nursing and residential care facilities',
							'Social assistance'],
							'Health care and social assistance'))
	ind_dict.update(dict.fromkeys(['Performing arts, spectator sports, museums, and related activities',
							'Amusements, gambling, and recreation industries'],
							'Arts, entertainment, and recreation'))
	ind_dict.update(dict.fromkeys(['Accomodation',
							'Food services and drinking places'],
							'Accommodation and food services'))
	ind_dict.update(dict.fromkeys(['Other services, except government'],
							'Other services, except government'))


	# create major industry variable
	by_industry['major_industry'] = by_industry['Industry']
	by_industry['major_industry'].replace(ind_dict,inplace=True)

	## the above is not quite working

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
