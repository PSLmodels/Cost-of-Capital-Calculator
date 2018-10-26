"""
Calculate Rho, METR, & METTR (calc_final_output.py):
------------------------------------------------------------------------
This module provides functions for calculating the cost of capital (rho),
marginal effective tax rate (METR) and marginal effective total tax rate
(METTR). Using the parameters from parameters.py values for rho, metr,
and mettr are calculated for each BEA asset type. Then values are
calculated for rho and metr at the industry level. This script also
contains a function which aggregates the fixed asset data to the two
digit NAICS code level.
"""
# Packages
import os.path
import sys
import pandas as pd
import numpy as np
import btax.parameters as param
from btax.util import get_paths, wavg

globals().update(get_paths())


def cost_of_capital(df, w, expense_inventory, stat_tax, inv_credit, phi,
                    Y_v, inflation_rate, discount_rate,
                    entity_list, financing_list):
    """
    Compute the cost of capital and the user cost of capital

    Args:
        df: DataFrame, assets by type with depreciation rates
        w: scalar, property tax rate
        expense_inventory: boolean, whether inventories are expensed
        stat_tax: Numpy array, entity level taxes for corp and noncorp
        inv_credit: scalar, investment tax credit
        phi: scalar, fraction of inventories using FIFO
        Y_v: integer, number of years inventories held
        inflation_rate: scalar, rate of inflation
        discount_rate: Numpy array, discount rate used by entity type
                                    and financing used
        entity_list: list, identifiers for entity type
        financing_list: list, indentifiers for financing used

    Returns:
        df: DataFrame, assets by type with depreciation and cost of
                      capital

    """
    # calculate the cost of capital, metr, mettr
    for i in range(discount_rate.shape[0]):
        for j in range(discount_rate.shape[1]):
            df['rho' + entity_list[j] + financing_list[i]] = \
                ((((discount_rate[i, j] - inflation_rate) + df['delta'])
                  * (1 - inv_credit - (stat_tax[j] *
                                       df['z' + entity_list[j] +
                                          financing_list[i]])) /
                  (1 - stat_tax[j])) + w - df['delta'])
            if not expense_inventory:
                rho_FIFO = (((1 / Y_v) *
                             np.log((np.exp(discount_rate[i, j] * Y_v)
                                     - stat_tax[j]) /
                                    (1 - stat_tax[j]))) -
                            inflation_rate)
                rho_LIFO = ((1 / Y_v) *
                            np.log((np.exp((discount_rate[i, j] -
                                            inflation_rate) * Y_v) -
                                    stat_tax[j]) / (1 - stat_tax[j])))
                df.loc[df['Asset Type'] == "Inventories", 'rho' +
                       entity_list[j] + financing_list[i]] = \
                        phi * rho_FIFO + (1 - phi) * rho_LIFO
            df['ucc' + entity_list[j] + financing_list[i]] =\
                df['rho' + entity_list[j] + financing_list[i]] + df['delta']
    return df


def metr(df, r_prime, inflation_rate, save_rate, entity_list,
         financing_list):
    """
    Compute the METR and METTR

    Args:
        df: DataFrame, assets by type with depreciation rates and cost
                       of capital
        r_prime: Numpy array, discount rate used by entity type
                                    and financing used
        inflation_rate: scalar, rate of inflation
        save_rate: Numpy array, after-tax return on savings
        entity_list: list, identifiers for entity type
        financing_list: list, indentifiers for financing used

    Returns:
        df: DataFrame, assets by type with depreciation and cost of
                      capital and METR and METTR and tax wedge

    """
    for i in range(save_rate.shape[0]):
        for j in range(save_rate.shape[1]):
            df['metr' + entity_list[j] + financing_list[i]] = \
                ((df['rho' + entity_list[j] + financing_list[i]] -
                  (r_prime[i, j] - inflation_rate)) /
                 df['rho' + entity_list[j] + financing_list[i]])
            df['mettr' + entity_list[j] + financing_list[i]] = \
                ((df['rho' + entity_list[j] + financing_list[i]] -
                  save_rate[i, j]) /
                 df['rho' + entity_list[j] + financing_list[i]])
            df['tax_wedge' + entity_list[j] + financing_list[i]] = \
                ((df['rho' + entity_list[j] + financing_list[i]] -
                  save_rate[i, j]))

    return df


def eatr(df, p, stat_tax, entity_list, financing_list):
    """
    Compute the EATR

    Args:
        df: DataFrame, assets by type with depreciation rates and cost
                       of capital and METR
        p: scalar, profit rate
        stat_tax: Numpy array, entity level taxes for corp and noncorp
        entity_list: list, identifiers for entity type
        financing_list: list, indentifiers for financing used

    Returns:
        df: DataFrame, assets by type with depreciation and cost of
                      capital and METR and METTR and EATR
    """
    for i in range(len(financing_list)):
        for j in range(len(entity_list)):
            df['eatr' + entity_list[j] + financing_list[i]] = \
                ((((p - df['rho' + entity_list[j] + financing_list[i]]) /
                 p) * stat_tax[j]) + ((df['rho' + entity_list[j] +
                                          financing_list[i]] / p) *
                                      df['metr' + entity_list[j] +
                                         financing_list[i]]))

    return df


def asset_calcs(params, asset_data):
    """
    Computes rho, ucc, METR, METTR, tax wedge, EATR by asset type.

    Args:
        params: dictionary, Constants used in the calculation
        asset_data: DataFrame, asset data by type and tax treatment

    Returns:
        output_by_asset: DataFrame, cost of capital, METR, METTR, total
                         amount of assets by asset type
    """
    # grab the constant values from the parameters dictionary
    inflation_rate = params['inflation rate']
    stat_tax = params['tax rate']
    discount_rate = params['discount rate']
    save_rate = params['return to savers']
    r_prime = params['after-tax rate']
    inv_credit = params['inv_credit']
    w = params['prop tax']
    z = params['depr allow']
    Y_v = params['Y_v']
    phi = params['phi']
    p = params['p']
    expense_inventory = params['expense_inventory']
    financing_list = params['financing_list']
    entity_list = params['entity_list']
    asset_dict = params['asset_dict']
    major_asset_groups = params['major_asset_groups']

    # initialize dataframe - start w/ z output
    output_by_asset = z.copy()

    # Drop religious buildings and IP of nonprofits
    output_by_asset = output_by_asset[output_by_asset['Asset Type'] !=
                                      'Religious'].copy()
    output_by_asset = output_by_asset[output_by_asset['Asset Type'] !=
                                      'Private universities and colleges'].copy()
    output_by_asset = output_by_asset[output_by_asset['Asset Type'] !=
                                      'Other nonprofit institutions'].copy()

    # calculate the cost of capital, metr, mettr, eatr
    output_by_asset = cost_of_capital(output_by_asset, w,
                                      expense_inventory, stat_tax,
                                      inv_credit, phi, Y_v,
                                      inflation_rate, discount_rate,
                                      entity_list, financing_list)
    output_by_asset = metr(output_by_asset, r_prime, inflation_rate,
                           save_rate, entity_list, financing_list)
    output_by_asset = eatr(output_by_asset, p, stat_tax, entity_list,
                           financing_list)

    # create asset category variable
    output_by_asset['asset_category'] = output_by_asset['Asset Type']
    output_by_asset['asset_category'].replace(asset_dict, inplace=True)

    # Drop IP (for now - need to better figure out how depreciate)
    # output_by_asset = output_by_asset[output_by_asset['asset_category'] !=
    #                                   'Intellectual Property'].copy()
    # output_by_asset = output_by_asset[output_by_asset['Asset Type'] !=
    #                                   'Land'].copy()

    # merge in dollar value of assets - sep for corp and non-corp
    # should be able to do this better with pivot table
    bea_corp = asset_data[asset_data['tax_treat'] == 'corporate'].copy()
    bea_noncorp = asset_data[asset_data['tax_treat'] == 'non-corporate'].copy()
    bea_corp_assets = (
        pd.DataFrame({'assets': bea_corp.
                      groupby('bea_asset_code')['assets'].
                      sum()})).reset_index()
    bea_noncorp_assets = (pd.DataFrame({'assets': bea_noncorp.
                                        groupby('bea_asset_code')['assets'].
                                        sum()})).reset_index()
    bea_corp_assets.rename(columns={"assets": "assets_c"}, inplace=True)
    bea_noncorp_assets.rename(columns={"assets": "assets_nc"}, inplace=True)

    output_by_asset = pd.merge(output_by_asset, bea_corp_assets,
                               how='left', left_on=['bea_asset_code'],
                               right_on=['bea_asset_code'],
                               left_index=False, right_index=False,
                               sort=False, copy=True)
    output_by_asset = pd.merge(output_by_asset, bea_noncorp_assets,
                               how='left', left_on=['bea_asset_code'],
                               right_on=['bea_asset_code'],
                               left_index=False, right_index=False,
                               sort=False, copy=True)

    # Add major asset groups
    output_by_asset['major_asset_group'] = output_by_asset['Asset Type']
    output_by_asset['major_asset_group'].replace(major_asset_groups,
                                                 inplace=True)

    # Now compute METR and other output by major asset group
    # create weighted averages by major asset group/tax treatment
    by_major_asset =\
        pd.DataFrame({'delta': output_by_asset.
                      groupby(['major_asset_group']).
                      apply(wavg, "delta", "assets_c")}).reset_index()
    corp_list = ['z_c', 'z_c_d', 'z_c_e', 'rho_c', 'rho_c_d', 'rho_c_e',
                 'ucc_c', 'ucc_c_d', 'ucc_c_e']
    noncorp_list = ['z_nc', 'z_nc_d', 'z_nc_e', 'rho_nc', 'rho_nc_d',
                    'rho_nc_e', 'ucc_nc', 'ucc_nc_d', 'ucc_nc_e']
    for item in corp_list:
        by_major_asset[item] =\
            (pd.DataFrame({item: output_by_asset.
                           groupby(['major_asset_group']).
                           apply(wavg, item, "assets_c")})).reset_index()[item]
    for item in noncorp_list:
        by_major_asset[item] =\
            (pd.DataFrame({item: output_by_asset.
                           groupby(['major_asset_group']).
                           apply(wavg, item, "assets_nc")})).reset_index()[item]

    by_major_asset['assets_c'] =\
        (pd.DataFrame({'assets_c': output_by_asset.
                       groupby(['major_asset_group'])['assets_c'].
                       sum()})).reset_index()['assets_c']
    by_major_asset['assets_nc'] = (
        pd.DataFrame({'assets_nc': output_by_asset.
                      groupby(['major_asset_group'])['assets_nc'].
                      sum()})).reset_index()['assets_nc']

    # calculate metr, mettr
    by_major_asset = metr(by_major_asset, r_prime, inflation_rate,
                          save_rate, entity_list, financing_list)
    by_major_asset = eatr(by_major_asset, p, stat_tax, entity_list,
                          financing_list)

    # make asset type = major asset group in by_major_asset
    by_major_asset['Asset'] = by_major_asset['major_asset_group']
    by_major_asset['Asset Type'] = by_major_asset['major_asset_group']

    # make calculation for overall rates
    overall = pd.DataFrame(
        {'delta': ((output_by_asset['delta'] *
                    output_by_asset['assets_c']).sum() /
                   output_by_asset['assets_c'].sum())}, index=[0])
    overall['assets_c'] = output_by_asset['assets_c'].sum()
    overall['assets_nc'] = output_by_asset['assets_nc'].sum()
    # overall =\
    #     pd.DataFrame({'delta_nc': ((output_by_asset['delta'] *
    #                                 output_by_asset['assets_nc']).sum()
    #                                 / output_by_asset['assets_nc'].
    #                                 sum())}).reset_index()
    overall['Asset'] = 'All Investments'
    overall['Asset Type'] = 'All Investments'
    overall['major_asset_group'] = 'All Investments'
    for item in corp_list:
        overall[item] = ((output_by_asset[item] *
                          output_by_asset['assets_c']).sum() /
                         output_by_asset['assets_c'].sum())
    for item in noncorp_list:
        overall[item] = ((output_by_asset[item] *
                          output_by_asset['assets_nc']).sum() /
                         output_by_asset['assets_nc'].sum())
    # calculate the cost of capital, metr, mettr
    overall = metr(overall, r_prime, inflation_rate, save_rate,
                   entity_list, financing_list)
    overall = eatr(overall, p, stat_tax, entity_list, financing_list)

    # append by_major_asset to output_by_asset
    # drop asset types that are only one in major group
    by_major_asset = by_major_asset[by_major_asset['major_asset_group'] !=
                                    'Inventories'].copy()
    by_major_asset = by_major_asset[by_major_asset['major_asset_group'] !=
                                    'Land'].copy()
    output_by_asset = (
        output_by_asset.append([by_major_asset, overall], sort=True,
                               ignore_index=True)).copy().reset_index()
    output_by_asset.drop('index', axis=1, inplace=True)

    # sort output_by_asset dataframe
    output_by_asset.sort_values(['Asset'], inplace=True)
    output_by_asset.reset_index(drop=True, inplace=True)

    return output_by_asset


def industry_calcs(params, asset_data, output_by_asset):
    """
    Calculates the cost of capital and marginal effective tax rates by
    industry.

    Args:
        params: dictionary, Constants used in the calculation
        asset_data: DataFrame, asset data by type and tax treatment
        output_by_asset: DataFrame, cost of capital, METRs, by asset

    Returns:
        by_industry: DataFrame, cost of capital, METR, METTR, total
                     amount of assets by asset type
    """
    # grabs the constant values from the parameters dictionary
    inflation_rate = params['inflation rate']
    save_rate = params['return to savers']
    r_prime = params['after-tax rate']
    financing_list = params['financing_list']
    entity_list = params['entity_list']
    p = params['p']
    stat_tax = params['tax rate']
    bea_code_dict = params['bea_code_dict']

    # initialize dataframe - start w/ fixed assets by industry and asset type
    bea = asset_data.copy()

    # merge cost of capital, depreciation rates by asset
    df2 = output_by_asset[['bea_asset_code', 'delta', 'z_c', 'z_c_d',
                           'z_c_e', 'z_nc', 'z_nc_d', 'z_nc_e', 'rho_c',
                           'rho_c_d', 'rho_c_e', 'rho_nc', 'rho_nc_d',
                           'rho_nc_e', 'ucc_c', 'ucc_c_d', 'ucc_c_e', 'ucc_nc',
                           'ucc_nc_d', 'ucc_nc_e', 'asset_category']].copy()
    by_industry_asset = pd.merge(bea, df2, how='right',
                                 left_on=['bea_asset_code'],
                                 right_on=['bea_asset_code'],
                                 left_index=False, right_index=False,
                                 sort=False, copy=True)

    # drop major groups - want to build up from individual assets
    # by_industry_asset =\
    #     by_industry_asset[by_industry_asset['asset_category'] !=
    #                       'Intellectual Property'].copy()
    by_industry_asset =\
        by_industry_asset[by_industry_asset['Asset Type'] !=
                          'Intellectual Property'].copy()
    by_industry_asset =\
        by_industry_asset[by_industry_asset['Asset Type'] !=
                          'Equipment'].copy()
    by_industry_asset =\
        by_industry_asset[by_industry_asset['Asset Type'] !=
                          'Structures'].copy()
    by_industry_asset =\
        by_industry_asset[by_industry_asset['Asset Type'] !=
                          'All Investments'].copy()
    # by_industry_asset =\
    #     by_industry_asset[by_industry_asset['tax_treat'] !=
    #                       'owner_occupied_housing'].copy()

    # create weighted averages by industry/tax treatment
    by_industry_tax =\
        pd.DataFrame({'delta': by_industry_asset.groupby(['bea_ind_code',
                                                          'tax_treat']).
                      apply(wavg, "delta", "assets")}).reset_index()
    col_list = ['z_c', 'z_c_d', 'z_c_e', 'z_nc', 'z_nc_d', 'z_nc_e',
                'rho_c', 'rho_c_d', 'rho_c_e', 'rho_nc', 'rho_nc_d',
                'rho_nc_e', 'ucc_c', 'ucc_c_d', 'ucc_c_e', 'ucc_nc',
                'ucc_nc_d', 'ucc_nc_e']
    for item in col_list:
        by_industry_tax[item] =\
            (pd.DataFrame({item: by_industry_asset.groupby(['bea_ind_code',
                                                            'tax_treat']).
                           apply(wavg, item, "assets")})).reset_index()[item]

    by_industry_tax['assets'] =\
        (pd.DataFrame({'assets': by_industry_asset.
                       groupby(['bea_ind_code', 'tax_treat'])['assets'].
                       sum()})).reset_index()['assets']

    # calculate metr and mettr and eatr
    by_industry_tax = metr(by_industry_tax, r_prime, inflation_rate,
                           save_rate, entity_list, financing_list)
    by_industry_tax = eatr(by_industry_tax, p, stat_tax, entity_list,
                           financing_list)

    # put together in different format (later we should consider changing how
    # output is handled and do long format)
    corp = by_industry_tax[by_industry_tax['tax_treat'] ==
                           'corporate'].copy()
    non_corp = by_industry_tax[by_industry_tax['tax_treat'] ==
                               'non-corporate'].copy()
    corp = corp[['bea_ind_code', 'delta', 'z_c', 'z_c_d', 'z_c_e',
                 'rho_c', 'rho_c_d', 'rho_c_e', 'ucc_c', 'ucc_c_d',
                 'ucc_c_e', 'metr_c', 'metr_c_d',
                 'metr_c_e', 'mettr_c', 'mettr_c_d', 'mettr_c_e',
                  'tax_wedge_c', 'tax_wedge_c_d', 'tax_wedge_c_e',
                  'eatr_c', 'eatr_c_d', 'eatr_c_e', 'assets']].copy()
    non_corp = non_corp[['bea_ind_code', 'delta', 'z_nc', 'z_nc_d',
                         'z_nc_e', 'rho_nc', 'rho_nc_d', 'rho_nc_e',
                         'ucc_nc', 'ucc_nc_d', 'ucc_nc_e',
                         'metr_nc', 'metr_nc_d', 'metr_nc_e', 'mettr_nc',
                         'mettr_nc_d', 'mettr_nc_e', 'tax_wedge_nc',
                         'tax_wedge_nc_d', 'tax_wedge_nc_e', 'eatr_nc',
                         'eatr_nc_d', 'eatr_nc_e', 'assets']].copy()
    corp.rename(columns={"delta": "delta_c", "assets": "assets_c"},
                inplace=True)
    non_corp.rename(columns={"delta": "delta_nc", "assets": "assets_nc"},
                    inplace=True)
    by_industry = pd.merge(corp, non_corp, how='inner',
                           on=['bea_ind_code'], left_index=False,
                           right_index=False, sort=False, copy=True)
    # merge in industry names
    df3 = asset_data[['Industry', 'bea_ind_code']].copy()
    df3.drop_duplicates(inplace=True)
    by_industry = pd.merge(by_industry, df3, how='left',
                           left_on=['bea_ind_code'],
                           right_on=['bea_ind_code'], left_index=False,
                           right_index=False, sort=False, copy=True)
    by_industry['Industry'] = by_industry['Industry'].str.strip()
    by_industry['major_industry'] = by_industry['bea_ind_code']
    by_industry['major_industry'].replace(bea_code_dict, inplace=True)

    '''
    ### Do above for major industry groups
    '''
    # create major industry variable
    by_industry_asset['Industry'] = by_industry_asset['Industry'].str.strip()
    by_industry_asset['major_industry'] = by_industry_asset['bea_ind_code']
    by_industry_asset['major_industry'].replace(bea_code_dict, inplace=True)

    # create weighted averages by industry/tax treatment
    by_major_ind_tax =\
        pd.DataFrame({'delta': by_industry_asset.
                      groupby(['major_industry', 'tax_treat']).
                      apply(wavg, "delta", "assets")}).reset_index()
    col_list = ['z_c', 'z_c_d', 'z_c_e', 'z_nc', 'z_nc_d', 'z_nc_e',
                'rho_c', 'rho_c_d', 'rho_c_e', 'rho_nc', 'rho_nc_d',
                'rho_nc_e', 'ucc_c', 'ucc_c_d', 'ucc_c_e', 'ucc_nc',
                'ucc_nc_d', 'ucc_nc_e']
    for item in col_list:
        by_major_ind_tax[item] =\
            (pd.DataFrame({item: by_industry_asset.
                           groupby(['major_industry', 'tax_treat']).
                           apply(wavg, item, "assets")})).reset_index()[item]

    by_major_ind_tax['assets'] =\
        (pd.DataFrame({'assets': by_industry_asset.
                       groupby(['major_industry', 'tax_treat'])['assets'].
                       sum()})).reset_index()['assets']

    # calculate metr and mettr and eatr
    by_major_ind_tax = metr(by_major_ind_tax, r_prime, inflation_rate,
                            save_rate, entity_list, financing_list)
    by_major_ind_tax = eatr(by_major_ind_tax, p, stat_tax, entity_list,
                            financing_list)

    # put together in different format (later we should consider
    # changing how output is handled and do long format)
    corp = by_major_ind_tax[by_major_ind_tax['tax_treat'] ==
                            'corporate'].copy()
    non_corp = by_major_ind_tax[by_major_ind_tax['tax_treat'] ==
                                'non-corporate'].copy()
    corp = corp[['major_industry', 'delta', 'z_c', 'z_c_d', 'z_c_e',
                 'rho_c', 'rho_c_d', 'rho_c_e', 'ucc_c', 'ucc_c_d',
                 'ucc_c_e', 'metr_c', 'metr_c_d',
                 'metr_c_e', 'mettr_c', 'mettr_c_d', 'mettr_c_e',
                 'tax_wedge_c', 'tax_wedge_c_d', 'tax_wedge_c_e',
                 'eatr_c', 'eatr_c_d', 'eatr_c_e', 'assets']].copy()
    non_corp = non_corp[['major_industry', 'delta', 'z_nc', 'z_nc_d',
                         'z_nc_e', 'rho_nc', 'rho_nc_d', 'rho_nc_e',
                         'ucc_nc', 'ucc_nc_d', 'ucc_nc_e',
                         'metr_nc', 'metr_nc_d', 'metr_nc_e', 'mettr_nc',
                         'mettr_nc_d', 'mettr_nc_e', 'tax_wedge_nc',
                         'tax_wedge_nc_d', 'tax_wedge_nc_e', 'eatr_nc',
                         'eatr_nc_d', 'eatr_nc_e', 'assets']].copy()
    corp.rename(columns={"delta": "delta_c", "assets": "assets_c"},
                inplace=True)
    non_corp.rename(columns={"delta": "delta_nc", "assets": "assets_nc"},
                    inplace=True)
    by_major_ind = pd.merge(corp, non_corp, how='inner',
                            on=['major_industry'], left_index=False,
                            right_index=False, sort=False,copy=True)
    by_major_ind['Industry'] = by_major_ind['major_industry']

    # make calculation for overall rates
    output_by_asset = output_by_asset[output_by_asset['Asset Type'] !=
                                      'All Investments'].copy()
    output_by_asset = output_by_asset[output_by_asset['Asset Type'] !=
                                      'Equipment'].copy()
    output_by_asset = output_by_asset[output_by_asset['Asset Type'] !=
                                      'Structures'].copy()
    output_by_asset = output_by_asset[output_by_asset['Asset Type'] !=
                                      'Intellectual Property'].copy()
    corp_list = ['z_c', 'z_c_d', 'z_c_e', 'rho_c', 'rho_c_d', 'rho_c_e',
                 'ucc_c', 'ucc_c_d', 'ucc_c_e']
    noncorp_list = ['z_nc', 'z_nc_d', 'z_nc_e', 'rho_nc', 'rho_nc_d',
                    'rho_nc_e', 'ucc_nc', 'ucc_nc_d', 'ucc_nc_e']
    overall = pd.DataFrame({'delta_c': ((output_by_asset['delta'] *
                                         output_by_asset['assets_c']).
                                        sum() / output_by_asset['assets_c'].
                                        sum())}, index=[0])
    overall['delta_nc'] = ((output_by_asset['delta'] *
                            output_by_asset['assets_nc']).sum() /
                           output_by_asset['assets_nc'].sum())
    overall['assets_c'] = output_by_asset['assets_c'].sum()
    overall['assets_nc'] = output_by_asset['assets_nc'].sum()
    # overall = pd.DataFrame({'delta_nc' : ((output_by_asset['delta']*
    #           output_by_asset['assets_nc']).sum()/
    #           output_by_asset['assets_nc'].sum())}).reset_index()
    overall['Industry'] = 'All Investments'
    overall['major_industry'] = 'All Investments'
    for item in corp_list:
        overall[item] = ((output_by_asset[item] *
                          output_by_asset['assets_c']).sum() /
                         output_by_asset['assets_c'].sum())
    for item in noncorp_list:
        overall[item] = ((output_by_asset[item] *
                          output_by_asset['assets_nc']).sum() /
                         output_by_asset['assets_nc'].sum())
    # calculate metr and mettr and eatr
    overall = metr(overall, r_prime, inflation_rate, save_rate,
                   entity_list, financing_list)
    overall = eatr(overall, p, stat_tax, entity_list, financing_list)

    # append by_major_asset to output_by_asset
    # drop major inds when only one in major group
    by_major_ind = by_major_ind[by_major_ind['major_industry'] !=
                                'Utilities'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry'] !=
                                'Construction'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry'] !=
                                'Wholesale trade'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry'] !=
                                'Retail trade'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry'] !=
                                'Management of companies and enterprises'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry'] !=
                                'Educational services'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry'] !=
                                'Other services, except government'].copy()
    by_industry = (by_industry.append([by_major_ind, overall], sort=True,
                                      ignore_index=True)).copy().reset_index()
    by_industry.drop('index', axis=1, inplace=True)

    # sort output_by_asset dataframe
    # by_industry = (by_industry.sort_values(['Industry'],
    #                inplace=True)).copy().reset_index()
    by_industry.sort_values(['Industry'], inplace=True)
    by_industry.reset_index(drop=True, inplace=True)

    return by_industry
