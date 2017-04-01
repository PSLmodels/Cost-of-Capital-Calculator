"""
Runner Script (run_btax.py):
-------------------------------------------------------------------------------
Initial module that contains the method to start the calculations in B-Tax.
Makes function calls to split out fixed assets by entity type
(pull_soi_data), allocate fixed assets to industries (read_bea),
grab all the parameters for the final calculations (get_params), and
calculate the Cost of Capital, Marginal Effective Tax Rates, and Marginal
Effective Total Tax Rates (asset_calcs). Additionally, this method compares
the calculated values with those produced by the CBO.
Last updated: 7/25/2016.

"""
# Import packages
from __future__ import unicode_literals
from collections import namedtuple, defaultdict
try:
    import cPickle as pickle
except ImportError:
    import pickle
from functools import partial
import numpy as np
import os.path
import pandas as pd
import sys

from btax.soi_processing import pull_soi_data
from btax import calc_final_outputs
from btax import check_output
from btax.util import (get_paths,
                       read_from_egg,
                       diff_two_tables,
                       filter_user_params_for_econ)
from btax import read_bea
import btax.soi_processing as soi
import btax.parameters as params
from btax import format_output
from btax import visuals
from btax import visuals_plotly
from btax.front_end_util import (runner_json_tables,
                                 replace_unicode_spaces)
from btax.util import DEFAULT_START_YEAR
from btax.run_btax import run_btax, RESULTS_TO_CSV

globals().update(get_paths())
TABLE_ORDER = ['base_output_by_asset',
               'reform_output_by_asset',
               'changed_output_by_asset',
               'base_output_by_industry',
               'reform_output_by_industry',
               'changed_output_by_industry',]

ModelDiffs = namedtuple('ModelDiffs', TABLE_ORDER + ['row_grouping'])

ASSET_PRE_CACHE_FILE = 'asset_data.pkl'



def runner(test_run,start_year,iit_reform,**user_params):
    econ_params = filter_user_params_for_econ(**user_params)
    base_output_by_asset, base_output_by_industry = run_btax(test_run,
                                                             True,
                                                             start_year,
                                                             {},
                                                             **econ_params)
    asset_row_grouping = {}
    asset_cols = ('Asset', 'asset_category', 'mettr_c', 'mettr_nc')
    subset = zip(*(getattr(base_output_by_asset, at) for at in asset_cols))
    for asset, cat, mettr_c, mettr_nc in subset:
        # A string column that may have NaN, so can't do isnan()
        # These are some summary rows that don't have all info
        if cat != cat:
            cat = asset
        asset, cat = map(replace_unicode_spaces, (asset, cat))
        item = {'major_grouping': cat,
                'summary_c': mettr_c,
                'summary_nc': mettr_nc,}
        asset_row_grouping[cat] = asset_row_grouping[asset] = item
    industry_row_grouping = {}
    inds = ('Industry', 'major_industry', 'mettr_c', 'mettr_nc')
    subset = zip(*(getattr(base_output_by_industry, at) for at in inds))
    for industry, cat, mettr_c, mettr_nc in subset:
        industry, cat = map(replace_unicode_spaces, (industry, cat))
        item = {'major_grouping': cat,
                'summary_c': mettr_c,
                'summary_nc': mettr_nc,}
        industry_row_grouping[cat] = industry_row_grouping[industry] = item
    row_grouping = {'asset': asset_row_grouping,
                    'industry': industry_row_grouping}
    reform_output_by_asset, reform_output_by_industry = run_btax(test_run,
                                                                 False,
                                                                 start_year,
                                                                 iit_reform,
                                                                 **user_params)
    changed_output_by_asset = diff_two_tables(reform_output_by_asset,
                                            base_output_by_asset)
    changed_output_by_industry = diff_two_tables(reform_output_by_industry,
                                               base_output_by_industry)

    # create plots
    # by asset
    #visuals.asset_crossfilter(base_output_by_asset,'baseline')
    #visuals.asset_crossfilter(reform_output_by_asset,'reform')
    #visuals_plotly.asset_bubble(output_by_asset)

    # save output to csv - useful if run locally
    if RESULTS_TO_CSV:
        # set BTAX_TABLES_TO_CSV=1 to get these CSV files
        # (to set RESULTS_TO_CSV to True)
        base_output_by_industry.to_csv('baseline_byindustry.csv',encoding='utf-8')
        reform_output_by_industry.to_csv('reform_byindustry.csv',encoding='utf-8')
        base_output_by_asset.to_csv('base_byasset.csv',encoding='utf-8')
        reform_output_by_asset.to_csv('reform_byasset.csv',encoding='utf-8')



    return ModelDiffs(base_output_by_asset,
                      reform_output_by_asset,
                      changed_output_by_asset,
                      base_output_by_industry,
                      reform_output_by_industry,
                      changed_output_by_industry,
                      row_grouping)




def main():
    run_btax()

if __name__ == '__main__':
    main()
