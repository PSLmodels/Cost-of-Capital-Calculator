"""
Fixed Asset Breakdown (read_bea.py):
-------------------------------------------------------------------------------

Using the BEA data spreadsheet fixed assets are allocated to several different industries.
Based on the SOI data the fixed asset data is divided into both corporate and non-corporate entitities.
Because of discrepancies in the BEA classifications, NAICS classifications, and the SOI classifications,
several different crosswalks are used to match the data. The majority of the script takes these crosswalks
and creates dictionaries to map the codes. Last updated 7/27/2016
"""
# Packages:
import os.path
import numpy as np
import pandas as pd
import xlrd
from btax.util import get_paths

# Directories:
globals().update(get_paths())

# Constant factors:
_BEA_IN_FILE_FCTR = 10**6
_FIN_ACCT_FILE_FCTR = 10**9
_START_POS = 8
_SKIP1 = 47
_SKIP2 = 80
_CORP_PRT = [1,2]
_NCORP_PRT = [3,4,5,6,7,8,9,10]


def fixed_assets(soi_data):
    """Opens the BEA workbook and pulls out the asset info

        :param entity_dfs: Contains all the soi data by entity type
        :type entity_dfs: dictionary
        :returns: Fixed asset data organized by industry, entity, and asset type
        :rtype: dictionary
    """
    # Read in BEA fixed asset table
    bea_FA = pd.read_excel(_BEA_ASSET_PATH, sheetname="Datasets")
    bea_FA = bea_FA[['2013']]
    bea_FA['long_code'] = bea_FA.index
    bea_FA.dropna(subset = ['long_code'],inplace=True)
    bea_FA.reset_index(drop=True,inplace=True)
    bea_FA.rename(columns={"2013": "assets"},inplace=True)
    bea_FA['assets'] = bea_FA['assets']*_BEA_IN_FILE_FCTR
    bea_FA['bea_asset_code'] = bea_FA.long_code.str[-6:-2]
    bea_FA['bea_ind_code'] = bea_FA.long_code.str[3:7]

    # Read in BEA asset names
    bea_asset_names = pd.read_excel(_BEA_ASSET_PATH, sheetname="110C",
                header=5, converters={'Asset Codes': str})
    bea_asset_names = bea_asset_names[['Asset Codes','NIPA Asset Types']]
    bea_asset_names.dropna(subset = ['Asset Codes'],inplace=True)
    bea_asset_names.rename(columns={"Asset Codes": "bea_asset_code", "NIPA Asset Types": "Asset Type"},inplace=True)
    bea_asset_names['Asset Type'] = bea_asset_names['Asset Type'].str.strip()

    # Merge asset names to asset data
    bea_FA = pd.merge(bea_FA, bea_asset_names, how='inner', on=['bea_asset_code'],
      left_index=False, right_index=False, sort=False,
      copy=True)


    # Read in BEA industry names
    bea_ind_names = pd.read_excel(_BEA_ASSET_PATH, sheetname="readme",
                                  converters={'BEA CODE': str}, header=14)
    bea_ind_names = bea_ind_names[['INDUSTRY TITLE ','BEA CODE']]
    bea_ind_names.dropna(subset = ['BEA CODE'],inplace=True)
    bea_ind_names.rename(columns={"INDUSTRY TITLE ": "Industry", "BEA CODE": "bea_ind_code"},inplace=True)
    #print bea_ind_names.head(n=50)

    # Merge industry names to asset data
    bea_FA = pd.merge(bea_FA, bea_ind_names, how='inner', on=['bea_ind_code'],
      left_index=False, right_index=False, sort=False,
      copy=True)

    # Read in cross-walk between IRS and BEA Industries
    soi_bea_ind_codes = pd.read_csv(_SOI_BEA_CROSS, dtype={'bea_ind_code':str})
    soi_bea_ind_codes.drop('notes', axis=1, inplace=True)

    # Merge SOI codes to BEA data
    bea_FA = pd.merge(bea_FA, soi_bea_ind_codes, how='left', left_on=['bea_ind_code'],
      right_on=['bea_code'], left_index=False, right_index=False, sort=False,
      copy=True)

    return bea_FA

def inventories(soi_data):
    """Opens the BEA workbook and pulls out the asset info

        :param entity_dfs: Contains all the soi data by entity type
        :type entity_dfs: dictionary
        :returns: Fixed asset data organized by industry, entity, and asset type
        :rtype: dictionary
    """
    # Read in BEA fixed asset table
    # note I had to edit this by hand becaue of the subindustries under manufacturing
    # and wholesale trade.  not sure how to read those are unique names otherwise.
    bea_inventories = pd.read_excel(_BEA_INV, sheetname="Sheet0",skiprows=6, skip_footer=4)
    bea_inventories.reset_index()
    bea_inventories = bea_inventories[['Unnamed: 1','IV.1']].copy()
    bea_inventories.rename(columns={"Unnamed: 1":"bea_inv_name",
                               "IV.1": "BEA Inventories"},inplace=True)
    bea_inventories['bea_inv_name'] = bea_inventories['bea_inv_name'].str.strip()

    # Merge inventories data to SOI data
    bea_inventories = pd.merge(bea_inventories,soi_data,how='right', left_on=['bea_inv_name'],
      right_on=['bea_inv_name'], left_index=False, right_index=False, sort=False,
      copy=True,indicator=False)

    # attribute BEA inventories across SOI minor industries
    bea_inventories['bea_ratio'] = bea_inventories.groupby(['bea_inv_name'])['Inventories'].apply(lambda x: x/float(x.sum()))
    bea_inventories['BEA Inventories'] = bea_inventories['bea_ratio']*bea_inventories['BEA Inventories']
    # the above hit the bea control totals

    return bea_inventories

def land(soi_data):
    """Opens the BEA workbook and pulls out the asset info

        :param entity_dfs: Contains all the soi data by entity type
        :type entity_dfs: dictionary
        :returns: Fixed asset data organized by industry, entity, and asset type
        :rtype: dictionary
    """
    # for now, don't read in land data from excel file since too simple, but need to update this
    # what fin accounts data is this from??
    corp_land = 2875.0*_FIN_ACCT_FILE_FCTR
    noncorp_land = 13792.4*_FIN_ACCT_FILE_FCTR

    #read in BEA data on residential fixed assets
    bea_residential = pd.read_excel(_BEA_RES, sheetname="Sheet0",skiprows=5, skip_footer=2)
    bea_residential.reset_index()
    bea_residential = bea_residential[[u'\xa0','2013']].copy()
    bea_residential.rename(columns={u"\xa0":"entity_type",
                               "2013": "Fixed Assets"},inplace=True)
    bea_residential['Fixed Assets'] *= _FIN_ACCT_FILE_FCTR
    bea_residential['entity_type'] = bea_residential['entity_type'].str.strip()
    owner_occ_house_FA = np.array(bea_residential.ix[bea_residential['entity_type']=='Households','Fixed Assets'])
    corp_res_FA = np.array(bea_residential.ix[bea_residential['entity_type']=='Corporate','Fixed Assets'])
    noncorp_res_FA = np.array(bea_residential.ix[bea_residential['entity_type']=='Sole proprietorships and partnerships','Fixed Assets'])


    # read in Financial Accounts data on total value of real estate in
    # owner occ sector (includes land and structures)
    b101 = pd.read_csv(_B101_PATH,header=5)
    b101.reset_index()
    b101 = b101[['Unnamed: 0','2013']].copy()
    b101.rename(columns={"Unnamed: 0":"Variable",
                               "2013": "Value"},inplace=True)
    b101['Value'] *= _FIN_ACCT_FILE_FCTR
    b101['Variable'] = b101['Variable'].str.strip()
    owner_occ_house_RE = np.array(b101.ix[b101['Variable']=='Households; owner-occupied real estate including vacant land and mobile homes at market value','Value'])

    # compute value of land for owner occupied housing sector
    owner_occ_house_land = owner_occ_house_RE - owner_occ_house_FA

    # create dictionary for owner-occupied housing to be appended to
    # final dataset with all assets
    owner_occ_dict = {'minor_code_alt':531115,'entity_type':'owner_occupied_housing',
                      'tax_treat':'owner_occupied_housing','BEA Inventories':0.,
                      'BEA Fixed Assets':owner_occ_house_FA,
                      'BEA Land':owner_occ_house_land}

    # update amout of land for non-corporate sector
    noncorp_land -= owner_occ_house_land

    # attribute land across tax treatment and industry using SOI data
    soi_data.loc[:,'BEA Land'] = noncorp_land
    soi_data.ix[soi_data['entity_type']=='s_corp', 'BEA Land'] = corp_land
    soi_data.ix[soi_data['entity_type']=='c_corp', 'BEA Land'] = corp_land
    soi_data['BEA Corp'] = False
    soi_data.ix[soi_data['entity_type']=='s_corp', 'BEA Corp'] = True
    soi_data.ix[soi_data['entity_type']=='c_corp', 'BEA Corp'] = True

    soi_data['land_ratio'] = soi_data.groupby(['BEA Corp'])['Land'].apply(lambda x: x/float(x.sum()))
    soi_data['BEA Land'] = soi_data['land_ratio']*soi_data['BEA Land']

    # total land attributed above matches Fin Accts totals for non-owner occ housing

    # attribute residential fixed assets across tax treatment (they all got to
    # one specific production sector)
    soi_data.loc[:,'BEA Fixed Assets'] = 0.
    soi_data.loc[:,'BEA Res Assets'] = noncorp_res_FA
    soi_data.ix[soi_data['entity_type']=='s_corp', 'BEA Res Assets'] = corp_res_FA
    soi_data.ix[soi_data['entity_type']=='c_corp', 'BEA Res Assets'] = corp_res_FA
    soi_data['res_FA_ratio'] = soi_data.groupby(['BEA Corp','minor_code_alt'])['Land'].apply(lambda x: x/float(x.sum()))

    soi_data['BEA Res Assets'] = soi_data['res_FA_ratio']*soi_data['BEA Res Assets']
    # add to residential buidling realestate industry fixed assets only
    soi_data.ix[soi_data['minor_code_alt']==531115, 'BEA Fixed Assets'] += soi_data['BEA Res Assets']
    soi_data.to_csv('testDF.csv')
    quit()




    return bea_land
