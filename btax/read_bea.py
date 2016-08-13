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
_START_POS = 8
_SKIP1 = 47
_SKIP2 = 80
_CORP_PRT = [1,2]
_NCORP_PRT = [3,4,5,6,7,8,9,10]


def read_bea():
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
