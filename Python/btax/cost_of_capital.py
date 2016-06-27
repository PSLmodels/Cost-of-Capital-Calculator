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
_ECON_DEPR_FILE = os.path.join(_RATE_DIR, 'Economic Depreciation Rates.csv')
_TAX_DEPR_FILE = os.path.join(_RATE_DIR, 'depr_allow.csv')

def asst_cost_of_capital():

	econ_depr = pd.read_csv(_ECON_DEPR_FILE)
	econ_depr = econ_depr.drop('Code',1)
	tax_depr_allow = pd.read_csv(_TAX_DEPR_FILE)
	depr_rates = np.array(econ_depr.merge(tax_depr_allow))
	params = param.get_params()
	inflation_rate = params['Inflation rate']
	corp_tax = params['Corporate tax rate']
	non_corp_tax = params['Non corporate tax rate']
	discount_rate = params['Discount rate']
	types = ['Corp', 'Non_corp']

	cost_of_capital = pd.DataFrame(index=np.arange(0,len(depr_rates)), columns=types)
	metr = pd.DataFrame(index=np.arange(0,len(depr_rates)), columns=types)
	for j in types:
		if(j == 'Corp'):
			tax_rate = corp_tax
		else:
			tax_rate = non_corp_tax
		for i in xrange(0, len(cost_of_capital)):
			cost_of_capital[j][i] = ((discount_rate - inflation_rate) + depr_rates[i][1]) * (1 - tax_rate * depr_rates[i][2]) / (1 - tax_rate) - depr_rates[i][1]
			metr[j][i] = (cost_of_capital[j][i] - discount_rate + inflation_rate) / cost_of_capital[j][i]
		

	return cost_of_capital

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
