'''
Calculate Depreciation Rates (calc_rates):
-------------------------------------------------------------------------------
Last updated: 4/29/2016.

This module provides functions for calculating economic and tax depreciation
rates. All of the data is processed into NAICS trees by other modules, and
taken in as input of these functions. 
'''
# Packages:
import os.path
import sys
import numpy as np
import pandas as pd
# Directories:
_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
_MAIN_DIR = os.path.dirname(_CUR_DIR)
_DATA_DIR = os.path.join(_CUR_DIR, 'data')
_DEPR_DIR = os.path.join(_DATA_DIR, 'depreciation_rates')
_RAW_DIR = os.path.join(_DATA_DIR, 'raw_data')
_BEA_DIR = os.path.join(_RAW_DIR, 'BEA')
sys.path.append(_DATA_DIR)
# Importing custom modules:
import naics_processing as naics
import constants as cst
import parameters as params
# Full file paths:
_ECON_DEPR_IN_PATH = os.path.join(_DEPR_DIR, 'Economic Depreciation Rates.csv')
_TAX_DEPR_IN_PATH = os.path.join(_DEPR_DIR, 'BEA_IRS_Crosswalk.csv')
_NAICS_CODE_PATH = os.path.join(_DATA_DIR, 'NAICS_Codes.csv')
_NAICS_PATH = os.path.join(_BEA_DIR, 'NAICS_SOI_crosswalk.csv')
def get_econ_depr():
    depr_econ = pd.read_csv(_ECON_DEPR_IN_PATH)
    depr_econ = depr_econ.fillna(0)
    return np.array(depr_econ['Economic Depreciation Rate'])

def calc_depr_rates(fixed_assets):

    #opens the file containing depreciation rates by asset type:
    depr_econ = pd.read_csv(_ECON_DEPR_IN_PATH)
    depr_econ = depr_econ.fillna(0)
    #stores the economic depreciation rates in a 1xN matrix
    econ_rates = np.array(depr_econ['Economic Depreciation Rate'])
    #retrieves the naics code
    naics_codes = pd.read_csv(_NAICS_PATH)['2007 NAICS Codes'].tolist()[1:]
    naics_list = pd.read_csv(_NAICS_PATH)['2007 NAICS Codes'].tolist()[1:]
    #creates a dataframe that is returned at the end of the function with a list of all corp and non-corp industry averages
    econ_depr = pd.DataFrame(index = np.arange(0,len(fixed_assets)), columns = ('NAICS', 'corp', 'non_corp'))
    types = ['corp', 'non_corp']
    #Runs for the corporate assets and for non-corporate assets 
    k = 0     
    for j in xrange(0, len(naics_codes)):
        naics_code = naics_codes[j]
        if(fixed_assets.has_key(naics_code)):
            total_assets = fixed_assets[naics_code]
            for i in types:
                assets = total_assets[i]
                tot_depr = assets * econ_rates
                avg_depr = np.sum(tot_depr) / np.sum(assets)
                econ_depr[i][k] = avg_depr
            k += 1
        else:
            naics_list.remove(naics_code)

    econ_depr = econ_depr.fillna(0)
    econ_depr['NAICS'] = naics_list
    return econ_depr

def calc_tax_depr_rates(discount, tax_methods):
    #
    tax_treat_list = ['Corporate','Non-Corporate']
    fin_list = ['Typical','Debt','Equity']
    
    tax_data = get_z(_TAX_DEPR_IN_PATH, discount, tax_treat_list, fin_list, tax_methods)
    return tax_data


def get_z(file_path,r,tax_treat_list,fin_list, tax_methods):
    tax_deprec = pd.read_csv(file_path)
    z = npv_tax_deprec(tax_deprec,r, tax_methods)

    return z

def npv_tax_deprec(df,r,tax_methods):
    df['b'] = df['Method']
    df['b'].replace(tax_methods,inplace=True)
    bools = np.array(((df['Method']=='GDS 200%')|(df['Method']=='GDS 150%')))
    bools = np.tile(np.reshape(bools,(bools.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
    z = np.where(bools, dbsl(df['GDS'],df['b'],r), 
        sl(df['ADS'],r))

    return z

def dbsl(Y,b,r):
    Y = np.tile(np.reshape(Y,(Y.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
    b = np.tile(np.reshape(b,(b.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
    beta = b/Y
    Y_star = Y*(1-(1/b))
    z = (((beta/(beta+r))*(1-np.exp(-1*(beta+r)*Y_star))) + 
        ((np.exp(-1*beta*Y_star)/((Y-Y_star)*r))*(np.exp(-1*r*Y_star)-np.exp(-1*r*Y))))

    return z

def sl(Y,r):
    Y = np.tile(np.reshape(Y,(Y.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
    z = np.exp(-1*r*Y)/(r*Y)

    return z