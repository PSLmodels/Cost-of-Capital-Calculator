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
    # Opening data on depreciable fixed assets, inventories, and land for parnterhsips
    # with net profits:
    xwalk = pd.read_csv(_DETAIL_SOLE_PROP_CROSS_PATH)
    # keep only codes that help to identify complete industries
    xwalk = xwalk[xwalk['complete']==1]

    # read in nonfarm sole prop data
    nonfarm_df = pd.read_csv(_NFARM_PATH)
    # Opens the nonfarm inventory data
    nonfarm_inv = soi.format_dataframe(pd.read_csv(_NFARM_INV).T,crosswalk)
    # Inserts the codes into the nonfarm dataframe
    nonfarm_df.insert(1, 'Codes:', crosswalk['Codes:'])
    # Formats the column names for the nonfarm dataframe
    nonfarm_df = format_columns(nonfarm_df)
    # Saves the industry names and codes so they can be reused later
    names = nonfarm_df['Industrial sector']
    codes = nonfarm_df['Codes:']
    nonfarm_df = nonfarm_df * _DDCT_FILE_FCTR
    # Puts back the original industry names and codes
    nonfarm_df['Industrial sector'] = names
    nonfarm_df['Codes:'] = codes
    # Takes only the overall values and removes duplicate columns for all the partner and sole prop data
    nonfarm_df = nonfarm_df.T.groupby(sort=False,level=0).first().T
    prt_deduct = prt_deduct.T.groupby(sort=False,level=0).first().T
    prt_asst = prt_asst.T.groupby(sort=False,level=0).first().T
    nonfarm_inv = nonfarm_inv.T.groupby(sort=False,level=0).first().T
    # Trims off all the extra columns and only leaves pertinent depreciation info
    sp_inv = nonfarm_inv[['Codes:', 'Inventory, beginning of year']]
    sp_depr = nonfarm_df[['Codes:','Depreciation deduction']]
    prt_depr = prt_deduct[['Codes:', 'Depreciation']]
    # Combines duplicate codes to create aggregate industries
    prt_depr = prt_depr.groupby('Codes:',sort=False).sum()
    codes = prt_depr.index.tolist()
    prt_depr.insert(0,'Codes:', codes)
    prt_depr.index = np.arange(0,len(prt_depr))
    # Trims and combines the partner capital data
    prt_capital = prt_asst[['Codes:', 'Depreciable assets', 'Less:  Accumulated depreciation', 'Land']]
    prt_capital = prt_capital.groupby('Codes:',sort=False).sum()
    codes = prt_capital.index.tolist()
    prt_capital.insert(0,'Codes:', codes)
    prt_capital.index = np.arange(0,len(prt_depr))
    # Joins all four of the dataframes into one (the common column is the industry codes) and stores the data in numpy arrays
    capital_data = np.array(sp_inv.merge(sp_depr.merge(prt_capital.merge(prt_depr))))



    # read in partner data
    df = format_stuff(pd.read_excel(_AST_FILE, skiprows=2, skip_footer=6))
    # Cuts off the repeated columns so only the data for all partnerships remains
    df03 = df.T.groupby(sort=False,level=0).first().T
    # Fixing the index labels of the new dataframe
    df03.reset_index(inplace=True)
    # Keep only variables of interest
    df03['Fixed Assets'] = (df03['Depreciable assets']-
                                         df03['Less:  Accumulated depreciation'])
    df03 = df03[['Item','Fixed Assets','Inventories','Land']]
    df03['Item'] = df03['Item'].str.strip()
    # merge industry codes to partner data
    df03 = pd.merge(df03, xwalk, how='inner', left_on=['Item'],
      right_on=['Industry:'], left_index=False, right_index=False, sort=False,
      copy=True)
    df03.drop(['Item','Industry:','Codes:','Notes:','complete'], axis=1, inplace=True)

    # Sums together the repeated codes into one industry
    df03 = df03.groupby('INDY_CD',sort=False).sum()
    df03.reset_index(level=0, inplace=True)

    ## create ratios for minor industry assets using corporate data
    # read in crosswalk for bea and soi industry codes
    soi_bea_ind_codes = pd.read_csv(_SOI_BEA_CROSS, dtype={'bea_ind_code':str})
    soi_bea_ind_codes.drop('notes', axis=1, inplace=True)
    # drop one repeated minor ind code in crosswalk
    soi_bea_ind_codes.drop_duplicates(subset=['minor_code_alt'],inplace=True)

    # merge codes to partner data
    # likely better way to do this...
    df03_sector = df03[(df03['INDY_CD']>9) & (df03['INDY_CD']<100)]
    df03_major = df03[(df03['INDY_CD']>99) & (df03['INDY_CD']<1000)]
    df03_minor = df03[(df03['INDY_CD']>99999) & (df03['INDY_CD']<1000000)]
    sector_df = pd.merge(df03_sector, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
      right_on=['sector_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    major_df = pd.merge(df03_major, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
      right_on=['major_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    minor_df = pd.merge(df03_minor, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
      right_on=['minor_code'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=True)
    # df03 = pd.merge(df03, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
    #                     right_on=['major_code'],left_index=False,
    #                     right_index=False, sort=False,suffixes=('_x', '_y'),
    #                     copy=True)
    part_data = sector_df.append([major_df,minor_df],ignore_index=True).copy().reset_index()
    part_data.drop(['bea_inv_name','bea_code','_merge'], axis=1, inplace=True)

    # merge codes to total corp data
    # inner join means that we keep only rows that match in both datasets
    # this should keep only unique soi minor industries
    # in total corp data - note that s corp data already unique by sector
    s_corp = entity_dfs['s_corp'][['INDY_CD','Fixed Assets','Inventories','Land']]
    corp = pd.merge(s_corp, soi_bea_ind_codes, how='inner', left_on=['INDY_CD'],
                        right_on=['minor_code_alt'],left_index=False,
                        right_index=False, sort=False,suffixes=('_x', '_y'),
                        copy=True)
    columns = ['Fixed Assets','Inventories','Land']
    for var in columns :
        corp[var+'_ratio'] = corp.groupby(['major_code'])[var].apply(lambda x: x/float(x.sum()))

    corp.drop(['bea_inv_name','bea_code','sector_code',
               'minor_code']+columns, axis=1, inplace=True)

    # merge these ratios to the partner data
    part_data = pd.merge(part_data, corp, how='right', left_on=['minor_code_alt'],
                        right_on=['minor_code_alt'],left_index=False,
                        right_index=False, sort=False,suffixes=('_x', '_y'),
                        copy=True)


    part_data.ix[part_data['INDY_CD_x']>99999, 'Fixed Assets_ratio'] = 1.
    part_data.ix[part_data['INDY_CD_x']>99999, 'Inventories_ratio'] = 1.
    part_data.ix[part_data['INDY_CD_x']>99999, 'Land_ratio'] = 1.
    # allocate capital based on ratios
    for var in columns :
        part_data[var] = part_data[var]*part_data[var+'_ratio']

    part_data.drop(map(lambda (x,y): x+y, zip(columns, ['_ratio']*len(columns))), axis=1, inplace=True)

    part_data.to_csv('testDF.csv',encoding='utf-8')
    quit()


    import btax.soi_processing as soi
	# Opens the file that contains the non farm sole prop data
    nonfarm_df = pd.read_csv(_NFARM_PATH)
    # Opens the nonfarm data crosswalk
    crosswalk = pd.read_csv(_DDCT_IN_CROSS_PATH)
    # Opens the nonfarm inventory data
    nonfarm_inv = soi.format_dataframe(pd.read_csv(_NFARM_INV).T,crosswalk)
    # Opens the crosswalk for the partner data
    # prt_crosswalk = pd.read_csv(_PRT_CROSS)
    # Opens and formats the partner depreciation deduction data
    inc_cross = pd.read_csv(_INC_IN_CROSS_PATH)
    prt_deduct = pull_soi_partner.format_stuff(pd.read_excel(_INC_FILE, skiprows=2, skip_footer=6), inc_cross)
    # Opens and formats the partner asset data
    ast_cross = pd.read_csv(_AST_IN_CROSS_PATH)
    prt_asst = pull_soi_partner.format_stuff(pd.read_excel(_AST_FILE, skiprows=2, skip_footer=6), ast_cross)
    # prt_asst = pd.read_csv(_PRT_ASST).T
    # prt_asst = soi.format_dataframe(prt_asst, prt_crosswalk)
    # Inserts the codes into the nonfarm dataframe
    nonfarm_df.insert(1, 'Codes:', crosswalk['Codes:'])
    # Formats the column names for the nonfarm dataframe
    nonfarm_df = format_columns(nonfarm_df)
    # Saves the industry names and codes so they can be reused later
    names = nonfarm_df['Industrial sector']
    codes = nonfarm_df['Codes:']
    nonfarm_df = nonfarm_df * _DDCT_FILE_FCTR
    # Puts back the original industry names and codes
    nonfarm_df['Industrial sector'] = names
    nonfarm_df['Codes:'] = codes
    # Takes only the overall values and removes duplicate columns for all the partner and sole prop data
    nonfarm_df = nonfarm_df.T.groupby(sort=False,level=0).first().T
    prt_deduct = prt_deduct.T.groupby(sort=False,level=0).first().T
    prt_asst = prt_asst.T.groupby(sort=False,level=0).first().T
    nonfarm_inv = nonfarm_inv.T.groupby(sort=False,level=0).first().T
    # Trims off all the extra columns and only leaves pertinent depreciation info
    sp_inv = nonfarm_inv[['Codes:', 'Inventory, beginning of year']]
    sp_depr = nonfarm_df[['Codes:','Depreciation deduction']]
    prt_depr = prt_deduct[['Codes:', 'Depreciation']]
    # Combines duplicate codes to create aggregate industries
    prt_depr = prt_depr.groupby('Codes:',sort=False).sum()
    codes = prt_depr.index.tolist()
    prt_depr.insert(0,'Codes:', codes)
    prt_depr.index = np.arange(0,len(prt_depr))
    # Trims and combines the partner capital data
    prt_capital = prt_asst[['Codes:', 'Depreciable assets', 'Less:  Accumulated depreciation', 'Land']]
    prt_capital = prt_capital.groupby('Codes:',sort=False).sum()
    codes = prt_capital.index.tolist()
    prt_capital.insert(0,'Codes:', codes)
    prt_capital.index = np.arange(0,len(prt_depr))
    # Joins all four of the dataframes into one (the common column is the industry codes) and stores the data in numpy arrays
    capital_data = np.array(sp_inv.merge(sp_depr.merge(prt_capital.merge(prt_depr))))

    fixed_assets = []
    land_data =[]
    inv_data = []
    # Iterates over each array in the new data structure and pulls out the relevant info for FA, Inv, and Land
    for array in capital_data:
        if(array[6] != 0):
            # Multiplies the ratio of land to depreciation deduction for partners by the depreciation deduction taken by sole props
            land = np.array([array[0],(array[5]*array[2]/float(array[6]))])
            # Multiplies the ratio of depreciable assets to depreciation deduction by the sole prop depreciation deduction
            fixed_asset = np.array([array[0],(array[3]-array[4])*array[2]/float(array[6])])
            # Takes the inventory value for sole props
            inventory = np.array([array[0], array[1]])
            # Adds these values to the capital stock lists
            fixed_assets.append(fixed_asset)
            land_data.append(land)
            inv_data.append(inventory)
    cstock_list = []
    # Iterates over the filled capital stock lists and converts them to numpy industry arrays
    for i in xrange(0,len(fixed_assets)):
        nfarm_cstock = np.array([int(fixed_assets[i][0]), float(fixed_assets[i][1]), float(inv_data[i][1]), float(land_data[i][1])])
        cstock_list.append(nfarm_cstock)
    # Stores the newly created sole proprietorship capital stock data in a dataframe then sums duplicate codes
    nfarm_df = pd.DataFrame(cstock_list, index=np.arange(0,len(cstock_list)), columns=['Codes:', 'Fixed Assets', 'Inventories', 'Land'])
    nfarm_df = nfarm_df.groupby('Codes:',sort=False).sum()
    codes = nfarm_df.index.tolist()
    nfarm_df.insert(0,'Codes:', codes)
    nfarm_df.index = np.arange(0,len(nfarm_df))
    # Similar to the method for partners, the baseline codes are added and holes are filled based on the corporate proportions
    baseline_codes = pd.read_csv(_SOI_CODES)
    nfarm_df = baseline_codes.merge(nfarm_df, how = 'outer').fillna(0)
    nfarm_df = baseline_codes.merge(nfarm_df, how = 'inner')
    nfarm_df = soi.interpolate_data(entity_dfs, nfarm_df)

    # Calculates the FA and Land for Farm sole proprietorships.
    farm_df = pd.read_csv(_FARM_IN_PATH)
    asst_land = farm_df['R_p'][0] + farm_df['Q_p'][0]
    agr_capital = prt_capital[prt_capital.index == 1]
    assts_agr = float(agr_capital['Depreciable assets'][1] - agr_capital['Less:  Accumulated depreciation'][1])
    land_agr = float(agr_capital['Land'])
    prt_farm_land = land_agr / (land_agr + assts_agr) * asst_land
    sp_farm_land = farm_df['A_sp'][0] * prt_farm_land / farm_df['A_p'][0]
    sp_farm_assts = farm_df['R_sp'][0] + farm_df['Q_sp'][0] - sp_farm_land
    sp_farm_cstock = np.array([sp_farm_assts, 0, sp_farm_land])

    # Adds farm data to industry 11
    nfarm_df.ix[nfarm_df['Codes:']==1,'Fixed Assets'] += sp_farm_cstock[0]
    nfarm_df.ix[nfarm_df['Codes:']==11,'Fixed Assets'] += sp_farm_cstock[0]
    nfarm_df.ix[nfarm_df['Codes:']==111,'Fixed Assets'] += sp_farm_cstock[0]
    nfarm_df.ix[nfarm_df['Codes:']==1,'Land'] += sp_farm_cstock[2]
    nfarm_df.ix[nfarm_df['Codes:']==11,'Land'] += sp_farm_cstock[2]
    nfarm_df.ix[nfarm_df['Codes:']==111,'Land'] += sp_farm_cstock[2]

    # Creates the dictionary of sector : dataframe that is returned and used to update entity_dfs
    data = {'sole_prop_data':nfarm_df}

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
