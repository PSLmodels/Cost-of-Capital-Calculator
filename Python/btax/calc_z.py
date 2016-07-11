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

def calc_tax_depr_rates(r, bonus_deprec, tax_methods):
    #
    tax_treat_list = ['Corporate','Non-Corporate']
    fin_list = ['Typical','Debt','Equity']
    
    tax_data = get_z(_TAX_DEPR_IN_PATH, r, bonus_deprec, tax_treat_list, fin_list, tax_methods)
    return tax_data


def get_z(file_path, r, bonus_deprec, tax_treat_list, fin_list, tax_methods):
    tax_deprec = pd.read_csv(file_path)
    z = npv_tax_deprec(tax_deprec, r, bonus_deprec, tax_methods)

    return z

def npv_tax_deprec(df, r, bonus_deprec, tax_methods):
    df['b'] = df['Method']
    df['b'].replace(tax_methods,inplace=True)
    bools = np.array(((df['Method']=='GDS 200%')|(df['Method']=='GDS 150%')))
    bools = np.tile(np.reshape(bools,(bools.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
    z = np.where(bools, dbsl(df['GDS'],df['b'],r, bonus_deprec), 
        sl(df['ADS'],r, bonus_deprec))

    return z

def dbsl(Y, b, r, bonus_deprec):
    if bonus_deprec > 0.:
        Y = np.tile(np.reshape(Y,(Y.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
        b = np.tile(np.reshape(b,(b.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
        beta = b/Y
        Y_star = (Y-1)*(1-(1/b))
        z_1 = (((beta/(beta+r))*(1-np.exp(-1*(beta+r)*Y_star))) + 
            ((np.exp(-1*beta*Y_star)/(((Y-1)-Y_star)*r))*(np.exp(-1*r*Y_star)-np.exp(-1*r*(Y-1)))))
        deprec1 = bonus_deprec + beta
        z = deprec1 + (z_1/(1+r))
    else:
        Y = np.tile(np.reshape(Y,(Y.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
        b = np.tile(np.reshape(b,(b.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
        beta = b/Y
        Y_star = Y*(1-(1/b))
        z = (((beta/(beta+r))*(1-np.exp(-1*(beta+r)*Y_star))) + 
            ((np.exp(-1*beta*Y_star)/((Y-Y_star)*r))*(np.exp(-1*r*Y_star)-np.exp(-1*r*Y))))

    return z

def sl(Y, r, bonus_deprec):
    if bonus_deprec > 0.:
        Y = np.tile(np.reshape(Y,(Y.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
        z_1 = np.exp(-1*r*(Y-1)/(r*(Y-1)))
        deprec1 = bonus_deprec + (1/Y)
        z =  deprec1 + (z_1/(1+r))
    else:
        Y = np.tile(np.reshape(Y,(Y.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
        z = np.exp(-1*r*Y)/(r*Y)

    return z