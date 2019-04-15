"""
This script creates the asset_data.csv file that will be read into the
Asset object in CCC.
"""

# Import packages
import os.path
import sys
import numpy as np
import pandas as pd
from ccc.utils import (get_paths,
                       read_from_egg,
                       diff_two_tables,
                       filter_user_params_for_econ)
import read_bea
from soi_processing import pull_soi_data
import pull_depreciation
from ccc.constants import MAJOR_ASSET_GROUPS, BEA_CODE_DICT
globals().update(get_paths())


# get soi totals for assets
soi_data = pull_soi_data()
# read in the BEA data on fixed assets and separate them by
# corp and non-corp
fixed_assets = read_bea.fixed_assets(soi_data)
# read in BEA data on inventories and separate by corp and
# non-corp and industry
inventories = read_bea.inventories(soi_data)
# read in BEA data on land and separate by corp and non-corp
# and industry
# this function also takes care of residential fixed assets
# and the owner-occupied housing sector
land, res_assets, owner_occ_dict = read_bea.land(
    soi_data, fixed_assets)
# put all asset data together
asset_data = read_bea.combine(
    fixed_assets, inventories, land, res_assets, owner_occ_dict)
# collapse over different entity types and just get the sum of corporate
# and non-corporate by industry and asset type
asset_data_by_tax_treat = pd.DataFrame(asset_data.groupby(
    ['tax_treat', 'Asset Type', 'assets', 'bea_asset_code',
     'bea_ind_code', 'Industry', 'minor_code_alt']).sum()).reset_index()
asset_data_by_tax_treat.drop(columns=['level_0', 'index'], inplace=True)
# Merge in major industry and asset grouping names...
# Add major asset group
asset_data_by_tax_treat['major_asset_group'] =\
    asset_data_by_tax_treat['Asset Type']
asset_data_by_tax_treat['major_asset_group'].replace(MAJOR_ASSET_GROUPS,
                                                     inplace=True)
# Add major industry groupings
asset_data_by_tax_treat['Industry'] =\
    asset_data_by_tax_treat['Industry'].str.strip()
asset_data_by_tax_treat['major_industry'] =\
    asset_data_by_tax_treat['bea_ind_code']
asset_data_by_tax_treat['major_industry'].replace(BEA_CODE_DICT,
                                                  inplace=True)
# Merge in economic depreciation rates and tax depreciation systems
deprec_info = pull_depreciation.get_depr()
asset_data_by_tax_treat = asset_data_by_tax_treat.merge(
    deprec_info, on='bea_asset_code', how='left', copy=True)

# Give land and inventories depreciation info?

# clean up
asset_data_by_tax_treat.drop(columns=['Asset Type_x', 'Asset Type_y'],
                             inplace=True)
asset_data_by_tax_treat.rename(
    columns={"Asset": "asset_name"}, inplace=True)

# save result to csv
asset_data_by_tax_treat.to_csv(os.path.join(_CUR_DIR,
                                            'ccc_asset_data.csv'))
