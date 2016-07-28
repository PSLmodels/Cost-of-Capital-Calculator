'''
Calculate Depreciation Rates (calc_z.py):
-------------------------------------------------------------------------------

This module provides functions for calculating the tax depreciation allowance. It also provides a function
that will return the economic depreciation rate (no calculation needed). The net present value of tax depreciation
allowances are calculated for both the declining balance and straight line methods of depreciation. Last Updated 7/27/2016
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
_TAX_DEPR = os.path.join(_DEPR_DIR, 'BEA_IRS_Crosswalk.csv')
_NAICS_CODE_PATH = os.path.join(_DATA_DIR, 'NAICS_Codes.csv')
_NAICS_PATH = os.path.join(_BEA_DIR, 'NAICS_SOI_crosswalk.csv')

def get_econ_depr():
    """Reads in the list of assets and their economic depreciation values

        :returns: A list of asset types and economic depreciation values
        :rtype: array
    """ 
    depr_econ = pd.read_csv(_ECON_DEPR_IN_PATH)
    depr_econ = depr_econ.fillna(0)
    return np.array(depr_econ['Economic Depreciation Rate'])

def calc_tax_depr_rates(r, bonus_deprec, tax_methods):
    """Loads in the data for depreciation schedules and depreciation method. Calls the calculation function.

        :param r: Discount rate
        :param bonus_deprec: Reform for bonus depreciation
        :param tax_methods: Rates of depreciation
        :type r: 3x2 array
        :type bonus_deprec: int, float
        :type tax_methods: dictionary
        :returns: The net present value of depreciation allowances
        :rtype: 96x3x2 array
    """
    tax_deprec = pd.read_csv(_TAX_DEPR)
    z = npv_tax_deprec(tax_deprec, r, bonus_deprec, tax_methods)
    return z

def npv_tax_deprec(df, r, bonus_deprec, tax_methods):
    """Depending on the method of depreciation, makes calls to either the straight line or declining balance calcs

        :param tax_deprec: Contains the service lives and method of depreciation.
        :param r: Discount rate
        :param bonus_deprec: Reform for bonus depreciation
        :param tax_methods: Rates of depreciation
        :type tax_deprec: DataFrame
        :type r: 3x2 array
        :type bonus_deprec: int, float
        :type tax_methods: dictionary
        :returns: The net present value of depreciation allowances
        :rtype: 96x3x2 array
    """
    df['b'] = df['Method']
    df['b'].replace(tax_methods,inplace=True)
    # Creates a boolean array for the appearance of the declining balance method
    bools = np.array(((df['Method']=='GDS 200%')|(df['Method']=='GDS 150%')))
    bools = np.tile(np.reshape(bools,(bools.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
    # The boolean array is used to determine which calculation function to call
    z = np.where(bools, dbsl(df['GDS'],df['b'],r, bonus_deprec), 
        sl(df['ADS'],r, bonus_deprec))

    return z

def dbsl(Y, b, r, bonus_deprec):
    """Makes the calculation for the declining balance method of depreciation.

        :param Y: Service life
        :param b: Rate of depreciation
        :param r: Discount rate
        :param bonus_deprec: Reform for bonus depreciation
        :type Y: int, float
        :type b: int, float
        :type r: 3x2 array
        :type bonus_deprec: int, float
        :returns: The net present value of declining balance depreciation allowances
        :rtype: 96x3x2 array

    """
    if bonus_deprec > 0.:
        Y = np.tile(np.reshape(Y,(Y.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
        b = np.tile(np.reshape(b,(b.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
        beta = b/Y
        # Point at which the depreciation switches to straight line
        Y_star = (Y-1)*(1-(1/b))
        # Main calculation for the net present value of tax depreciation allowances
        z_1 = (((beta/(beta+r))*(1-np.exp(-1*(beta+r)*Y_star))) + 
            ((np.exp(-1*beta*Y_star)/(((Y-1)-Y_star)*r))*(np.exp(-1*r*Y_star)-np.exp(-1*r*(Y-1)))))
        # Addition of bonus depreciation
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
    """Makes the calculation for the declining balance method of depreciation.

        :param Y: Service life
        :param r: Discount rate
        :param bonus_deprec: Reform for bonus depreciation
        :type Y: int, float
        :type r: 3x2 array
        :type bonus_deprec: int, float
        :returns: The net present value of straight line depreciation allowances
        :rtype: 96x3x2 array

    """
    if bonus_deprec > 0.:
        Y = np.tile(np.reshape(Y,(Y.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
        z_1 = np.exp(-1*r*(Y-1)/(r*(Y-1)))
        deprec1 = bonus_deprec + (1/Y)
        z =  deprec1 + (z_1/(1+r))
    else:
        Y = np.tile(np.reshape(Y,(Y.shape[0],1,1)),(1,r.shape[0],r.shape[1]))
        z = np.exp(-1*r*Y)/(r*Y)

    return z
