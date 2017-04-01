'''
Calculate Depreciation Rates (calc_z.py):
-------------------------------------------------------------------------------

This module provides functions for calculating the tax depreciation allowance.
It also provides a function that will return the economic depreciation
rate (no calculation needed). The net present value of tax depreciation
allowances are calculated for both the declining balance and straight
line methods of depreciation. Last Updated 7/27/2016
'''
# Packages:
import os.path
import sys
import numpy as np
import pandas as pd

# Importing custom modules:
from btax import parameters as params
from btax.util import get_paths, str_modified

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
                                      "Economic Depreciation Rate": "delta"},
                             inplace=True)
    econ_deprec_rates['Asset'] = econ_deprec_rates['Asset'].str.strip()
    bea = econ_deprec_rates['bea_asset_code']
    econ_deprec_rates['bea_asset_code'] = bea.str.strip()

    return econ_deprec_rates

def calc_tax_depr_rates(r, pi, delta, bonus_deprec, deprec_system,
                        expense_inventory, expense_land, tax_methods,
                        financing_list, entity_list):
    """Loads in the data for depreciation schedules and depreciation method.
       Calls the calculation function.

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
    tax_deprec_rates['Asset Type'] = tax_deprec_rates['Asset Type'].str.strip()

    # update tax_deprec_rates based on user defined parameters
    gds = tax_deprec_rates['GDS Life']
    tax_deprec_rates['System'] = gds.apply(str_modified)
    tax_deprec_rates['System'].replace(deprec_system, inplace=True)
    tax_deprec_rates.loc[tax_deprec_rates['System']=='ADS','Method'] = 'SL'
    econ = tax_deprec_rates['System']=='Economic'
    tax_deprec_rates.loc[econ, 'Method'] = 'Economic'

    # add bonus depreciation to tax deprec parameters dataframe
    gds = tax_deprec_rates['GDS Class Life']
    tax_deprec_rates['bonus'] = gds.apply(str_modified)
    tax_deprec_rates['bonus'].replace(bonus_deprec,inplace=True)

    # merge in econ depreciation rates
    tax_deprec_rates = pd.merge(tax_deprec_rates, delta,
                                how='left', left_on=['Asset Type'],
                                right_on=['Asset'], left_index=False,
                                right_index=False, sort=False, copy=True)

    z = npv_tax_deprec(tax_deprec_rates, r, pi, tax_methods,
                       financing_list, entity_list)

    # replace tax depreciation rates on land and
    # inventories w/ zero - unless expense
    if expense_inventory:
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                zi = 'z' + entity_list[j] + financing_list[i]
                z.loc[z['Asset Type'] == 'Inventories', zi] = 1.
    else:
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                zi = 'z' + entity_list[j] + financing_list[i]
                z.loc[z['Asset Type'] == 'Inventories', zi] = 0.
    if expense_land:
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                zi = 'z' + entity_list[j] + financing_list[i]
                z.loc[z['Asset Type'] == 'Land', zi] = 1.
    else:
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                zi = 'z' + entity_list[j] + financing_list[i]
                z.loc[z['Asset Type'] == 'Land', zi] = 0.

    return z

def npv_tax_deprec(df, r, pi, tax_methods, financing_list, entity_list):
    """Depending on the method of depreciation, makes calls to either the
       straight line or declining balance calcs

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
    db200 = df['Method'] == 'DB 200%'
    db150 = df['Method'] == 'DB 150%'
    df_dbsl = dbsl(df.loc[db200 | db150].copy(),
                   r, financing_list, entity_list)
    df_sl = sl(df.loc[df['Method']=='SL'].copy(),
               r, financing_list, entity_list)
    econ_col = df.loc[df['Method'] == 'Economic'].copy()
    df_econ = econ(econ_col, r, pi, financing_list, entity_list)
    exp = df.loc[df['Method'] == 'Expensing'].copy()
    df_expense = expensing(exp, r, financing_list, entity_list)

    # append gds and ads results
    df_all = df_dbsl.append(df_sl.append(df_econ.append(df_expense,
                                                        ignore_index=True),
                                                        ignore_index=True),
                                                        ignore_index=True)

    return df_all

def dbsl(df, r, financing_list, entity_list):
    """Makes the calculation for the declining balance method of depreciation.

        :param Y: Service life
        :param b: Rate of depreciation
        :param r: Discount rate
        :param bonus_deprec: Reform for bonus depreciation
        :type Y: int, float
        :type b: int, float
        :type r: 3x2 array
        :type bonus_deprec: int, float
        :returns: The net present value of declining balance
                  depreciation allowances

    """
    df['Y'] = df['GDS Life']
    df['beta'] = df['b']/df['Y']
    df['Y_star'] = ((((df['Y']-1)*(1-(1/df['b'])))*(df['bonus']!=0.)) +
                    ((1-(df['bonus']!=0.))*(df['Y']*(1-(1/df['b'])))))

    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            df['z'+entity_list[j]+financing_list[i]] = \
                            df['bonus'] + ((1-df['bonus'])*(((df['beta']/\
                                (df['beta']+r[i,j]))*(1-np.exp(-1*\
                                    (df['beta']+r[i,j])*
                               df['Y_star']))) +
                           ((np.exp(-1*df['beta']*df['Y_star'])/\
                            ((df['Y']-df['Y_star'])
                               *r[i,j]))*(np.exp(-1*r[i,j]*df['Y_star'])-\
                           np.exp(-1*r[i,j]*df['Y'])))))

    df.drop(['beta', 'Y', 'Y_star'], axis=1, inplace=True)

    return df

def sl(df, r, financing_list, entity_list):
    """Makes the calculation for the straight line method of depreciation.

        :param Y: Service life
        :param r: Discount rate
        :param bonus_deprec: Reform for bonus depreciation
        :type Y: int, float
        :type r: 3x2 array
        :type bonus_deprec: int, float
        :returns: The net present value of straight line
                  depreciation allowances
        :rtype: 96x3x2 array

    """
    df['Y'] = df['ADS Life']
    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            df['z'+entity_list[j]+financing_list[i]] = \
                df['bonus'] + ((1-df['bonus'])*((1-np.exp(-1*r[i,j]*df['Y']))/\
                            (r[i,j]*df['Y'])))

    df.drop(['Y'], axis=1, inplace=True)

    return df

def expensing(df, r, financing_list, entity_list):
    """Makes the calculation for expensing.
        :param bonus_deprec: Reform for bonus depreciation
        :returns: The net present value of expensed investments
        :rtype: 96x3x2 array
    """
    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            df['z'+entity_list[j]+financing_list[i]] = 1.

    return df

def econ(df, r, pi, financing_list, entity_list):
    """Makes the calculation for economic depreciation.

        :param Y: Service life
        :param r: Discount rate
        :param bonus_deprec: Reform for bonus depreciation
        :type Y: int, float
        :type r: 3x2 array
        :type bonus_deprec: int, float
        :returns: The net present value of straight line depreciation allowances
        :rtype: 96x3x2 array

    """
    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            df['z'+entity_list[j]+financing_list[i]] = \
                df['bonus'] + ((1-df['bonus'])*(((df['delta'])/\
                               (df['delta']+r[i,j]-pi))))

    return df
