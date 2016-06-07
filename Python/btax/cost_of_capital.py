import os.path
import sys
import pandas as pd
import numpy as np

_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
_OUT_DIR = os.path.join(_CUR_DIR, 'output')

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
