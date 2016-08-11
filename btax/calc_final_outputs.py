"""
Calculate Rho, METR, & METTR (calc_final_output.py):
-------------------------------------------------------------------------------

This module provides functions for calculating the cost of capital (rho), marginal effective tax rate
(METR) and marginal effective total tax rate (METTR). Using the parameters from parameters.py values for
rho, metr, and mettr are calculated for each BEA asset type. Then values are calculated for rho and metr
at the industry level. This script also contains a function which aggregates the fixed asset data to the
two digit NAICS code level. Last Updated 7/27/2016
"""
# Packages
import os.path
import sys
import pandas as pd
import numpy as np
import parameters as param
from btax.util import get_paths

globals().update(get_paths())


def asset_calcs(params):
    """Computes rho, METR, and METTR at the asset level.

        :param params: Constants used in the calculation
        :param fixed_assets: Fixed asset data for each industry
        :type params: dictionary
        :type fixed_assets: dictionary
        :returns: rho, METR, METTR, ind_rho, ind_METR
        :rtype: 96x3x2, DataFrame
    """
    # grabs the constant values from the parameters dictionary
    inflation_rate = params['inflation rate']
    stat_tax = params['tax rate']
    discount_rate = params['discount rate']
    save_rate = params['return to savers']
    delta = params['econ depreciation']
    r_prime = params['after-tax rate']
    inv_credit = params['inv_credit']
    w = params['prop tax']
    z = params['depr allow']
    financing_list = params['financing_list']
    entity_list = params['entity_list']
    asset_dict = params['asset_dict']

    # initialize dataframe - start w/ z output
    output_by_asset = z.copy()


    # calculate the cost of capital, metr, mettr
    for i in range(save_rate.shape[0]):
        for j in range(save_rate.shape[1]):
            output_by_asset['rho'+entity_list[j]+financing_list[i]] = \
                ((((discount_rate[i,j] - inflation_rate) +
                output_by_asset['delta']) * (1- inv_credit- (stat_tax[j] *
                output_by_asset['z'+entity_list[j]+financing_list[i]])) /
                (1-stat_tax[j])) + w - output_by_asset['delta'])
            output_by_asset['metr'+entity_list[j]+financing_list[i]] = \
                (output_by_asset['rho'+entity_list[j]+financing_list[i]] -
                (r_prime[i,j] - inflation_rate))/ output_by_asset['rho'+entity_list[j]+financing_list[i]]
            output_by_asset['mettr'+entity_list[j]+financing_list[i]] = \
                (output_by_asset['rho'+entity_list[j]+financing_list[i]] -
                save_rate[i,j])/ output_by_asset['rho'+entity_list[j]+financing_list[i]]

    # create asset category variable
    output_by_asset['asset_category'] = output_by_asset['Asset Type']
    output_by_asset['asset_category'].replace(asset_dict,inplace=True)


    return output_by_asset


def industry_calcs(params, fixed_assets, output_by_asset):
    """Calculates the cost of capital and marginal effective tax rates by industry

        :param agg_fa: Fixed assets organized by entity, asset, and industry
        :param rho: Cost of capital by asset
        :param metr: Marginal effective tax rate by asset
        :type agg_fa: dictionary
        :type rho: 96x3x2 Array
        :type metr: 96x3x2 Array
        :returns: The result of the weighted average of the cost of capital and METR for each BEA industry
        :rtype: DataFrame
    """
    # grabs the constant values from the parameters dictionary
    inflation_rate = params['inflation rate']
    stat_tax = params['tax rate']
    discount_rate = params['discount rate']
    save_rate = params['return to savers']
    delta = params['econ depreciation']
    r_prime = params['after-tax rate']
    inv_credit = params['inv_credit']
    w = params['prop tax']
    z = params['depr allow']
    financing_list = params['financing_list']
    entity_list = params['entity_list']
    ind_dict = params['ind_dict']

    # initialize dataframe - start w/ fixed assets by industry and asset type
    bea = fixed_assets.copy()

    # merge cost of capital, depreciation rates by asset
    df2 = output_by_asset[['bea_asset_code', 'delta','z_c','z_c_d','z_c_e','z_nc', 'z_nc_d',
                        'z_nc_e', 'rho_c','rho_c_d','rho_c_e','rho_nc',
                        'rho_nc_d', 'rho_nc_e']].copy()
    by_industry_asset = pd.merge(bea, df2, how='left', left_on=['bea_asset_code'],
      right_on=['bea_asset_code'], left_index=False, right_index=False, sort=False,
      copy=True)

    # create weighted averages by industry/tax treatment
    by_industry = pd.DataFrame({'delta' : by_industry_asset.groupby( ['bea_ind_code'] ).apply(wavg, "delta", "assets")}).reset_index()
    col_list = ['z_c','z_c_d','z_c_e','z_nc', 'z_nc_d',
                        'z_nc_e', 'rho_c','rho_c_d','rho_c_e','rho_nc',
                        'rho_nc_d', 'rho_nc_e']
    for item in col_list:
        by_industry[item] = (pd.DataFrame({item : by_industry_asset.groupby('bea_ind_code').apply(wavg, item, "assets")})).reset_index()[item]

    # calculate the cost of capital, metr, mettr
    for i in range(save_rate.shape[0]):
        for j in range(save_rate.shape[1]):
            by_industry['metr'+entity_list[j]+financing_list[i]] = \
                ((by_industry['rho'+entity_list[j]+financing_list[i]] -
                (r_prime[i,j] - inflation_rate))/(by_industry['rho'+entity_list[j]+financing_list[i]]))
            by_industry['mettr'+entity_list[j]+financing_list[i]] = \
                ((by_industry['rho'+entity_list[j]+financing_list[i]] -
                save_rate[i,j])/(by_industry['rho'+entity_list[j]+financing_list[i]]))

    # merge in industry names
    df3 = fixed_assets[['Industry','bea_ind_code']]
    df3.drop_duplicates(inplace=True)
    by_industry = pd.merge(by_industry, df3, how='left', left_on=['bea_ind_code'],
      right_on=['bea_ind_code'], left_index=False, right_index=False, sort=False,
      copy=True)
    by_industry['Industry'] = by_industry['Industry'].str.strip()

    # create major industry variable
    by_industry['major_industry'] = by_industry['Industry']
    by_industry['major_industry'].replace(ind_dict,inplace=True)

    return by_industry

def wavg(group, avg_name, weight_name):
    """
    Computes a weighted average
    """
    d = group[avg_name]
    w = group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return d.mean()
