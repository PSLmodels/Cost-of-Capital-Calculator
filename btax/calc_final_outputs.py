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
    Y_v = params['Y_v']
    phi = params['phi']
    financing_list = params['financing_list']
    entity_list = params['entity_list']
    asset_dict = params['asset_dict']
    major_asset_groups = params['major_asset_groups']

    # initialize dataframe - start w/ z output
    output_by_asset = z.copy()

    # Drop religious buildings
    output_by_asset = output_by_asset[output_by_asset['Asset Type']!='Religious'].copy()

    # calculate the cost of capital, metr, mettr
    for i in range(save_rate.shape[0]):
        for j in range(save_rate.shape[1]):
            output_by_asset['rho'+entity_list[j]+financing_list[i]] = \
                ((((discount_rate[i,j] - inflation_rate) +
                output_by_asset['delta']) * (1- inv_credit- (stat_tax[j] *
                output_by_asset['z'+entity_list[j]+financing_list[i]])) /
                (1-stat_tax[j])) + w - output_by_asset['delta'])
            output_by_asset.loc[output_by_asset['Asset Type']=="Inventories",'rho'+entity_list[j]+financing_list[i]] = \
                    ((phi*(((1/Y_v)*np.log((np.exp(discount_rate[i,j]*Y_v)-stat_tax[j])/(1-stat_tax[j])))-inflation_rate))
                    + ((1-phi)*(((1/Y_v)*np.log((np.exp((discount_rate[i,j]-inflation_rate)*Y_v)-stat_tax[j])/(1-stat_tax[j]))))))
            output_by_asset['metr'+entity_list[j]+financing_list[i]] = \
                (output_by_asset['rho'+entity_list[j]+financing_list[i]] -
                (r_prime[i,j] - inflation_rate))/ output_by_asset['rho'+entity_list[j]+financing_list[i]]
            output_by_asset['mettr'+entity_list[j]+financing_list[i]] = \
                (output_by_asset['rho'+entity_list[j]+financing_list[i]] -
                save_rate[i,j])/ output_by_asset['rho'+entity_list[j]+financing_list[i]]

    # create asset category variable
    output_by_asset['asset_category'] = output_by_asset['Asset Type']
    output_by_asset['asset_category'].replace(asset_dict,inplace=True)

    # Drop IP (for now - need to better figure out how depreciate)
    output_by_asset = output_by_asset[output_by_asset['asset_category']!='Intellectual Property'].copy()

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

    # Add major asset groups
    output_by_asset['major_asset_group'] = output_by_asset['Asset Type']
    output_by_asset['major_asset_group'].replace(major_asset_groups,inplace=True)

    # Now compute METR and other output by major asset group
    # create weighted averages by major asset group/tax treatment
    by_major_asset = pd.DataFrame({'delta' : output_by_asset.groupby(
        ['major_asset_group'] ).apply(wavg, "delta", "assets_c")}).reset_index()
    corp_list = ['z_c','z_c_d','z_c_e','rho_c','rho_c_d','rho_c_e']
    noncorp_list = ['z_nc','z_nc_d','z_nc_e','rho_nc','rho_nc_d','rho_nc_e']
    for item in corp_list:
        by_major_asset[item] = (pd.DataFrame({item : output_by_asset.groupby(
            ['major_asset_group']).apply(wavg, item, "assets_c")})).reset_index()[item]
    for item in noncorp_list:
        by_major_asset[item] = (pd.DataFrame({item : output_by_asset.groupby(
            ['major_asset_group']).apply(wavg, item, "assets_nc")})).reset_index()[item]

    by_major_asset['assets_c'] = (pd.DataFrame({'assets_c' : output_by_asset.groupby(
        ['major_asset_group'])['assets_c'].sum()})).reset_index()['assets_c']
    by_major_asset['assets_nc'] = (pd.DataFrame({'assets_nc' : output_by_asset.groupby(
        ['major_asset_group'])['assets_nc'].sum()})).reset_index()['assets_nc']

    # calculate the cost of capital, metr, mettr
    for i in range(save_rate.shape[0]):
        for j in range(save_rate.shape[1]):
            by_major_asset['metr'+entity_list[j]+financing_list[i]] = \
                ((by_major_asset['rho'+entity_list[j]+financing_list[i]] -
                (r_prime[i,j] - inflation_rate))/(by_major_asset['rho'+entity_list[j]+financing_list[i]]))
            by_major_asset['mettr'+entity_list[j]+financing_list[i]] = \
                ((by_major_asset['rho'+entity_list[j]+financing_list[i]] -
                save_rate[i,j])/(by_major_asset['rho'+entity_list[j]+financing_list[i]]))



    # make asset type = major asset group in by_major_asset
    by_major_asset['Asset'] = by_major_asset['major_asset_group']
    by_major_asset['Asset Type'] = by_major_asset['major_asset_group']

    # make calculation for overall rates
    corp_list = ['z_c','z_c_d','z_c_e','rho_c','rho_c_d','rho_c_e']
    noncorp_list = ['z_nc','z_nc_d','z_nc_e','rho_nc','rho_nc_d','rho_nc_e']
    overall = pd.DataFrame({'delta' : ((output_by_asset['delta']*
              output_by_asset['assets_c']).sum()/output_by_asset['assets_c'].sum())},index=[0])
    overall['assets_c'] = output_by_asset['assets_c'].sum()
    overall['assets_nc'] = output_by_asset['assets_nc'].sum()
    # overall = pd.DataFrame({'delta_nc' : ((output_by_asset['delta']*
    #           output_by_asset['assets_nc']).sum()/output_by_asset['assets_nc'].sum())}).reset_index()
    overall['Asset'] = 'All Investments'
    overall['Asset Type'] = 'All Investments'
    overall['major_asset_group'] = 'All Investments'
    for item in corp_list:
        overall[item] = ((output_by_asset[item]*output_by_asset['assets_c']).sum()/
                         output_by_asset['assets_c'].sum())
    for item in noncorp_list:
        overall[item] = ((output_by_asset[item]*output_by_asset['assets_nc']).sum()/
                         output_by_asset['assets_nc'].sum())
    for i in range(save_rate.shape[0]):
        for j in range(save_rate.shape[1]):
            overall['metr'+entity_list[j]+financing_list[i]] = \
                ((overall['rho'+entity_list[j]+financing_list[i]] -
                (r_prime[i,j] - inflation_rate))/(overall['rho'+entity_list[j]+financing_list[i]]))
            overall['mettr'+entity_list[j]+financing_list[i]] = \
                ((overall['rho'+entity_list[j]+financing_list[i]] -
                save_rate[i,j])/(overall['rho'+entity_list[j]+financing_list[i]]))

    # append by_major_asset to output_by_asset
    # drop asset types that are only one in major group
    by_major_asset = by_major_asset[by_major_asset['major_asset_group']!='Inventories'].copy()
    by_major_asset = by_major_asset[by_major_asset['major_asset_group']!='Land'].copy()
    output_by_asset = (output_by_asset.append([by_major_asset,overall],ignore_index=True)).copy().reset_index()
    output_by_asset.drop('index', axis=1,inplace=True)

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
    bea_code_dict = params['bea_code_dict']

    # initialize dataframe - start w/ fixed assets by industry and asset type
    bea = asset_data.copy()

    # merge cost of capital, depreciation rates by asset
    df2 = output_by_asset[['bea_asset_code', 'delta','z_c','z_c_d','z_c_e','z_nc', 'z_nc_d',
                        'z_nc_e', 'rho_c','rho_c_d','rho_c_e','rho_nc',
                        'rho_nc_d', 'rho_nc_e','asset_category']].copy()
    by_industry_asset = pd.merge(bea, df2, how='right', left_on=['bea_asset_code'],
      right_on=['bea_asset_code'], left_index=False, right_index=False, sort=False,
      copy=True)

    # drop certain types of assets and owner occupied housing when making industry calcs
    # Means industry calculations will only be for equipment and structures
    by_industry_asset = by_industry_asset[by_industry_asset['asset_category']!='Intellectual Property'].copy()
    by_industry_asset = by_industry_asset[by_industry_asset['Asset Type']!='Equipment'].copy()
    by_industry_asset = by_industry_asset[by_industry_asset['Asset Type']!='Structures'].copy()
    by_industry_asset = by_industry_asset[by_industry_asset['Asset Type']!='All Investments'].copy()
    #by_industry_asset = by_industry_asset[by_industry_asset['tax_treat']!='owner_occupied_housing'].copy()

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
    by_industry['major_industry'] = by_industry['bea_ind_code']
    by_industry['major_industry'].replace(bea_code_dict,inplace=True)

    '''
    ### Do above for major industry groups
    '''
    # create major industry variable
    by_industry_asset['Industry'] = by_industry_asset['Industry'].str.strip()
    by_industry_asset['major_industry'] = by_industry_asset['bea_ind_code']
    by_industry_asset['major_industry'].replace(bea_code_dict,inplace=True)

    # create weighted averages by industry/tax treatment
    by_major_ind_tax = pd.DataFrame({'delta' : by_industry_asset.groupby(
        ['major_industry','tax_treat'] ).apply(wavg, "delta", "assets")}).reset_index()
    col_list = ['z_c','z_c_d','z_c_e','z_nc', 'z_nc_d',
                        'z_nc_e', 'rho_c','rho_c_d','rho_c_e','rho_nc',
                        'rho_nc_d', 'rho_nc_e']
    for item in col_list:
        by_major_ind_tax[item] = (pd.DataFrame({item : by_industry_asset.groupby(
            ['major_industry','tax_treat']).apply(wavg, item, "assets")})).reset_index()[item]

    by_major_ind_tax['assets'] = (pd.DataFrame({'assets' : by_industry_asset.groupby(
        ['major_industry','tax_treat'])['assets'].sum()})).reset_index()['assets']

    # calculate the cost of capital, metr, mettr
    for i in range(save_rate.shape[0]):
        for j in range(save_rate.shape[1]):
            by_major_ind_tax['metr'+entity_list[j]+financing_list[i]] = \
                ((by_major_ind_tax['rho'+entity_list[j]+financing_list[i]] -
                (r_prime[i,j] - inflation_rate))/(by_major_ind_tax['rho'+entity_list[j]+financing_list[i]]))
            by_major_ind_tax['mettr'+entity_list[j]+financing_list[i]] = \
                ((by_major_ind_tax['rho'+entity_list[j]+financing_list[i]] -
                save_rate[i,j])/(by_major_ind_tax['rho'+entity_list[j]+financing_list[i]]))

    # put together in different format (later we should consider changing how
    # output is handled and do long format)
    corp = by_major_ind_tax[by_major_ind_tax['tax_treat']=='corporate'].copy()
    non_corp = by_major_ind_tax[by_major_ind_tax['tax_treat']=='non-corporate'].copy()
    corp = corp[['major_industry','delta','z_c','z_c_d','z_c_e','rho_c','rho_c_d','rho_c_e',
                 'metr_c','metr_c_d','metr_c_e','mettr_c','mettr_c_d','mettr_c_e','assets']].copy()
    non_corp = non_corp[['major_industry','delta','z_nc','z_nc_d','z_nc_e','rho_nc','rho_nc_d','rho_nc_e',
                 'metr_nc','metr_nc_d','metr_nc_e','mettr_nc','mettr_nc_d','mettr_nc_e','assets']].copy()
    corp.rename(columns={"delta": "delta_c","assets": "assets_c"},inplace=True)
    non_corp.rename(columns={"delta": "delta_nc","assets": "assets_nc"},inplace=True)
    by_major_ind = pd.merge(corp, non_corp, how='inner', on=['major_industry'],
                           left_index=False, right_index=False, sort=False,copy=True)
    by_major_ind['Industry'] = by_major_ind['major_industry']

    # make calculation for overall rates
    output_by_asset = output_by_asset[output_by_asset['Asset Type']!='All Investments'].copy()
    corp_list = ['z_c','z_c_d','z_c_e','rho_c','rho_c_d','rho_c_e']
    noncorp_list = ['z_nc','z_nc_d','z_nc_e','rho_nc','rho_nc_d','rho_nc_e']
    overall = pd.DataFrame({'delta_c' : ((output_by_asset['delta']*
              output_by_asset['assets_c']).sum()/output_by_asset['assets_c'].sum())},index=[0])
    overall['delta_nc'] = ((output_by_asset['delta']*
              output_by_asset['assets_nc']).sum()/output_by_asset['assets_nc'].sum())
    overall['assets_c'] = output_by_asset['assets_c'].sum()
    overall['assets_nc'] = output_by_asset['assets_nc'].sum()
    # overall = pd.DataFrame({'delta_nc' : ((output_by_asset['delta']*
    #           output_by_asset['assets_nc']).sum()/output_by_asset['assets_nc'].sum())}).reset_index()
    overall['Industry'] = 'All Investments'
    overall['major_industry'] = 'All Investments'
    for item in corp_list:
        overall[item] = ((output_by_asset[item]*output_by_asset['assets_c']).sum()/
                         output_by_asset['assets_c'].sum())
    for item in noncorp_list:
        overall[item] = ((output_by_asset[item]*output_by_asset['assets_nc']).sum()/
                         output_by_asset['assets_nc'].sum())
    for i in range(save_rate.shape[0]):
        for j in range(save_rate.shape[1]):
            overall['metr'+entity_list[j]+financing_list[i]] = \
                ((overall['rho'+entity_list[j]+financing_list[i]] -
                (r_prime[i,j] - inflation_rate))/(overall['rho'+entity_list[j]+financing_list[i]]))
            overall['mettr'+entity_list[j]+financing_list[i]] = \
                ((overall['rho'+entity_list[j]+financing_list[i]] -
                save_rate[i,j])/(overall['rho'+entity_list[j]+financing_list[i]]))

    # append by_major_asset to output_by_asset
    # drop major inds when only one in major group
    by_major_ind = by_major_ind[by_major_ind['major_industry']!='Utilities'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry']!='Construction'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry']!='Wholesale trade'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry']!='Retail trade'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry']!='Management of companies and enterprises'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry']!='Educational services'].copy()
    by_major_ind = by_major_ind[by_major_ind['major_industry']!='Other services, except government'].copy()
    by_industry = (by_industry.append([by_major_ind,overall],ignore_index=True)).copy().reset_index()
    by_industry.drop('index', axis=1,inplace=True)

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
