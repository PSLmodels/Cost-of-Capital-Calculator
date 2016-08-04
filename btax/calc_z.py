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

# Importing custom modules:
import parameters as params
from util import get_paths

# Directories:
globals().update(get_paths())




def get_econ_depr():
    """Reads in the list of assets and their economic depreciation values

        :returns: A list of asset types and economic depreciation values
        :rtype: array
    """
    econ_deprec_rates = pd.read_csv(_ECON_DEPR_IN_PATH)
    econ_deprec_rates = econ_deprec_rates.fillna(0)
    econ_deprec_rates.rename(columns={"Code": "bea_asset_code",
                        "Economic Depreciation Rate": "delta"},inplace=True)
    return econ_deprec_rates

def calc_tax_depr_rates(r, bonus_deprec, tax_methods, financing_list, entity_list):
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
    tax_deprec_rates = pd.read_csv(_TAX_DEPR)
    z = npv_tax_deprec(tax_deprec_rates, r, bonus_deprec, tax_methods, financing_list, entity_list)
    return z

def npv_tax_deprec(df, r, bonus_deprec, tax_methods, financing_list, entity_list):
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

    df_gds = dbsl(df.loc[df['System']=='GDS'], r, bonus_deprec, financing_list, entity_list)
    df_ads = sl(df.loc[df['System']=='ADS'], r, bonus_deprec, financing_list, entity_list)

    # append gds and ads results
    df_all = df_gds.append(df_ads, ignore_index=True)

    return df_all

def dbsl(df, r, bonus_deprec, financing_list, entity_list):
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
        df['Y'] = df['GDS']
        df['beta'] = df['Y']/df['b']
        df['Y_star'] = (df['GDS']-1)*(1-(1/df['b']))
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                df['z1'+entity_list[j]+financing_list[i]] = \
                    (((df['beta']/(df['beta']+r[i,j]))*(1-np.exp(-1*(df['beta']
                        +r[i,j])*df['Y_star']))) +
                    ((np.exp(-1*df['beta']*df['Y_star'])/(((df['Y']-1)-
                    df['Y_star'])*r[i,j]))*(np.exp(-1*r[i,j]*df['Y_star'])-
                                            np.exp(-1*r[i,j]*(df['Y']-1)))))
                df['z'+entity_list[j]+financing_list[i]] = \
                    np.max(bonus_deprec+df['beta'] + ((1-bonus_deprec+df['beta'])*
                   (df['z1'+entity_list[j]+financing_list[i]]/(1+r[i,j]))),1.0)
        df.drop(['z1', 'beta', 'Y', 'Y_star'], axis=1, inplace=True)
    else:
        df['Y'] = df['GDS']
        df['beta'] = df['Y']/df['b']
        df['Y_star'] = (df['GDS']-1)*(1-(1/df['b']))
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                df['z'+entity_list[j]+financing_list[i]] = \
                    (((df['beta']/(df['beta']+r[i,j]))*(1-np.exp(-1*(df['beta']+r[i,j])*
                            df['Y_star']))) +
                        ((np.exp(-1*df['beta']*df['Y_star'])/((df['Y']-df['Y_star'])
                            *r[i,j]))*(np.exp(-1*r[i,j]*df['Y_star'])-np.exp(-1*r[i,j]*df['Y']))))

        df.drop(['beta', 'Y', 'Y_star'], axis=1, inplace=True)

    return df

def sl(df, r, bonus_deprec, financing_list, entity_list):
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
        df['Y'] = df['ADS']
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                df['z1'+entity_list[j]+financing_list[i]] = \
                    np.exp(-1*r[i,j]*(df['Y']-1)/(r[i,j]*(df['Y']-1)))
                df['z'+entity_list[j]+financing_list[i]] = \
                    np.max(bonus_deprec+(1./df['Y']) + ((1-bonus_deprec+(1./df['Y']))*
                   (df['z1'+entity_list[j]+financing_list[i]]/(1+r[i,j]))),1.0)
        df.drop(['z1', 'Y'], axis=1, inplace=True)
    else:
        df['Y'] = df['ADS']
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                df['z'+entity_list[j]+financing_list[i]] = \
                    np.exp(-1*r[i,j]*df['Y'])/(r[i,j]*df['Y'])
        df.drop('Y', axis=1, inplace=True)

    return df
