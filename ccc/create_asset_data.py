"""
This script creates the asset_data.csv file that will be read into the
Asset object in CCC.
"""

# Import packages
import os.path
import sys
import numpy as np
import pandas as pd
from ccc.soi_processing import pull_soi_data
from ccc import calc_final_outputs
from ccc import check_output
from ccc.utils import (get_paths,
                       read_from_egg,
                       diff_two_tables,
                       filter_user_params_for_econ)
from ccc import read_bea
import ccc.soi_processing as soi
from ccc.utils import get_paths
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
    by=['tax_treat', 'Asset Type', 'assets', 'bea_asset_code',
        'bea_ind_code', 'minor_code_alt'],
    as_index=False)['assets'].sum()).reset_index()
# Merge in major industry and asset grouping names...
# Add major asset groups
#     output_by_asset['major_asset_group'] = output_by_asset['Asset Type']
#     output_by_asset['major_asset_group'].replace(major_asset_groups,
#                                                  inplace=True)
# # Add major industry groupings
#     by_industry_asset['Industry'] = by_industry_asset['Industry'].str.strip()
#     by_industry_asset['major_industry'] = by_industry_asset['bea_ind_code']
#     by_industry_asset['major_industry'].replace(bea_code_dict, inplace=True)
# save result to csv
asset_data_by_tax_treat.to_csv(os.path.join(_CUR_DIR,
                                            'ccc_asset_data.csv'))
