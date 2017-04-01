"""
SOI Proprietorship Data (pull_soi_partner.py):
-------------------------------------------------------------------------------
Module that handles reading in the soi proprietorship data.
Because no fixed asset and land data is available for sole props, the
depreciation deduction is used along with the partner data. The
ratio of land and fixed assets to the depreciation deduction for partners
is used to impute the data for sole props. The sole prop inventory and
farm data is also loaded in.
Last updated: 7/26/2016.

"""

import os.path
import re
import sys

import numpy as np
import pandas as pd

from btax.util import get_paths, to_str
import btax.pull_soi_partner as prt
globals().update(get_paths())

_DDCT_FILE_FCTR = 10 ** 3

def load_proprietorship_data(entity_dfs):
    """Using the partner and sole prop data, the capital stock data is imputed.

        :param entity_dfs: Contains all the soi data by entity
        :type entity_dfs: dictionary
        :returns: The SOI capital stock data, organized by industry
        :rtype: dictionary
    """
    # Opening data on depreciable fixed assets, inventories, and
    # land for non-farm sole props
    df = pd.read_excel(_NFARM_PATH, skiprows=2, skip_footer=8)
    nonfarm_df = format_dataframe(df)
    # Cuts off the repeated columns so only the data for all sole props remains
    nonfarm_df = nonfarm_df.T.groupby(sort=False, level=0).first().T
    # Fixing the index labels of the new dataframe
    nonfarm_df.reset_index(inplace=True,drop=True)
    # Keep only variables of interest
    cols = ['Industry','Depreciation deduction [1,2]']
    nonfarm_df = nonfarm_df[cols]
    industry = nonfarm_df['Industry']
    re_replace = lambda x: re.sub('[\s+]', '',x)
    nonfarm_df['Industry'] = industry.apply(re_replace)
    col_map = {"Industry": "Item",
               "Depreciation deduction [1,2]": "Depreciation"}
    nonfarm_df.rename(columns=col_map, inplace=True)

    # Opens the nonfarm inventory data
    df = pd.read_excel(_NFARM_INV, skiprows=1, skip_footer=8)
    nonfarm_inv = prt.format_excel(df)
    # Cuts off the repeated columns so only the data
    # for all sole props remains
    nonfarm_inv = nonfarm_inv.T.groupby(sort=False, level=0).first().T
    nonfarm_inv.columns = [to_str(c) for c in nonfarm_inv.columns]
    # Fixing the index labels of the new dataframe
    nonfarm_inv.reset_index(inplace=True, drop=True)
    # Keep only variables of interest
    cols = ['Net income status, item','Inventory, end of year']
    nonfarm_inv = nonfarm_inv[cols]
    net_inc = nonfarm_inv['Net income status, item']
    nonfarm_inv['Net income status, item'] = net_inc.str.strip()
    col_map = {
        "Net income status, item" : "Item",
        "Inventory, end of year": "Inventories",
    }
    nonfarm_inv.rename(columns=col_map, inplace=True)
    nonfarm_inv['Item'] = nonfarm_inv['Item'].apply(re_replace)
    # merge together two sole prop data sources
    # have to manually fix a couple names to be compatible
    other_amb = ("Otherambulatoryhealthcareservices"
                 "(includingambulanceservices,bloodandorganbanks)")
    nonfarm_df.ix[nonfarm_df['Item'] == other_amb, 'Item'] = other_amb
    prop_appr = ("Officesofrealestateagents,brokers,"
                 "propertymanagers,andappraisers")
    nonfarm_df.ix[nonfarm_df['Item'] == prop_appr, 'Item'] = prop_appr
    oother = ("OOtherautorepairandmaintenance(includingoilchange,"
              "lubrication,andcarwashes)")
    other = ('Otherautorepairandmaintenance(includingoilchange,'
             'lube,andcarwashes)')
    nonfarm_df.ix[nonfarm_df['Item'] == oother, 'Item']=other
    nonfarm_df = pd.merge(nonfarm_df, nonfarm_inv,
        how='inner', left_on=['Item'],
        right_on=['Item'], left_index=False,
        right_index=False, sort=False,
        copy=True)

    # Read in crosswalk for these data
    xwalk = pd.read_csv(_DETAIL_SOLE_PROP_CROSS_PATH)
    # Keep only codes that help to identify complete industries
    xwalk = xwalk[xwalk['complete'] == 1]
    xwalk = xwalk[['Industry','INDY_CD']]
    re_replace = lambda x: re.sub('[\s+]', '',x)
    xwalk['Industry'] = xwalk['Industry'].apply(re_replace)

    # merge industry codes to sole prop data
    nonfarm_df = pd.merge(nonfarm_df, xwalk,
        how='inner', left_on=['Item'],
        right_on=['Industry'], left_index=False,
        right_index=False, sort=False,
        copy=True)
    nonfarm_df.drop(['Item','Industry'], axis=1, inplace=True)

    # Sums together the repeated codes into one industry
    nonfarm_df = nonfarm_df.groupby('INDY_CD',sort=False).sum()
    nonfarm_df.reset_index(level=0, inplace=True)

    # add some rows for industry codes not in the sole prop data because they are zero
    df = pd.DataFrame(columns=('INDY_CD','Depreciation','Inventories'))
    missing_code_list = [312, 517, 519, 524140, 524142, 524143,
                         524156, 524159, 55, 521, 525, 531115]
    for i in range(len(missing_code_list)):
        df.loc[i] = [int(missing_code_list[i]), 0., 0.]
    nonfarm_df = nonfarm_df.append(df,ignore_index=True).copy().reset_index()

    # attribute over a minor industry only idenfified in w/ other minor ind in SOI
    ndf = nonfarm_df['INDY_CD']==531115
    nonfarm_df.ix[ndf, 'Depreciation'] = nonfarm_df.ix[nonfarm_df['INDY_CD']==531135, 'Depreciation'].values*0.5
    nonfarm_df.ix[ndf, 'Inventories'] = nonfarm_df.ix[nonfarm_df['INDY_CD']==531135, 'Inventories'].values*0.5
    indy_cd = nonfarm_df['INDY_CD']==531135
    depr = nonfarm_df.ix[indy_cd, 'Depreciation']
    nonfarm_df.ix[indy_cd, 'Depreciation'] = depr.values * 0.5
    inv = nonfarm_df.ix[indy_cd, 'Inventories']
    nonfarm_df.ix[indy_cd, 'Inventories'] = inv.values * 0.5

    # Create ratios for minor industry assets using corporate data
    # read in crosswalk for bea and soi industry codes
    soi_bea_ind_codes = pd.read_csv(_SOI_BEA_CROSS, dtype={'bea_ind_code':str})
    soi_bea_ind_codes.drop('notes', axis=1, inplace=True)
    # Drop one repeated minor ind code in crosswalk
    soi_bea_ind_codes.drop_duplicates(subset=['minor_code_alt'],inplace=True)

    # Merge codes to sole prop data likely better way to do this...
    nonfarm_sector = nonfarm_df[(nonfarm_df['INDY_CD'] > 9) &
                                (nonfarm_df['INDY_CD'] < 100)]
    nonfarm_major = nonfarm_df[(nonfarm_df['INDY_CD'] > 99) &
                               (nonfarm_df['INDY_CD'] < 1000)]
    nonfarm_minor = nonfarm_df[(nonfarm_df['INDY_CD'] > 99999) &
                               (nonfarm_df['INDY_CD'] < 1000000)]
    sector_df = pd.merge(nonfarm_sector, soi_bea_ind_codes,
        how='inner', left_on=['INDY_CD'],
        right_on=['sector_code'], left_index=False,
        right_index=False, sort=False,
        copy=True,indicator=True)
    major_df = pd.merge(nonfarm_major, soi_bea_ind_codes,
        how='inner', left_on=['INDY_CD'],
        right_on=['major_code'], left_index=False,
        right_index=False, sort=False,
        copy=True,indicator=True)
    minor_df = pd.merge(nonfarm_minor, soi_bea_ind_codes,
        how='inner', left_on=['INDY_CD'],
        right_on=['minor_code'], left_index=False,
        right_index=False, sort=False,
        copy=True, indicator=True)
    sector = sector_df.append([major_df,minor_df], ignore_index=True)
    nonfarm_data = sector.copy().reset_index()
    drop_cols = ['bea_inv_name','bea_code','_merge']
    nonfarm_data.drop(drop_cols, axis=1, inplace=True)

    # merge codes to total part data
    # inner join means that we keep only rows that match in both datasets
    # this should keep only unique soi minor industries
    columns = ['Inventories', 'Depreciation']
    cols = ['minor_code_alt', 'part_type'] + columns + ['Land','Fixed Assets']
    part_data = entity_dfs['part_data'][cols].copy()

    # sum at industry-partner type level
    part_data = part_data.groupby(['minor_code_alt']).sum().reset_index()
    part2 = part_data[['minor_code_alt']+columns].copy()
    partner = pd.merge(part2, soi_bea_ind_codes,
        how='inner', left_on=['minor_code_alt'],
        right_on=['minor_code_alt'], left_index=False,
        right_index=False, sort=False,
        suffixes=('_x', '_y'), copy=True)

    for var in columns:
        v = partner.groupby(['major_code'])[var]
        partner[var + '_ratio'] = v.apply(lambda x: x / float(x.sum()))

    columns_partner = ['bea_inv_name','bea_code',
                       'sector_code', 'minor_code']+columns
    partner.drop(columns_partner, axis=1, inplace=True)
    # merge these ratios to the sole prop data
    nonfarm = pd.merge(nonfarm_data, partner,
        how='right', left_on=['minor_code_alt'],
        right_on=['minor_code_alt'],left_index=False,
        right_index=False, sort=False,suffixes=('_x', '_y'),
        copy=True,indicator=True)
    # Filling in missing values.  This works ok now but need to be
    # careful as the ratio value could cause problems
    nonfarm['Inventories'].fillna(value=0., axis=0, inplace=True)
    nonfarm['Inventories_ratio'].fillna(value=1., axis=0, inplace=True)

    # allocate capital based on ratios
    for var in columns :
        nonfarm.ix[nonfarm['INDY_CD'] > 99999, var + '_ratio'] = 1.
        nonfarm[var] = nonfarm[var] * nonfarm[var + '_ratio']

    nonfarm.drop(list(x + '_ratio' for x in columns), axis=1, inplace=True)
    nonfarm.drop(['index','sector_code','major_code_x','minor_code',
                  'major_code_y','_merge'], axis=1, inplace=True)

    # data here totals out for allocable industries (so doesn't hit SOI totals
    # for all industries bc some not allocated to an industry)

    # merge in partner data to get ratios need to impute FA's and land
    part_ratios = part_data[['minor_code_alt','Fixed Assets',
                             'Depreciation','Land']].copy()
    assets = part_ratios['Fixed Assets']
    depr = part_ratios['Depreciation']
    part_ratios['FA_ratio'] = assets / depr
    land = part_ratios['Land']
    part_ratios['Land_ratio'] = land / assets
    part_ratios = part_ratios[['minor_code_alt','FA_ratio','Land_ratio']]
    nonfarm = pd.merge(nonfarm, part_ratios,
                       how='inner', left_on=['minor_code_alt'],
                       right_on=['minor_code_alt'],left_index=False,
                       right_index=False, sort=False,suffixes=('_x', '_y'),
                       copy=True,indicator=False)

    # need to find ratio of assets from BEA to SOI
    bea_ratio = 1.
    fa = nonfarm['FA_ratio']
    depr = nonfarm['Depreciation']
    nonfarm['Fixed Assets'] = fa * depr * bea_ratio
    nonfarm['Land'] = nonfarm['Land_ratio']*nonfarm['Fixed Assets']
    nonfarm.drop(['Land_ratio','FA_ratio'], axis=1, inplace=True)

    # Calculates the FA and Land for Farm sole proprietorships.
    # Note: we should update so read in raw Census of Agriculture
    # What about inventories for farm sole props? Worry about??
    farm_df = pd.read_csv(_FARM_IN_PATH)
    asst_land = farm_df['R_p'][0] + farm_df['Q_p'][0]
    part_111 = part_data['minor_code_alt']==111
    land = part_data.ix[part_111, 'Land']
    land_ratio = np.array((land /
                  (part_data.ix[part_111, 'Fixed Assets'] +
                   part_data.ix[part_111, 'Land'])))
    part_land = land_ratio * asst_land
    sp_farm_land = farm_df['A_sp'][0] * part_land / farm_df['A_p'][0]
    sp_farm_assts = farm_df['R_sp'][0] + farm_df['Q_sp'][0] - sp_farm_land
    sp_farm_cstock = np.array([sp_farm_assts, 0, sp_farm_land])

    # Adds farm data to industry 111
    indy_cd = nonfarm['INDY_CD']==111
    nonfarm.ix[indy_cd,'Fixed Assets'] += sp_farm_cstock[0]
    nonfarm.ix[indy_cd,'Land'] += sp_farm_cstock[2]

    # Creates the dictionary of sector : dataframe that is returned and
    # used to update entity_dfs
    data = {'sole_prop_data': nonfarm}

    return data

def format_columns(nonfarm_df):
    """Removes extra characters from the columns of the dataframe

        :param nonfarm_df: Contains the nonfarm capital stock data
        :type nonfarm_df: DataFrame
        :returns: The formatted dataframe
        :rtype: DataFrame
    """
    columns = nonfarm_df.columns.tolist()
    for i in xrange(0,len(columns)):
        column = columns[i]
        if '.1' in column:
            column = column[:-2]
        if '\n' in column:
            column = column.replace('\n', ' ').replace('\r','')
        column = column.rstrip()
        columns[i] = column
    nonfarm_df.columns = columns
    return nonfarm_df

def format_dataframe(nonfarm_df):
    """Fixes the column headers, drops the unnecessary rows,
    inserts the SOI codes and multiplies by a factor of a thousand
        :param nonfarm: The dataframe that will be formatted
        :param crosswalk: SOI industry names and codes
        :type crosswalk: DataFrame
        :type nonfarm: DataFrame
        :returns: The dataframe in a simple format
        :rtype: DataFrame
    """
    # Creates a list from the first row of the dataframe
    columns = nonfarm_df.iloc[0].tolist()
    # Replaces the first item in the list with a new label
    columns[0] = 'Industry'
    # Sets the values of the columns on the dataframes
    nonfarm_df.columns = list(to_str(x).replace('\n', ' ') for x in columns)
    # Drops the first couple of rows and last row in the dataframe
    nonfarm_df.dropna(inplace=True)
    # Multiplies each value in the dataframe by a factor of 1000
    nonfarm_df.iloc[:,1:] = nonfarm_df.iloc[:,1:] * _DDCT_FILE_FCTR
    # Resets the index values to a normal range after some have been dropped
    nonfarm_df.reset_index(inplace=True,drop=True)

    return nonfarm_df
