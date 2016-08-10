
import os.path
import sys
import numpy as np
import pandas as pd
from btax.util import get_paths
globals().update(get_paths())
_OOH_VALUE = os.path.join(_DATA_DIR, 'b101.csv')
_DEBT_NFCORP = os.path.join(_DATA_DIR, 'l103.csv')
_DEBT_NCORP = os.path.join(_DATA_DIR, 'l104.csv')
_DEBT_FCORP = os.path.join(_DATA_DIR, 'l208.csv')
_DEBT_HOME = os.path.join(_DATA_DIR, 'l218.csv')
_EQUITY_CORP = os.path.join(_DATA_DIR, 'l223.csv')
_EQUITY_NCORP = os.path.join(_DATA_DIR, 'l229.csv')
_NAICS_CODES = os.path.join(_DATA_DIR, 'NAICS_Codes.csv')
_CST_FACTOR = 10**6

def calibrate_financing():
	skipped = [29,22,14,8,7,9,10]
	columns = [0,11]
	column_name = ['Type', 'Amount']
	num_rows = [1,4]
	#reads the equity data from the .csv file. Specifies which columns and rows to read in the file
	corp_equity_df = pd.read_csv(_EQUITY_CORP, skiprows=skipped[5],
		usecols=columns, header=None, names=column_name, nrows=num_rows[1])

	non_fin_corp_equity = corp_equity_df[corp_equity_df.index==0]['Amount'][0] * _CST_FACTOR
	#apportions the equity based on the ratio of equity held by each industry
	equity_values = apportion_equity({'non_fin_corp_equity':non_fin_corp_equity})
	non_fin_corp_debt = pd.read_csv(_DEBT_NFCORP, skiprows=skipped[0], usecols=columns,
		header=None, names=column_name, nrows=num_rows[0])['Amount'][0] * _CST_FACTOR
	#apportions the debt based on the ratio of interest paid by each industry
	debt_values = apportion_debt({'non_fin_corp_debt': non_fin_corp_debt})

	fin_corp_equity = corp_equity_df[corp_equity_df.index==3]['Amount'][3] * _CST_FACTOR
	equity_values.update(apportion_equity({'fin_corp_equity':fin_corp_equity}))
	fin_corp_debt = pd.read_csv(_DEBT_FCORP, skiprows=skipped[2], usecols=columns,
		header=None, names=column_name, nrows=num_rows[0])['Amount'][0] * _CST_FACTOR
	debt_values.update(apportion_debt({'fin_corp_debt':fin_corp_debt}))

	non_corp_equity = pd.read_csv(_EQUITY_NCORP, skiprows=skipped[4], usecols=columns,
		header=None, names=column_name, nrows=num_rows[0])['Amount'][0] * _CST_FACTOR
	equity_values.update(apportion_equity({'non_corp_equity':non_corp_equity}))
	non_corp_debt = pd.read_csv(_DEBT_NCORP, skiprows=skipped[1], usecols=columns,
		header=None, names=column_name, nrows=num_rows[0])['Amount'][0] * _CST_FACTOR
	debt_values.update(apportion_debt({'non_corp_debt':non_corp_debt}))

	#calculates the overall debt ratios based on the equity and debt values, stored in dictionaries {key:dataframe}
	debt_params = calc_debt(equity_values, debt_values)
	return debt_params

	mortg_debt = pd.read_csv(_DEBT_HOME, skiprows=skipped[3], usecols=columns,
		header=None, names=column_name, nrows=num_rows[0])['Amount'][0] * _CST_FACTOR
	house_value = pd.read_csv(_OOH_VALUE, skiprows=skipped[6], usecols=columns,
		header=None, names=column_name, nrows=num_rows[0])['Amount'][0] * _CST_FACTOR

def apportion_debt(total_liab):
	#use the ratio of total liabilities in an industry to total interest paid by all industries to proportionally distribute debt
	keyword = total_liab.keys()[0]
	#choose interest paid for either corporate or non-corporate businesses
	if((keyword=='non_fin_corp_debt') or (keyword=='fin_corp_debt')):
		columns = [11]
		intrst_pd_1 = pd.read_csv(_SOI_S_VALUES, usecols=columns)
		intrst_pd_2 = pd.read_csv(_SOI_C_VALUES, usecols=columns)
		types = ['c_corp', 's_corp']
		intrst_pd = {'c_corp':intrst_pd_1, 's_corp':intrst_pd_2}
	else:
		columns = [2]
		intrst_pd_1 = pd.read_csv(_SOI_PA_VALUES, usecols=columns)
		intrst_pd_2 = pd.read_csv(_SOI_PR_VALUES, usecols=columns)
		types = ['partner', 'prop']
		intrst_pd = {'partner':intrst_pd_1, 'prop':intrst_pd_2}

	#runs the debt calculation twice for s-corps and c-corps or partnerships and sole proprietorships
	debt_df = pd.DataFrame(index=np.arange(0,len(intrst_pd_1)), columns=types)
	for i in types:
		total_intrst = intrst_pd[i].sum(axis=0)['interest_paid']
		ratio = total_liab[keyword] / total_intrst
		indust_debt = np.array(intrst_pd[i]['interest_paid']) * ratio
		debt_df[i] = indust_debt

	return {keyword:debt_df}

def apportion_equity(total_equity):
	keyword = total_equity.keys()[0]
	if((keyword=='non_fin_corp_equity') or (keyword=='fin_corp_equity')):
		columns = [1,3,4,6,8]
		equity_x_1 = pd.read_csv(_SOI_S_VALUES, usecols=columns)
		equity_x_2 = pd.read_csv(_SOI_C_VALUES, usecols=columns)
		types = ['c_corp', 's_corp']
		equity = {'c_corp':equity_x_1, 's_corp':equity_x_2}

		equity_df = pd.DataFrame(index=np.arange(0,len(equity_x_1)),columns=['c_corp', 's_corp'])
		for i in types:
			equity[i]['cost_of_treasury_stock'] = equity[i]['cost_of_treasury_stock'] * -1
			sum_equity = sum(equity[i].sum(axis=0))
			equity_rows = equity[i].sum(axis=1)
			ratio = total_equity[keyword] / sum_equity
			indust_equity = np.array(equity_rows) * ratio
			equity_df[i] = indust_equity

		return {keyword:equity_df}

	else:
		columns = [7]
		equity_pca = pd.read_csv(_SOI_AS_VALUES, usecols=columns)
		equity_df = pd.DataFrame(index=np.arange(0,len(equity_pca)),columns=['non_corp'])
		sum_equity = equity_pca.sum(axis=0)['capital_accounts_net']
		ratio = total_equity[keyword] / sum_equity
		indust_equity = np.array(equity_pca) * ratio
		equity_df['non_corp'] = indust_equity

	return {keyword:equity_df}

def calc_debt(total_equity, total_liab):
	#calculates the debt ratio for each industry and then uses it to calculate the real discount rate
	c_corp_equity = total_equity['non_fin_corp_equity']['c_corp']
	s_corp_equity = total_equity['non_fin_corp_equity']['s_corp']
	c_corp_debt = total_liab['non_fin_corp_debt']['c_corp']
	s_corp_debt = total_liab['non_fin_corp_debt']['s_corp']

	non_corp_debt = total_liab['non_corp_debt'].sum(axis=1) + s_corp_debt
	non_corp_equity = total_equity['non_corp_equity'].sum(axis=1) + s_corp_equity

	#calculates the debt ratio for all corporate and non-corporate industries
	debt_f_corp = (c_corp_debt) / (c_corp_equity + c_corp_debt)
	debt_f_non_corp = (non_corp_debt) / (non_corp_equity + non_corp_debt)

	#prints out the debt ratios as an intermediate step
	total_debt_f = pd.concat([pd.read_csv(_NAICS_CODES),debt_f_corp, debt_f_non_corp], axis=1)
	total_debt_f.columns = ['NAICS', 'corp', 'non_corp']
	save_ratios(total_debt_f)

	return total_debt_f


def calc_after_return(indust_debt):
	#calculates the real after-tax return paid by a corporation
	inflation_rate = 0.011
	nominal_mrkt_intrst = 0.0365
	real_rate_return = 0.006
	debt_ratio = np.array(indust_debt)
	#debt_ratio = np.nan_to_num(debt_ratio)
	equity_ratio = 1 - debt_ratio

	after_tax_return = debt_ratio * (nominal_mrkt_intrst - inflation_rate) + equity_ratio * real_rate_return

def save_ratios(debt_ratios):
	debt_ratios = debt_ratios[(debt_ratios.NAICS=='11')|(debt_ratios.NAICS=='211')|(debt_ratios.NAICS=='212')|(debt_ratios.NAICS=='213')
	|(debt_ratios.NAICS=='22')|(debt_ratios.NAICS=='23')|(debt_ratios.NAICS=='31-33')|(debt_ratios.NAICS=='32411')|(debt_ratios.NAICS == '336')
	|(debt_ratios.NAICS=='3391')|(debt_ratios.NAICS=='42')|(debt_ratios.NAICS=='44-45')|(debt_ratios.NAICS=='48-49')|(debt_ratios.NAICS == '51')
	|(debt_ratios.NAICS=='52')|(debt_ratios.NAICS=='531')|(debt_ratios.NAICS=='532')|(debt_ratios.NAICS=='533')|(debt_ratios.NAICS=='54')
	|(debt_ratios.NAICS=='55')|(debt_ratios.NAICS=='56')|(debt_ratios.NAICS=='61')|(debt_ratios.NAICS=='62')|(debt_ratios.NAICS=='71')
	|(debt_ratios.NAICS=='72')|(debt_ratios.NAICS=='81')|(debt_ratios.NAICS=='92')]
	debt_ratios.to_csv(os.path.join(_OUT_DIR,'debt.csv'), index = False)
