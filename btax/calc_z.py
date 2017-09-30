'''
Calculate Depreciation Rates (calc_z.py):
------------------------------------------------------------------------

This module provides functions for calculating the tax depreciation
allowance.  It also provides a function that will return the economic
depreciation rate (no calculation needed). The net present value of tax
depreciation allowances are calculated for both the declining balance
and straight line methods of depreciation.
'''
# Packages:
import numpy as np
import pandas as pd

# Importing custom modules:
from btax.util import get_paths, str_modified

# Directories:
globals().update(get_paths())


def get_econ_depr():
    """
    Reads in the list of assets and their economic depreciation values

    Args:
        None

    Returns:
        econ_deprec_rates: dataframe, economic depreciation rates for
                           all asset types

    """
    econ_deprec_rates = pd.read_csv(_ECON_DEPR_IN_PATH)
    econ_deprec_rates = econ_deprec_rates.fillna(0)
    econ_deprec_rates.rename(columns={"Code": "bea_asset_code",
                                      "Economic Depreciation Rate": "delta"},
                             inplace=True)
    econ_deprec_rates['Asset'] = econ_deprec_rates['Asset'].str.strip()
    econ_deprec_rates['bea_asset_code'] = econ_deprec_rates['bea_asset_code'].str.strip()

    return econ_deprec_rates


def calc_tax_depr_rates(r, pi, delta, bonus_deprec, deprec_system,
                        expense_inventory, expense_land, tax_methods,
                        financing_list, entity_list):
    """
    Loads in the data for depreciation schedules and depreciation method.
    Calls functions defined below to compute NPV of tax depreciation.

    Args:
        r: scalar, nominal interest rate
        pi: scalar, inflation rate
        delta: economic depreciation rate
        bonus_deprec: rate of bonus depreciation
        deprec_system: depreciation system used (e.g. ADS/GDS)
        expense_inventory: boolean, True if immediately expense
                           inventories
        expense_land: scalar, rate of expending on land
        tax_methods:
        financing_list: list, list of strings defining financing options
                        (e.g., typically financed, debt financed,
                        equity financed)
        entity_list = list, list of strings of different entity types

        Returns:
            z: dataframe, NPV of depreciation deductions for all asset
               types, all financing types, and all tax treatment types

    """
    tax_deprec_rates = pd.read_csv(_TAX_DEPR)
    tax_deprec_rates['Asset Type'] = tax_deprec_rates['Asset Type'].str.strip()

    # update tax_deprec_rates based on user defined parameters
    tax_deprec_rates['System'] = tax_deprec_rates['GDS Life'].apply(str_modified)
    tax_deprec_rates['System'].replace(deprec_system, inplace=True)
    tax_deprec_rates.loc[tax_deprec_rates['System'] == 'ADS', 'Method'] = 'SL'
    tax_deprec_rates.loc[tax_deprec_rates['System'] == 'Economic', 'Method'] = 'Economic'

    # add bonus depreciation to tax deprec parameters dataframe
    tax_deprec_rates['bonus'] = tax_deprec_rates['GDS Class Life'].apply(str_modified)
    tax_deprec_rates['bonus'].replace(bonus_deprec, inplace=True)

    # merge in econ depreciation rates
    tax_deprec_rates = pd.merge(tax_deprec_rates, delta, how='left',
                                left_on=['Asset Type'],
                                right_on=['Asset'], left_index=False,
                                right_index=False, sort=False, copy=True)

    z = npv_tax_deprec(tax_deprec_rates, r, pi, tax_methods,
                       financing_list, entity_list)

    # replace tax depreciation rates on land and inventories w/ zero - unless expense
    if expense_inventory:
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                z.loc[z['Asset Type'] == 'Inventories', 'z' + entity_list[j] + financing_list[i]] = 1.
    else:
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                z.loc[z['Asset Type'] == 'Inventories', 'z'+entity_list[j] + financing_list[i]] = 0.
    if expense_land:
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                z.loc[z['Asset Type'] == 'Land', 'z' + entity_list[j] + financing_list[i]] = 1.
    else:
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                z.loc[z['Asset Type'] == 'Land', 'z' + entity_list[j] + financing_list[i]] = 0.

    return z


def npv_tax_deprec(df, r, pi, tax_methods, financing_list, entity_list):
    """
    Depending on the method of depreciation, makes calls to either
    the straight line or declining balance calculations.

    Args:
        r: scalar, nominal interest rate
        pi: scalar, inflation rate
        tax_methods:
        financing_list: list, list of strings defining financing options
                        (e.g., typically financed, debt financed,
                        equity financed)
        entity_list = list, list of strings of different entity types

        Returns:
            df_all: dataframe, NPV of depreciation deductions for
                    all asset types, all financing types, and all
                    tax treatment types

    """

    df['b'] = df['Method']
    df['b'].replace(tax_methods, inplace=True)

    df_dbsl = dbsl(df.loc[(df['Method'] == 'DB 200%') | (df['Method'] ==
                                                         'DB 150%')].copy(),
                   r, financing_list, entity_list)
    df_sl = sl(df.loc[df['Method'] == 'SL'].copy(), r, financing_list,
               entity_list)
    df_econ = econ(df.loc[df['Method'] == 'Economic'].copy(), r, pi,
                   financing_list, entity_list)
    df_expense = expensing(df.loc[df['Method'] == 'Expensing'].copy(), r,
                           financing_list, entity_list)

    # append gds and ads results
    df_all = df_dbsl.append(df_sl.append(df_econ.append(df_expense,
                                                        ignore_index=True),
                                         ignore_index=True),
                            ignore_index=True)

    return df_all


def dbsl(df, r, financing_list, entity_list):
    """
    Makes the calculation for the declining balance with a switch to
    straight line (DBSL) method of depreciation.

    Args:
        df: dataframe, contains economic depreciation and tax
            depreciation schedules for all assets where DBSL depreciation
            will be applied.
        r: scalar, nominal interest rate
        financing_list: list, list of strings defining financing options
                        (e.g., typically financed, debt financed,
                        equity financed)
        entity_list = list, list of strings of different entity types

        Returns:
            df: dataframe, NPV of depreciation deductions for
                    all asset using DBSL depreciation, all financing types,
                    and all tax treatment types

    """

    df['Y'] = df['GDS Life']
    df['beta'] = df['b']/df['Y']
    df['Y_star'] = ((((df['Y'] - 1) * (1 - (1 / df['b']))) *
                     (df['bonus'] != 0.)) + ((1 - (df['bonus'] != 0.)) *
                                             (df['Y'] * (1 - (1 /
                                                              df['b'])))))

    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            df['z'+entity_list[j]+financing_list[i]] = \
                (df['bonus'] + ((1 - df['bonus']) *
                                (((df['beta'] / (df['beta'] +
                                                 r[i, j])) *
                                  (1 - np.exp(-1 * (df['beta'] + r[i, j])
                                              * df['Y_star']))) +
                                 ((np.exp(-1 * df['beta'] * df['Y_star'])
                                   / ((df['Y'] - df['Y_star']) * r[i, j]))
                                  * (np.exp(-1 * r[i, j] * df['Y_star'])
                                     - np.exp(-1 * r[i, j] * df['Y']))))))

    df.drop(['beta', 'Y', 'Y_star'], axis=1, inplace=True)

    return df


def sl(df, r, financing_list, entity_list):
    """
    Makes the calculation for straight line (SL) method of depreciation.

    Args:
        df: dataframe, contains economic depreciation and tax
            depreciation schedules for all assets where DBSL depreciation
            will be applied.
        r: scalar, nominal interest rate
        financing_list: list, list of strings defining financing options
                        (e.g., typically financed, debt financed,
                        equity financed)
        entity_list = list, list of strings of different entity types

        Returns:
            df: dataframe, NPV of depreciation deductions for
                    all asset using SL depreciation, all financing types,
                    and all tax treatment types

    """
    df['Y'] = df['ADS Life']
    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            df['z' + entity_list[j] + financing_list[i]] = \
                (df['bonus'] + ((1 - df['bonus']) *
                                ((1 - np.exp(-1 * r[i, j] *
                                             df['Y'])) / (r[i, j]*df['Y']))))

    df.drop(['Y'], axis=1, inplace=True)

    return df


def econ(df, r, pi, financing_list, entity_list):
    """
    Makes the calculation for the NPV of depreciation using economic
    depreciation rates.

    Args:
        df: dataframe, contains economic depreciation and tax
            depreciation schedules for all assets where DBSL depreciation
            will be applied.
        r: scalar, nominal interest rate
        pi: scalar, inflatino rate
        financing_list: list, list of strings defining financing options
                        (e.g., typically financed, debt financed,
                        equity financed)
        entity_list = list, list of strings of different entity types

        Returns:
            df: dataframe, NPV of depreciation deductions for
                    all asset using economics depreciation, all
                    financing types, and all tax treatment types

    """

    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            df['z'+entity_list[j] + financing_list[i]] = \
                df['bonus'] + ((1 - df['bonus']) * (((df['delta']) /
                                                     (df['delta'] +
                                                      r[i, j] - pi))))
    return df
