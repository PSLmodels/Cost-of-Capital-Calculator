"""
SOI Proprietorship Data (pull_soi_partner.py):
-------------------------------------------------------------------------------
Module that handles reading in the soi proprietorship data. Because no fixed asset and land data is
available for sole props, the depreciation deduction is used along with the partner data. The
ratio of land and fixed assets to the depreciation deduction for partners is used to impute the data
for sole props. The sole prop inventory and farm data is also loaded in.
Last updated: 7/26/2016.

"""

import os.path
import sys
import numpy as np
import pandas as pd

from btax.util import get_paths
from btax import pull_soi_partner
globals().update(get_paths())

_DDCT_FILE_FCTR = 10**3

def load_proprietorship_data(entity_dfs):
    """Using the partner and sole prop data, the capital stock data is imputed.

        :param entity_dfs: Contains all the soi data by entity
        :type entity_dfs: dictionary
        :returns: The SOI capital stock data, organized by industry
        :rtype: dictionary
    """
    # Opening data on depreciable fixed assets, inventories, and land for non-farm sole props
    nonfarm_df = pd.read_csv(_NFARM_PATH)
    # Formats the column names for the nonfarm dataframe
    nonfarm_df = format_columns(nonfarm_df)
    # Cuts off the repeated columns so only the data for all sole props remains
    nonfarm_df = nonfarm_df.T.groupby(sort=False,level=0).first().T
    # Fixing the index labels of the new dataframe
    nonfarm_df.reset_index(inplace=True)
    # Keep only variables of interest
    nonfarm_df = nonfarm_df[['Industrial sector','Depreciation deduction']]
    nonfarm_df['Industrial sector'] = nonfarm_df['Industrial sector'].str.strip()
    nonfarm_df.rename(columns={"Industrial sector":"Item",
                               "Depreciation deduction": "Depreciation"},inplace=True)
    nonfarm_df['Depreciation'] = nonfarm_df['Depreciation']*_DDCT_FILE_FCTR
    nonfarm_df['Item'] = nonfarm_df['Item'].str.replace(',','')
    nonfarm_df['Item'] = nonfarm_df['Item'].str.replace('\x20\x20','\x20')


    # read in nonfarm sole prop inventories data
    nonfarm_inv = format_dataframe(pd.read_csv(_NFARM_INV).T)
    # Cuts off the repeated columns so only the data for all sole props remains
    nonfarm_inv = nonfarm_inv.T.groupby(sort=False,level=0).first().T
    # Fixing the index labels of the new dataframe
    nonfarm_inv.reset_index(inplace=True)
    # Keep only variables of interest
    nonfarm_inv = nonfarm_inv[['Item','Inventory, end of year']]
    nonfarm_inv['Item'] = nonfarm_inv['Item'].str.strip()
    nonfarm_inv.rename(columns={"Item": "Industrial sector",
                                "Inventory, end of year": "Inventories"},inplace=True)
    nonfarm_inv['Item'] = nonfarm_inv['Industrial sector'].str.replace(',', '')
    nonfarm_inv['Item'] = nonfarm_inv['Item'].str.replace('\x20\x20','\x20')

    # merge together two sole prop data sources
    # have to manually fix a couple names to be compatible
    nonfarm_inv.ix[nonfarm_inv['Item']=='Other ambulatory health care services (including ambulance services blood organ banks)'
                   , 'Item'] = 'Other ambulatory health care services (including ambulance services blood and organ banks)'
    nonfarm_inv.ix[nonfarm_inv['Item']=='Other auto repair and maintenance (including oil change lube and car washes)'
                   , 'Item'] = 'Other auto repair and maintenance (including oil change lubrication and car washes)'
    nonfarm_df = pd.merge(nonfarm_df, nonfarm_inv, how='inner', left_on=['Item'],
      right_on=['Item'], left_index=False, right_index=False, sort=False,
      copy=True)

    # read in crosswalk for these data
    xwalk = pd.read_csv(_DETAIL_SOLE_PROP_CROSS_PATH)
    # keep only codes that help to identify complete industries
    xwalk = xwalk[xwalk['complete']==1]
    xwalk = xwalk[['Industry','INDY_CD']]
    xwalk['Industry'] = xwalk['Industry'].str.strip()

    # merge industry codes to sole prop data
    nonfarm_df = pd.merge(nonfarm_df, xwalk, how='inner', left_on=['Industrial sector'],
      right_on=['Industry'], left_index=False, right_index=False, sort=False,
      copy=True)
    nonfarm_df.drop(['Item','Industrial sector','Industry'], axis=1, inplace=True)

    # Sums together the repeated codes into one industry
    nonfarm_df = nonfarm_df.groupby('INDY_CD',sort=False).sum()
    nonfarm_df.reset_index(level=0, inplace=True)

    # add some rows for industry codes not in the sole prop data because they are zero
    df = pd.DataFrame(columns=('INDY_CD','Depreciation','Inventories'))
    missing_code_list = [312,517,519,524140,524142,524143,524156,524159,55,521,525,531115]
    for i in range(len(missing_code_list)):
        df.loc[i] = [int(missing_code_list[i]),0.,0.]
    nonfarm_df = nonfarm_df.append(df,ignore_index=True).copy().reset_index()

    # attribute over a minor industry only idenfified in w/ other minor ind in SOI
    nonfarm_df.ix[nonfarm_df['INDY_CD']==531115, 'Depreciation'] = nonfarm_df.ix[nonfarm_df['INDY_CD']==531135, 'Depreciation'].values*0.5
    nonfarm_df.ix[nonfarm_df['INDY_CD']==531115, 'Inventories'] = nonfarm_df.ix[nonfarm_df['INDY_CD']==531135, 'Inventories'].values*0.5
    nonfarm_df.ix[nonfarm_df['INDY_CD']==531135, 'Depreciation'] = nonfarm_df.ix[nonfarm_df['INDY_CD']==531135, 'Depreciation'].values*0.5
    nonfarm_df.ix[nonfarm_df['INDY_CD']==531135, 'Inventories'] = nonfarm_df.ix[nonfarm_df['INDY_CD']==531135, 'Inventories'].values*0.5

    ## create ratios for minor industry assets using corporate data
    # read in crosswalk for bea and soi industry codes
    soi_bea_ind_codes = pd.read_csv(_SOI_BEA_CROSS, dtype={'bea_ind_code':str})
    soi_bea_ind_codes.drop('notes', axis=1, inplace=True)
    # drop one repeated minor ind code in crosswalk
    soi_bea_ind_codes.drop_duplicates(subset=['minor_code_alt'],inplace=True)

    # merge codes to sole prop data
    # likely better way to do this...
    nonfarm_sector = nonfarm_df[(nonfarm_df['INDY_CD']>9) & (nonfarm_df['INDY_CD']<100)]
    nonfarm_major = nonfarm_df[(nonfarm_df['INDY_CD']>99) & (nonfarm_df['INDY_CD']<1000)]
    nonfarm_minor = nonfarm_df[(nonfarm_df['INDY_CD']>99999) & (nonfarm_df['INDY_CD']<1000000)]
    sector_df = pd.merge(nonfarm_sector, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
      right_on=['sector_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    major_df = pd.merge(nonfarm_major, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
      right_on=['major_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    minor_df = pd.merge(nonfarm_minor, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
      right_on=['minor_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    nonfarm_data = sector_df.append([major_df,minor_df],ignore_index=True).copy().reset_index()
    nonfarm_data.drop(['bea_inv_name','bea_code','_merge'], axis=1, inplace=True)

    # merge codes to total part data
    # inner join means that we keep only rows that match in both datasets
    # this should keep only unique soi minor industries
    columns = ['Inventories','Depreciation']
    part_data = entity_dfs['part_data'][['minor_code_alt']+columns]
    partner = pd.merge(part_data, soi_bea_ind_codes, how='inner', left_on=['minor_code_alt'],
                        right_on=['minor_code_alt'],left_index=False,
                        right_index=False, sort=False,suffixes=('_x', '_y'),
                        copy=True)

    for var in columns :
        partner[var+'_ratio'] = partner.groupby(['major_code'])[var].apply(lambda x: x/float(x.sum()))


    partner.drop(['bea_inv_name','bea_code','sector_code',
               'minor_code']+columns, axis=1, inplace=True)
    # merge these ratios to the sole prop data
    nonfarm = pd.merge(nonfarm_data, partner, how='right', left_on=['minor_code_alt'],
                        right_on=['minor_code_alt'],left_index=False,
                        right_index=False, sort=False,suffixes=('_x', '_y'),
                        copy=True,indicator=True)
    # filling in missing values.  This works ok now but need to be
    # careful as the ratio value could cause problems
    nonfarm['Inventories'].fillna(value=0.,axis=0,inplace=True)
    nonfarm['Inventories_ratio'].fillna(value=1.,axis=0,inplace=True)

    # allocate capital based on ratios
    for var in columns :
        nonfarm.ix[nonfarm['INDY_CD']>99999, var+'_ratio'] = 1.
        nonfarm[var] = nonfarm[var]*nonfarm[var+'_ratio']

    nonfarm.drop(map(lambda (x,y): x+y, zip(columns, ['_ratio']*len(columns))), axis=1, inplace=True)
    nonfarm.drop(['index','sector_code','major_code_x','minor_code',
                    'major_code_y','_merge'],axis=1,inplace=True)

    # data here totals out for allocable industries (so doesn't hit SOI totals
    # for all industries bc some not allocated to an industry)

    # merge in partner data to get ratios need to impute FA's and land
    part_ratios = entity_dfs['part_data'][['minor_code_alt','Fixed Assets','Depreciation','Land']]
    part_ratios['FA_ratio'] = part_ratios['Fixed Assets']/part_ratios['Depreciation']
    part_ratios['Land_ratio'] = part_ratios['Land']/part_ratios['Fixed Assets']
    part_ratios = part_ratios[['minor_code_alt','FA_ratio','Land_ratio']]
    nonfarm = pd.merge(nonfarm, part_ratios, how='inner', left_on=['minor_code_alt'],
                        right_on=['minor_code_alt'],left_index=False,
                        right_index=False, sort=False,suffixes=('_x', '_y'),
                        copy=True,indicator=False)

    # need to find ratio of assets from BEA to SOI
    bea_ratio = 1.
    nonfarm['Fixed Assets'] = nonfarm['FA_ratio']*nonfarm['Depreciation']*bea_ratio
    nonfarm['Land'] = nonfarm['Land_ratio']*nonfarm['Fixed Assets']
    nonfarm.drop(['Land_ratio','FA_ratio'],axis=1,inplace=True)

    # Calculates the FA and Land for Farm sole proprietorships.
    # Note: we should update so read in raw Census of Agriculture
    farm_df = pd.read_csv(_FARM_IN_PATH)
    asst_land = farm_df['R_p'][0] + farm_df['Q_p'][0]
    part_data = entity_dfs['part_data'][['minor_code_alt','Fixed Assets','Depreciation','Land']]
    land_ratio = np.array((part_data.ix[part_data['minor_code_alt']==111, 'Land']/
                  (part_data.ix[part_data['minor_code_alt']==111, 'Fixed Assets']+
                   part_data.ix[part_data['minor_code_alt']==111, 'Land'])))
    part_land = land_ratio*asst_land
    sp_farm_land = farm_df['A_sp'][0] * part_land / farm_df['A_p'][0]
    sp_farm_assts = farm_df['R_sp'][0] + farm_df['Q_sp'][0] - sp_farm_land
    sp_farm_cstock = np.array([sp_farm_assts, 0, sp_farm_land])

    # Adds farm data to industry 111
    nonfarm.ix[nonfarm['INDY_CD']==111,'Fixed Assets'] += sp_farm_cstock[0]
    nonfarm.ix[nonfarm['INDY_CD']==111,'Land'] += sp_farm_cstock[2]

    # Creates the dictionary of sector : dataframe that is returned and used to update entity_dfs
    data = {'sole_prop_data':nonfarm}

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

def format_dataframe(df):
    """Formats the dataframe with industry codes as the rows and asset information as the columns.

        :param df: The dataframe to be formatted
        :param crosswalk: Maps the SOI codes to their respective industries
        :type df: DataFrame
        :type crosswalk: DataFrame
        :returns: A clean dataframe with the data easily acessible
        :rtype: DataFrame
    """
    indices = []
    # Removes the extra characters from the industry names
    for string in df.index:
        indices.append(string.replace('\n',' ').replace('\r',''))
    # Adds the industry names as the first column in the dataframe
    df.insert(0,indices[0],indices)
    # Stores the values of the first row in columns
    columns = df.iloc[0].tolist()
    # Drops the first row because it will become the column labels
    df = df[df.Item != 'Item']
    # Removes extra characters from the column labels
    for i in xrange(0,len(columns)):
        columns[i] = columns[i].strip().replace('\r','')
    # Sets the new column values
    df.columns = columns
    names = df['Item']
    # Multiplies the entire dataframe by a factor of a thousand
    df = df * _DDCT_FILE_FCTR
    # Replaces the industry names and codes to adjust for the multiplication in the previous step
    df['Item'] = names
    df.reset_index(inplace=True)
    # Returns the newly formatted dataframe
    return df
