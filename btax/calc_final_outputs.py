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


def asset_calcs(params,asset_data):
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

    # Drop religious buildings
    output_by_asset = output_by_asset[output_by_asset['Asset Type']!='Religious'].copy()

    # create asset category variable
    output_by_asset['asset_category'] = output_by_asset['Asset Type']
    output_by_asset['asset_category'].replace(asset_dict,inplace=True)
    output_by_asset.to_csv('out_test.csv',encoding='utf-8')

    # merge in dollar value of assets - sep for corp and non-corp
    # should be able to do this better with pivot table
    bea_corp = asset_data[asset_data['tax_treat']=='corporate'].copy()
    bea_noncorp = asset_data[asset_data['tax_treat']=='non-corporate'].copy()
    bea_corp_assets = (pd.DataFrame({'assets' : bea_corp.groupby('bea_asset_code')['assets'].sum()})).reset_index()
    bea_noncorp_assets = (pd.DataFrame({'assets' : bea_noncorp.groupby('bea_asset_code')['assets'].sum()})).reset_index()
    bea_corp_assets.rename(columns={"assets": "assets_c"},inplace=True)
    bea_noncorp_assets.rename(columns={"assets": "assets_nc"},inplace=True)

    output_by_asset = pd.merge(output_by_asset, bea_corp_assets, how='left', left_on=['bea_asset_code'],
      right_on=['bea_asset_code'], left_index=False, right_index=False, sort=False,
      copy=True)
    output_by_asset = pd.merge(output_by_asset, bea_noncorp_assets, how='left', left_on=['bea_asset_code'],
      right_on=['bea_asset_code'], left_index=False, right_index=False, sort=False,
      copy=True)

    return output_by_asset


def industry_calcs(params, asset_data, output_by_asset):
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
    bea = asset_data.copy()

    # merge cost of capital, depreciation rates by asset
    df2 = output_by_asset[['bea_asset_code', 'delta','z_c','z_c_d','z_c_e','z_nc', 'z_nc_d',
                        'z_nc_e', 'rho_c','rho_c_d','rho_c_e','rho_nc',
                        'rho_nc_d', 'rho_nc_e','asset_category']].copy()
    by_industry_asset = pd.merge(bea, df2, how='left', left_on=['bea_asset_code'],
      right_on=['bea_asset_code'], left_index=False, right_index=False, sort=False,
      copy=True)

    # drop Intellectual Property - not sure have it straight and CBO not include
    by_industry_asset = by_industry_asset[by_industry_asset['asset_category']!='Intellectual Property'].copy()
    #by_industry_asset = by_industry_asset[by_industry_asset['asset_category']!='Land'].copy()
    #by_industry_asset = by_industry_asset[by_industry_asset['asset_category']!='Inventories'].copy()


    # create weighted averages by industry/tax treatment
    by_industry_tax = pd.DataFrame({'delta' : by_industry_asset.groupby(
        ['bea_ind_code','tax_treat'] ).apply(wavg, "delta", "assets")}).reset_index()
    col_list = ['z_c','z_c_d','z_c_e','z_nc', 'z_nc_d',
                        'z_nc_e', 'rho_c','rho_c_d','rho_c_e','rho_nc',
                        'rho_nc_d', 'rho_nc_e']
    for item in col_list:
        by_industry_tax[item] = (pd.DataFrame({item : by_industry_asset.groupby(
            ['bea_ind_code','tax_treat']).apply(wavg, item, "assets")})).reset_index()[item]

    by_industry_tax['assets'] = (pd.DataFrame({'assets' : by_industry_asset.groupby(
        ['bea_ind_code','tax_treat'])['assets'].sum()})).reset_index()['assets']

    # calculate the cost of capital, metr, mettr
    for i in range(save_rate.shape[0]):
        for j in range(save_rate.shape[1]):
            by_industry_tax['metr'+entity_list[j]+financing_list[i]] = \
                ((by_industry_tax['rho'+entity_list[j]+financing_list[i]] -
                (r_prime[i,j] - inflation_rate))/(by_industry_tax['rho'+entity_list[j]+financing_list[i]]))
            by_industry_tax['mettr'+entity_list[j]+financing_list[i]] = \
                ((by_industry_tax['rho'+entity_list[j]+financing_list[i]] -
                save_rate[i,j])/(by_industry_tax['rho'+entity_list[j]+financing_list[i]]))

    # put together in different format (later we should consider changing how
    # output is handled and do long format)
    corp = by_industry_tax[by_industry_tax['tax_treat']=='corporate'].copy()
    non_corp = by_industry_tax[by_industry_tax['tax_treat']=='non-corporate'].copy()
    corp = corp[['bea_ind_code','delta','z_c','z_c_d','z_c_e','rho_c','rho_c_d','rho_c_e',
                 'metr_c','metr_c_d','metr_c_e','mettr_c','mettr_c_d','mettr_c_e','assets']].copy()
    non_corp = non_corp[['bea_ind_code','delta','z_nc','z_nc_d','z_nc_e','rho_nc','rho_nc_d','rho_nc_e',
                 'metr_nc','metr_nc_d','metr_nc_e','mettr_nc','mettr_nc_d','mettr_nc_e','assets']].copy()
    corp.rename(columns={"delta": "delta_c","assets": "assets_c"},inplace=True)
    non_corp.rename(columns={"delta": "delta_nc","assets": "assets_nc"},inplace=True)
    by_industry = pd.merge(corp, non_corp, how='inner', on=['bea_ind_code'],
                           left_index=False, right_index=False, sort=False,copy=True)
    # merge in industry names
    df3 = asset_data[['Industry','bea_ind_code']].copy()
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
