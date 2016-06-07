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
sys.path.append(_DATA_DIR)
# Importing custom modules:
import naics_processing as naics
import constants as cst
# Full file paths:
_ECON_DEPR_IN_PATH = os.path.join(_DEPR_DIR, 'Economic Depreciation Rates.csv')
_TAX_DEPR_IN_PATH = os.path.join(_DEPR_DIR, 'BEA_IRS_Crosswalk.csv')
_NAICS_CODE_PATH = os.path.join(_DATA_DIR, 'NAICS_Codes.csv')

def calc_depr_rates(asset_tree, inv_tree, land_tree):
    #opens the file containing depreciation rates by asset type:
    depr_econ = pd.read_csv(_ECON_DEPR_IN_PATH)
    depr_econ = depr_econ.fillna(0)
    #stores the economic depreciation rates in a 1xN matrix
    econ_rates = np.array(depr_econ['Economic Depreciation Rate'])
    #creates a dataframe that is returned at the end of the function with a list of all corp and non-corp industry averages
    econ_depr = pd.DataFrame(index = np.arange(0,len(asset_tree.enum_inds)), columns = ('NAICS', 'All', 'Corp', 'Non-Corp'))
    #retrieves the naics code
    naics_codes = pd.read_csv(_NAICS_CODE_PATH)
    #sets the first column of the dataframe with the naics values
    econ_depr['NAICS'] = naics_codes
    types = ['All','Corp', 'Non-Corp']
    #Runs for the corporate assets and for non-corporate assets
    for i in types:        
        depr_list = []
        #Iterates over every industry in the tree     
        for j in xrange(0, len(asset_tree.enum_inds)):
            #retrieves the fixed asset values for each industry
            asset_row = asset_tree.enum_inds[j].data.dfs[i].values[0]
            #calculates the depreciation for each asset in that industry
            depr_row = np.multiply(asset_row, econ_rates)
            #takes the weighted average of depreciation
            if(np.sum(asset_row) != 0):
                avg_depr = np.sum(depr_row) / np.sum(asset_row)
            else:
                avg_depr = 0
            #stores the weighted average in a list
            depr_list.append(avg_depr)
        #stores the depreciation list in the dataframe 
        econ_depr[i] = depr_list

    return econ_depr

def calc_tax_depr_rates(asset_tree, inv_tree, land_tree):
    #
    tax_data = pd.read_csv(_TAX_DEPR_IN_PATH).fillna(0)
    tax_assets = tax_data['Asset Type']
    # Real Interest Rate:
    r = .05  
    tax_mthds = {'GDS 200%': 2.0, 'GDS 150%': 1.5, 'GDS SL': 1.0, 'ADS SL': 1.0}
    tax_rates = np.zeros(len(tax_assets))

    # Compute the tax depreciation rates:
    for i in xrange(0, len(tax_assets)):
        tax_method = tax_data['Method'][i]
        tax_system = tax_data['System'][i]
        tax_life = tax_data[tax_system][i]
        tax_b = tax_mthds[tax_method]
        tax_beta = tax_b / tax_life
        if(tax_method == 'GDS 200%' or tax_method == 'GDS 150%'):
            tax_star = tax_life * (1 - (1/tax_b))
            tax_z = (((tax_beta/(tax_beta+r))* (1-np.exp(-1*(tax_beta+r)*tax_star))) 
                      + ((np.exp(-1*tax_beta*tax_star)/((tax_life-tax_star)*r))* (np.exp(-1*r*tax_star)-np.exp(-1*r*tax_life))))
            tax_rates[i] = r/((1/tax_z)-1)
        else:
            tax_z = ((1-np.exp(-1*r*tax_life)) / (r*tax_life))
            tax_rates[i] = (tax_z * r) / (1 + r - tax_z)
    #
    tax_depr = pd.DataFrame(index = np.arange(0,len(asset_tree.enum_inds)), columns = ('NAICS', 'All', 'Corp', 'Non-Corp'))
    #retrieves the naics code
    naics_codes = pd.read_csv(_NAICS_CODE_PATH)
    #sets the first column of the dataframe with the naics values
    tax_depr['NAICS'] = naics_codes
    types = ['All', 'Corp', 'Non-Corp']
    for i in types:        
        #Iterates over every industry in the tree
        depr_list = []       
        for j in xrange(0, len(asset_tree.enum_inds)):
            #retrieves the fixed asset values for each industry
            asset_row = asset_tree.enum_inds[j].data.dfs[i].values[0]
            #calculates the depreciation for each asset in that industry
            depr_row = np.multiply(asset_row, tax_rates)
            #takes the weighted average of depreciation
            if(np.sum(asset_row) != 0):
                avg_depr = np.sum(depr_row) / np.sum(asset_row)
            else:
                avg_depr = 0
            #stores the weighted average in a list
            depr_list.append(avg_depr)
        tax_depr[i] = depr_list    
                    
    return tax_depr
