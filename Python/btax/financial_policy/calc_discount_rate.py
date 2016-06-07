import pandas as pd
import numpy as np
import os.path

_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_CUR_DIR,'data')
_OUT_DIR = os.path.join(_CUR_DIR, 'output')
_NAICS_CODES = os.path.join(_DATA_DIR, 'NAICS_Codes.csv')

def calc_real_discount_rate(indust_debt):
	corp_discount = calc_corp(indust_debt)
	corp_df = pd.DataFrame(corp_discount, columns = ['corp'])
	non_corp_discount = calc_non_corp(indust_debt)
	non_corp_df = pd.DataFrame(non_corp_discount, columns = ['non_corp'])
	#ooh_discount = calc_ooh(indust_debt)

	total_discount_rates = pd.concat([pd.read_csv(_NAICS_CODES), corp_df, non_corp_df], axis = 1)
	total_discount_rates.columns = ['NAICS', 'corp', 'non_corp']
	save_rates(total_discount_rates)
	return total_discount_rates

def calc_corp(indust_debt):
	#uses all the financial parameters to calculate the real discount rate
	inflation_rate = 0.011 #inflation rate in the United States over the past year
	real_rate_return = 0.006 #interest rate for savings
	debt_ratio = np.array(indust_debt['corp']) #share of investment financed by debt
	#debt_ratio = np.nan_to_num(debt_ratio)
	equity_ratio = 1 - debt_ratio #share of investment financed by equity
	nominal_mrkt_intrst = 0.0365 #interest rate paid on a 30 year fixed loan
	corp_tax_rate = 0.391 #statutory corporate tax rate in the United States

	real_discount_rates = debt_ratio * (nominal_mrkt_intrst * (1 - corp_tax_rate) - inflation_rate) + equity_ratio * (real_rate_return)

	return real_discount_rates

def calc_non_corp(indust_debt):
	inflation_rate = 0.011 #inflation rate in the United States over the past year
	equity_return = 0.5 #return paid on equity
	debt_ratio = np.array(indust_debt['non_corp']) #share of investment financed by debt
	#debt_ratio = np.nan_to_num(debt_ratio)
	equity_ratio = 1 - debt_ratio #share of investment financed by equity
	nominal_mrkt_intrst = 0.0365 #interest rate paid on a 30 year fixed loan
	non_corp_tax_rate = 0.5

	real_discount_rates = debt_ratio * (nominal_mrkt_intrst * (1 - non_corp_tax_rate) - inflation_rate) + equity_ratio * (equity_return)

	return real_discount_rates

#def calc_ooh(indust_debt)

def save_rates(disc_rates):
	disc_rates = disc_rates[(disc_rates.NAICS=='11')|(disc_rates.NAICS=='211')|(disc_rates.NAICS=='212')|(disc_rates.NAICS=='213') 
    |(disc_rates.NAICS=='22')|(disc_rates.NAICS=='23')|(disc_rates.NAICS=='31-33')|(disc_rates.NAICS=='32411')|(disc_rates.NAICS == '336')
    |(disc_rates.NAICS=='3391')|(disc_rates.NAICS=='42')|(disc_rates.NAICS=='44-45')|(disc_rates.NAICS=='48-49')|(disc_rates.NAICS == '51')
    |(disc_rates.NAICS=='52')|(disc_rates.NAICS=='531')|(disc_rates.NAICS=='532')|(disc_rates.NAICS=='533')|(disc_rates.NAICS=='54')
    |(disc_rates.NAICS=='55')|(disc_rates.NAICS=='56')|(disc_rates.NAICS=='61')|(disc_rates.NAICS=='62')|(disc_rates.NAICS=='71')
    |(disc_rates.NAICS=='72')|(disc_rates.NAICS=='81')|(disc_rates.NAICS=='92')]
	
	disc_rates.to_csv(os.path.join(_OUT_DIR,'discount_rates.csv'), index = False)
