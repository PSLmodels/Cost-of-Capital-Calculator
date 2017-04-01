"""
Fixed Asset Breakdown (check_asset_alloc.py):
-------------------------------------------------------------------------------

This script reads in BEA, SOI, and and Financial Accounts data.
It computes totals from these data and then compares those totals to
objects produced from run_btax.  Differences are printed to the screen.
In addition, a series of tables showing the split of assets between corporat
and non-corporate tax treatement across industry are produced
for comparison with similar tables from the CBO.

Last updated 10/05/2016
"""
# Packages:
from __future__ import print_function
import os.path
import numpy as np
import pandas as pd
import xlrd
import pickle
from btax.util import get_paths

# Directories:
globals().update(get_paths())

# Constant factors:
_BEA_IN_FILE_FCTR = 10**6
_BEA_INV_RES_FCTR = 10**9
_FIN_ACCT_FILE_FCTR = 10**9
_START_POS = 8
_SKIP1 = 47
_SKIP2 = 80
_CORP_PRT = [1, 2]
_NCORP_PRT = list(range(3, 11))


'''
Find totals to compare to
'''

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
bea_FA['bea_asset_code'] = bea_FA['bea_asset_code'].str.strip()
# Read in BEA asset names
bea_asset_names = pd.read_excel(_BEA_ASSET_PATH, sheetname="110C",
            header=5, converters={'Asset Codes': str})
bea_asset_names = bea_asset_names[['Asset Codes','NIPA Asset Types']]
bea_asset_names.dropna(subset = ['Asset Codes'],inplace=True)
bea_asset_names.rename(columns={"Asset Codes": "bea_asset_code",
                                "NIPA Asset Types": "Asset Type"},
                       inplace=True)
bea = bea_asset_names['bea_asset_code']
bea_asset_names['bea_asset_code'] = bea.str.strip()
bea = bea_asset_names['Asset Type']
bea_asset_names['Asset Type'] = bea.str.strip()
# Merge asset names to asset data - this will leave out subtotals for different
# categories (equipment, structure, IP)
bea_FA = pd.merge(bea_FA, bea_asset_names,
                  how='inner', on=['bea_asset_code'],
                  left_index=False, right_index=False, sort=False,
                  copy=True)
# find total
total_bea_FA = bea_FA['assets'].sum()



# read in BEA inventories data
bea_inventories = pd.read_excel(_BEA_INV,
                                sheetname="Sheet0",
                                skiprows=6,
                                skip_footer=4)
bea_inventories.reset_index()
bea_inventories = bea_inventories[['Unnamed: 1', 'IV.1']].copy()
bea_inventories.rename(columns={"Unnamed: 1":"bea_inv_name",
                                "IV.1": "BEA Inventories"}, inplace=True)
bea_inv = bea_inventories['bea_inv_name']
bea_inventories['bea_inv_name'] = bea_inv.str.strip()
bea_inv2 = bea_inventories['BEA Inventories']
bea_inventories['BEA Inventories'] = bea_inv2 * _BEA_INV_RES_FCTR
priv = bea_inventories['bea_inv_name'] == 'Private inventories 1'
total_bea_INV = bea_inventories.loc[priv, 'BEA Inventories'].values



# Get totals for land
# for now, don't read in land data from excel file since too simple, but need to update this
# what fin accounts data is this from??
corp_land = 2875.0 * _FIN_ACCT_FILE_FCTR
noncorp_land = 13792.4 * _FIN_ACCT_FILE_FCTR
total_finacct_LAND = corp_land + noncorp_land

# Get totals for residential assets
#read in BEA data on residential fixed assets
bea_residential = pd.read_excel(_BEA_RES, sheetname="Sheet0",
                                skiprows=5, skip_footer=2)
bea_residential.reset_index()
bea_residential = bea_residential[[u'\xa0','2013']].copy()
bea_residential.rename(columns={u"\xa0":"entity_type",
                                "2013": "Fixed Assets"},
                       inplace=True)
bea_residential['Fixed Assets'] *= _BEA_INV_RES_FCTR
bea_residential['entity_type'] = bea_residential['entity_type'].str.strip()
house = bea_residential['entity_type'] == 'Households'
owner_occ_house_FA = np.array(bea_residential.ix[house,'Fixed Assets'])
corp = bea_residential['entity_type']=='Corporate'
corp_res_FA = np.array(bea_residential.ix[corp,'Fixed Assets'])
sole = bea_residential['entity_type']=='Sole proprietorships and partnerships'
noncorp_res_FA = np.array(bea_residential.ix[sole,'Fixed Assets'])
total_bea_RES_FA = owner_occ_house_FA + corp_res_FA + noncorp_res_FA

# read in Financial Accounts data on total value of real estate in
# owner occ sector (includes land and structures)
b101 = pd.read_csv(_B101_PATH,header=5)
b101.reset_index()
b101 = b101[['Unnamed: 0','2013']].copy()
b101.rename(columns={"Unnamed: 0":"Variable",
                           "2013": "Value"},inplace=True)
b101['Value'] *= _FIN_ACCT_FILE_FCTR
b101['Variable'] = b101['Variable'].str.strip()
owner_occ_house_RE = np.array(b101.ix[b101['Variable']==
    'Households; owner-occupied real estate '
    'including vacant land and mobile homes at market value','Value'])

# compute value of land for owner occupied housing sector
owner_occ_house_land = owner_occ_house_RE - owner_occ_house_FA
print('Owner Occ housing land: ', owner_occ_house_land)
print('Owner Occ housing FAs: ', owner_occ_house_FA)
# update amout of land for non-corporate sector
noncorp_land -= owner_occ_house_land


'''
Read in asset pickle ued by B-Tax and compare totals
'''
asset_data = pickle.load(open('asset_data.pkl', 'rb'))
total_btax_assets = asset_data['assets'].sum()
land = asset_data['Asset Type'] == 'Land'
total_btax_LAND = asset_data.loc[land,'assets'].sum()
inv = asset_data['Asset Type']=='Inventories'
total_btax_INV = asset_data.loc[inv,'assets'].sum()
res = asset_data['Asset Type']=='Residential'
total_btax_RES_FA = asset_data.loc[res, 'assets'].sum()
total_btax_FA = total_btax_assets - total_btax_LAND - \
                total_btax_INV - total_btax_RES_FA
print('diff in FA: ', total_btax_RES_FA-total_bea_RES_FA)


'''
Print percentage differences between control totals and BTax data
'''
print('Diff in Non-residential Fixed Assets: ',
      (total_btax_FA-total_bea_FA)/total_bea_FA)
print('Diff in Land: ',
      (total_btax_LAND - total_finacct_LAND) / total_finacct_LAND)
print('Diff in Inventories: ',
      (total_btax_INV - total_bea_INV) / total_bea_INV)
print('Diff in Residential Fixed Assets: ',
      (total_btax_RES_FA - total_bea_RES_FA) / total_bea_RES_FA)

print("amount non-res fixed assets: ", total_btax_FA)
print("amount of land: ", total_btax_LAND)
print("amount of inventories: ", total_btax_INV)
print("amount of res fixed assets: ", total_btax_RES_FA)
print("diff in res fixed assets: ", total_btax_RES_FA - total_bea_RES_FA)
'''
Do differences in fixed assets by industry (the place where BEA data has detail)
'''
btax_FA = asset_data[asset_data['Asset Type'] != 'Land'].copy()
btax_FA = btax_FA[btax_FA['Asset Type'] != 'Inventories'].copy()
btax_FA = btax_FA[btax_FA['Asset Type'] != 'Land'].copy()
btax_FA = btax_FA[btax_FA['Asset Type'] != 'Residential'].copy()
bea_ind = pd.DataFrame(bea_FA.groupby('bea_ind_code').sum()).reset_index()
btax_ind = pd.DataFrame(btax_FA.groupby('bea_ind_code').sum()).reset_index()
FA_ind = pd.merge(bea_ind, btax_ind,
                  how='left', left_on=['bea_ind_code'],
                  right_on=['bea_ind_code'], left_index=False,
                  right_index=False, sort=False, copy=True)
FA_ind['difference'] = FA_ind['assets_x'] - FA_ind['assets_y']
FA_ind.to_csv('FixedAsset_DiffsByInd.csv', encoding='utf-8')


'''
Find shares of assets attributed to corp/non-corp by industry
'''
btax_FA['assets_nc'] = 0
btax_FA['assets_c'] = 0
non_corp = btax_FA['tax_treat']=='non-corporate'
btax_FA.loc[non_corp,'assets_nc']= btax_FA.loc[non_corp,'assets']
treat = btax_FA['tax_treat']=='corporate'
btax_FA.loc[treat,'assets_c']= btax_FA.loc[treat,'assets']
summ = btax_FA.groupby(['bea_ind_code'])['assets_c','assets_nc','assets'].sum()
shares_corp_non = pd.DataFrame(summ).reset_index()
shares_corp_non['Corp Share'] = shares_corp_non['assets_c']/\
                                (shares_corp_non['assets_c'] + \
                                 shares_corp_non['assets_nc'])
shares_corp_non['Non-corp Share'] = shares_corp_non['assets_nc'] / \
                                    (shares_corp_non['assets_c'] + \
                                     shares_corp_non['assets_nc'])
shares_corp_non['check'] = (shares_corp_non['assets_c'] + \
                            shares_corp_non['assets_nc']) - \
                            shares_corp_non['assets']
# merge in industry names
df3 = asset_data[['Industry','bea_ind_code']].copy()
df3.drop_duplicates(inplace=True)
shares_corp_non = pd.merge(shares_corp_non, df3,
                           how='left', left_on=['bea_ind_code'],
                           right_on=['bea_ind_code'], left_index=False,
                           right_index=False, sort=False, copy=True)
shares_corp_non['Industry'] = shares_corp_non['Industry'].str.strip()
# save to csv to look over/compare with CBO
shares_corp_non.to_csv('shares_corp_non.csv',encoding='utf-8')

'''
Find shares of assets attributed to corp/non-corp partnerships by industry
'''
not_land = asset_data['Asset Type'] != 'Land'
btax_FA = asset_data[not_land].copy()
btax_part_FA = btax_FA[btax_FA['entity_type'] == 'partnership'].copy()
not_inv = btax_part_FA['Asset Type'] != 'Inventories'
btax_part_FA = btax_part_FA[not_inv].copy()
btax_part_FA = btax_part_FA[not_land].copy()
not_resid = btax_part_FA['Asset Type'] != 'Residential'
btax_part_FA = btax_part_FA[not_resid].copy()
btax_part_FA['assets_nc'] = 0
btax_part_FA['assets_c'] = 0
non_corp = btax_part_FA['tax_treat']=='non-corporate'
btax_part_FA.loc[non_corp,'assets_nc']= btax_part_FA.loc[non_corp,'assets']
corp = btax_part_FA['tax_treat'] == 'corporate'
btax_part_FA.loc[corp, 'assets_c'] = btax_part_FA.loc[corp, 'assets']
# shares_corp_non = pd.DataFrame({btax_FA.groupby(
#     ['bea_ind_code'])['assets_c','assets_nc','assets'].sum()}).reset_index()
gr = btax_part_FA.groupby(['bea_ind_code']
                          )['assets_c','assets_nc','assets'].sum()
part_corp_non = pd.DataFrame(gr).reset_index()
part_corp_non['Corp Share'] = part_corp_non['assets_c'] / \
                              (part_corp_non['assets_c'] + \
                               part_corp_non['assets_nc'])
part_corp_non['Non-corp Share'] = part_corp_non['assets_nc'] / \
                                  (part_corp_non['assets_c'] + \
                                   part_corp_non['assets_nc'])
part_corp_non['check'] = (part_corp_non['assets_c'] + \
                          part_corp_non['assets_nc']) - part_corp_non['assets']
# merge in industry names
df3 = asset_data[['Industry','bea_ind_code']].copy()
df3.drop_duplicates(inplace=True)
part_corp_non = pd.merge(part_corp_non, df3,
                         how='left', left_on=['bea_ind_code'],
                         right_on=['bea_ind_code'],
                         left_index=False, right_index=False,
                         sort=False, copy=True)
part_corp_non['Industry'] = part_corp_non['Industry'].str.strip()
# save to csv to look over/compare with CBO
part_corp_non.to_csv('part_corp_non.csv', encoding='utf-8')
