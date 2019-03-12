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
land, res_assets, owner_occ_dict = read_bea.land(soi_data,
                                             fixed_assets)
# put all asset data together
asset_data = read_bea.combine(fixed_assets, inventories,
                          land, res_assets,
                          owner_occ_dict)
# save result to csv
asset_data.to_csv(os.path.join(_CUR_DIR, 'ccc_asset_data.csv'))
