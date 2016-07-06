import os.path
import sys
import pandas as pd
import numpy as np
import parameters as param

_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
_OUT_DIR = os.path.join(_CUR_DIR, 'output')
_DEPR_DIR = os.path.join(_CUR_DIR, 'depreciation')
_DATA_DIR = os.path.join(_DEPR_DIR, 'data')
_RATE_DIR = os.path.join(_DATA_DIR, 'depreciation_rates')
_RAW_DIR = os.path.join(_DATA_DIR, 'raw_data')
_BEA_DIR = os.path.join(_RAW_DIR, 'BEA')
_NAICS_PATH = os.path.join(_BEA_DIR, 'NAICS_SOI_crosswalk.csv')
_ECON_DEPR_FILE = os.path.join(_RATE_DIR, 'Economic Depreciation Rates.csv')
_TAX_DEPR_FILE = os.path.join(_RATE_DIR, 'depr_allow.csv')

def asset_cost_of_capital(fixed_assets):

	econ_depr = pd.read_csv(_ECON_DEPR_FILE)
	econ_depr = econ_depr.drop('Code',1)
	tax_depr_allow = pd.read_csv(_TAX_DEPR_FILE)
	depr_rates = np.array(econ_depr.merge(tax_depr_allow))
	# grabs the constant values from the parameters dictionary
	params = param.get_params()
	inflation_rate = params['Inflation rate']
	corp_tax = params['Corporate tax rate']
	non_corp_tax = params['Non corporate tax rate']
	corp_discount_rate = params['Corporate discount rate']
	non_corp_discount_rate = params['Non corporate discount rate']
	types = ['corp', 'non_corp']
	column_types = types + ['corp_assets', 'non_corp_assets']

	# calculates the cost of capital by asset type 
	cost_of_capital = pd.DataFrame(index=np.arange(0,len(depr_rates)), columns=column_types)
	metr = pd.DataFrame(index=np.arange(0,len(depr_rates)), columns=types)

	agg_fa = aggregate_fixed_assets(fixed_assets, types)

	for j in types:
		new_type = j + '_assets'
		# chooses the corporate or non-corporate tax for the statutory tax rate
		if(j == 'corp'):
			tax_rate = corp_tax
			discount_rate = corp_discount_rate
		else:
			tax_rate = non_corp_tax
			discount_rate = non_corp_discount_rate
		for i in xrange(0, len(cost_of_capital)):
			# calculates the cost of capital using input parameters and depreciation rates
			cost_of_capital[j][i] = ((discount_rate - inflation_rate) + depr_rates[i][1]) * (1 - tax_rate * depr_rates[i][2]) / (1 - tax_rate) - depr_rates[i][1]
			cost_of_capital[new_type][i] = 0
			for code, assets in agg_fa.iteritems():
				cost_of_capital[new_type][i] += assets[j][i]
			# also calculates the marginal effective tax rate by asset and entity type
			metr[j][i] = (cost_of_capital[j][i] - discount_rate + inflation_rate) / cost_of_capital[j][i]
	import ipdb
	ipdb.set_trace()
	agg_cc = pd.DataFrame(index=np.arange(0, len(agg_fa)), columns=['NAICS', 'corp', 'non_corp', 'corp_assets', 'non_corp_assets'])
	asst_cc = {}
	# calculates the cost of capital by industry and entity type
	for i in types:
		asst_cc[i] = np.array(cost_of_capital[i])
	l = 0
	for code, assets in agg_fa.iteritems():
		agg_cc['NAICS'][l] = code
		for i in types:
			new_type = i + '_assets'
			agg_cc[i][l] = sum(assets[i] * asst_cc[i]) / sum(assets[i])
			agg_cc[new_type][l] = sum(assets[i])
		l += 1

	agg_cc = agg_cc.sort('NAICS')
	agg_cc = agg_cc.fillna(0)
	agg_cc.index = np.arange(0, len(agg_cc))
	import ipdb
	ipdb.set_trace()
	return agg_cc


def calc_cost_of_capital(depr_params, discount_rates):
	discount_rate = np.array(discount_rates['corp'])
	depr_allow = np.array(depr_params['Tax_Corp'])
	econ_depr = np.array(depr_params['Econ_Corp'])
	corp_tax = 0.391 #corporate tax rate in the US

	cost_of_capital = ((discount_rate + econ_depr) * (1 - corp_tax * depr_allow) / (1 - corp_tax)) - econ_depr
	capital_df = pd.DataFrame(cost_of_capital, columns=['Corp'])
	naics_codes = pd.DataFrame(discount_rates['NAICS'], columns=['NAICS'])

	capital_df = pd.concat([naics_codes, capital_df], axis=1)
	save_capital(capital_df)

	return capital_df

def save_capital(capital_df):
	capital_df = capital_df[(capital_df.NAICS=='11')|(capital_df.NAICS=='211')|(capital_df.NAICS=='212')|(capital_df.NAICS=='213') 
    |(capital_df.NAICS=='22')|(capital_df.NAICS=='23')|(capital_df.NAICS=='31-33')|(capital_df.NAICS=='32411')|(capital_df.NAICS == '336')
    |(capital_df.NAICS=='3391')|(capital_df.NAICS=='42')|(capital_df.NAICS=='44-45')|(capital_df.NAICS=='48-49')|(capital_df.NAICS == '51')
    |(capital_df.NAICS=='52')|(capital_df.NAICS=='531')|(capital_df.NAICS=='532')|(capital_df.NAICS=='533')|(capital_df.NAICS=='54')
    |(capital_df.NAICS=='55')|(capital_df.NAICS=='56')|(capital_df.NAICS=='61')|(capital_df.NAICS=='62')|(capital_df.NAICS=='71')
    |(capital_df.NAICS=='72')|(capital_df.NAICS=='81')|(capital_df.NAICS=='92')]
	
	capital_df.to_csv(os.path.join(_OUT_DIR,'cost_of_capital.csv'), index = False)


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