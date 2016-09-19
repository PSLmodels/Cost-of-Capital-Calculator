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
                        "Economic Depreciation Rate": "delta"},inplace=True)
    econ_deprec_rates['Asset'] = econ_deprec_rates['Asset'].str.strip()
    econ_deprec_rates['bea_asset_code'] = econ_deprec_rates['bea_asset_code'].str.strip()

    return econ_deprec_rates

def calc_tax_depr_rates(r, delta, bonus_deprec, deprec_system, tax_methods, financing_list, entity_list):
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
    tax_deprec_rates['Asset Type'] = tax_deprec_rates['Asset Type'].str.strip()

    # update tax_deprec_rates based on user defined parameters
    tax_deprec_rates['System'] = tax_deprec_rates['GDS'].apply(str_modified)
    tax_deprec_rates['System'].replace(deprec_system,inplace=True)

    # add bonus depreciation to tax deprec parameters dataframe
    tax_deprec_rates['bonus'] = tax_deprec_rates['GDS'].apply(str_modified)
    tax_deprec_rates['bonus'].replace(bonus_deprec,inplace=True)

    # merge in econ depreciation rates
    tax_deprec_rates = pd.merge(tax_deprec_rates, delta, how='left', left_on=['Asset Type'],
      right_on=['Asset'], left_index=False, right_index=False, sort=False,
      copy=True)

    z = npv_tax_deprec(tax_deprec_rates, r, tax_methods, financing_list, entity_list)

    # replace tax depreciation rates on land and inventories w/ zero
    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            z.ix[z['Asset Type']=='Land', 'z'+entity_list[j]+financing_list[i]] = 0
            z.ix[z['Asset Type']=='Inventories', 'z'+entity_list[j]+financing_list[i]] = 0

    return z

def npv_tax_deprec(df, r, tax_methods, financing_list, entity_list):
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


    df_gds = dbsl(df.loc[df['System']=='GDS'].copy(), r, financing_list, entity_list)
    df_ads = sl(df.loc[df['System']=='ADS'].copy(), r, financing_list, entity_list)
    df_econ = econ(df.loc[df['System']=='Economic'].copy(), r, financing_list, entity_list)

    # append gds and ads results
    df_all = df_gds.append(df_ads.append(df_econ,ignore_index=True), ignore_index=True)

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
        :returns: The net present value of declining balance depreciation allowances
        :rtype: 96x3x2 array

    """
    df['Y'] = df['GDS']
    df['beta'] = df['b']/df['Y']
    # df['Y_star'] = ((df['Y']-1)*(1-(1/df['b']))).where(df['bonus']!=0., inplace=True)
    # df['Y_star'] = (df['Y']*(1-(1/df['b']))).where(df['bonus']==0., inplace=True)
    df['Y_star'] = ((((df['Y']-1)*(1-(1/df['b'])))*(df['bonus']!=0.)) +
                    ((1-(df['bonus']!=0.))*(df['Y']*(1-(1/df['b'])))))


    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            # df['z1'+entity_list[j]+financing_list[i]] = \
            #     (((df['beta']/(df['beta']+r[i,j]))*(1-np.exp(-1*(df['beta']
            #         +r[i,j])*df['Y_star']))) +
            #     ((np.exp(-1*df['beta']*df['Y_star'])/(((df['Y']-1)-
            #     df['Y_star'])*r[i,j]))*(np.exp(-1*r[i,j]*df['Y_star'])-
            #                             np.exp(-1*r[i,j]*(df['Y']-1))))).where(df['bonus']!=0.)
            # df['z'+entity_list[j]+financing_list[i]] = \
            #     ((df['bonus']+df['beta'] + ((1-(df['bonus']-df['beta']))*
            #    (df['z1'+entity_list[j]+financing_list[i]]/(1+r[i,j]))))).where(df['bonus']!=0.)
            # df['z'+entity_list[j]+financing_list[i]] = \
            #     (((df['beta']/(df['beta']+r[i,j]))*(1-np.exp(-1*(df['beta']+r[i,j])*
            #         df['Y_star']))) +
            #     ((np.exp(-1*df['beta']*df['Y_star'])/((df['Y']-df['Y_star'])
            #         *r[i,j]))*(np.exp(-1*r[i,j]*df['Y_star'])-np.exp(-1*r[i,j]*df['Y'])))).where(df['bonus']==0.)
            df['z1'+entity_list[j]+financing_list[i]] = \
                            (((((df['beta']/(df['beta']+r[i,j]))*(1-np.exp(-1*(df['beta']
                                +r[i,j])*df['Y_star']))) +
                            ((np.exp(-1*df['beta']*df['Y_star'])/(((df['Y']-1)-
                            df['Y_star'])*r[i,j]))*(np.exp(-1*r[i,j]*df['Y_star'])-
                                                    np.exp(-1*r[i,j]*(df['Y']-1))))))*(df['bonus']!=0.))
            df['z'+entity_list[j]+financing_list[i]] = \
                            ((((df['bonus']+(df['beta']*(1-(df['bonus']))) + ((1-(df['bonus']+(df['beta']*(1-(df['bonus'])))))*
                           (df['z1'+entity_list[j]+financing_list[i]]/(1+r[i,j])))))*(df['bonus']!=0.))
                           + (((((df['beta']/(df['beta']+r[i,j]))*(1-np.exp(-1*(df['beta']+r[i,j])*
                               df['Y_star']))) +
                           ((np.exp(-1*df['beta']*df['Y_star'])/((df['Y']-df['Y_star'])
                               *r[i,j]))*(np.exp(-1*r[i,j]*df['Y_star'])-np.exp(-1*r[i,j]*df['Y']))))
                              *(1-(df['bonus']!=0.)))))

            # don't allow bonus to give NPV > 1
            df.ix[df['z'+entity_list[j]+financing_list[i]] > 1., 'z'+entity_list[j]+financing_list[i]] = 1.


    df.drop(['z1_c', 'z1_c_d', 'z1_c_e', 'z1_nc', 'z1_nc_d', 'z1_nc_e', 'beta', 'Y', 'Y_star'], axis=1, inplace=True)

    return df

def sl(df, r, financing_list, entity_list):
    """Makes the calculation for the straight line method of depreciation.

        :param Y: Service life
        :param r: Discount rate
        :param bonus_deprec: Reform for bonus depreciation
        :type Y: int, float
        :type r: 3x2 array
        :type bonus_deprec: int, float
        :returns: The net present value of straight line depreciation allowances
        :rtype: 96x3x2 array

    """
    df['Y'] = df['ADS']
    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            # df['z1'+entity_list[j]+financing_list[i]] = \
            #     (np.exp(-1*r[i,j]*(df['Y']-1)/(r[i,j]*(df['Y']-1)))).where(df['bonus']!=0.)
            # df['z'+entity_list[j]+financing_list[i]] = \
            #     (df['bonus']+(1./df['Y']) + ((1-df['bonus']-(1./df['Y']))*
            #    (df['z1'+entity_list[j]+financing_list[i]]/(1+r[i,j])))).where(df['bonus']!=0.)
            # df['z'+entity_list[j]+financing_list[i]] = \
            #     (np.exp(-1*r[i,j]*df['Y'])/(r[i,j]*df['Y'])).where(df['bonus']==0.)
            df['z1'+entity_list[j]+financing_list[i]] = \
                ((np.exp(-1*r[i,j]*(df['Y']-1)/(r[i,j]*(df['Y']-1))))*(df['bonus']!=0.))
            df['z'+entity_list[j]+financing_list[i]] = \
                (((df['bonus']+((1./df['Y'])*(1-df['bonus'])) + ((1-(df['bonus']+((1./df['Y'])*(1-df['bonus']))))*
               (df['z1'+entity_list[j]+financing_list[i]]/(1+r[i,j]))))*(df['bonus']!=0.))
                + ((np.exp(-1*r[i,j]*df['Y'])/(r[i,j]*df['Y']))**(1-(df['bonus']!=0.))))

            # don't allow bonus to give NPV > 1
            df.ix[df['z'+entity_list[j]+financing_list[i]] > 1., 'z'+entity_list[j]+financing_list[i]] = 1.

    df.drop(['z1_c', 'z1_c_d', 'z1_c_e', 'z1_nc', 'z1_nc_d', 'z1_nc_e', 'Y'], axis=1, inplace=True)

    return df


def econ(df, r, financing_list, entity_list):
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
            # df['z'+entity_list[j]+financing_list[i]] = \
            #     (df['bonus']+(df['delta']) + ((1-df['bonus']-df['delta'])*
            #    (df['delta']/((df['delta']+r[i,j])*(1+r[i,j]))))).where(df['bonus']!=0.)
            # df['z'+entity_list[j]+financing_list[i]] = \
            #     (df['delta']/(df['delta']+r[i,j])).where(df['bonus']==0.)
            df['z'+entity_list[j]+financing_list[i]] = \
                (((df['bonus']+(df['delta']*(1-df['bonus'])) + ((1-(df['bonus']+(df['delta']*(1-df['bonus']))))*
               (df['delta']/((df['delta']+r[i,j])*(1+r[i,j])))))*(df['bonus']!=0.))
                + ((df['delta']/(df['delta']+r[i,j]))*(1-(df['bonus']==0.))))

            # don't allow bonus to give NPV > 1
            df.ix[df['z'+entity_list[j]+financing_list[i]] > 1., 'z'+entity_list[j]+financing_list[i]] = 1.

    return df
