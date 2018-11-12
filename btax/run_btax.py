"""
Runner Script (run_btax.py):
------------------------------------------------------------------------
Initial module that contains the method to start the calculations in
B-Tax. Makes function calls to split out fixed assets by entity type
(pull_soi_data), allocate fixed assets to industries (read_bea), grab
all the parameters for the final calculations (get_params), and
calculate the Cost of Capital, Marginal Effective Tax Rates, and
Marginal Effective Total Tax Rates (asset_calcs). Additionally, this
method compares the calculated values with those produced by the CBO.

"""

# Import packages
from __future__ import unicode_literals
from collections import namedtuple, defaultdict
try:
    import cPickle as pickle
except ImportError:
    import pickle
from functools import partial
import os.path
import sys

import numpy as np
import pandas as pd

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
from btax.front_end_util import (runner_json_tables,
                                 replace_unicode_spaces)
from btax.util import DEFAULT_START_YEAR

globals().update(get_paths())
TABLE_ORDER = ['base_output_by_asset', 'reform_output_by_asset',
               'changed_output_by_asset', 'base_output_by_industry',
               'reform_output_by_industry',
               'changed_output_by_industry']

ModelDiffs = namedtuple('ModelDiffs', TABLE_ORDER + ['row_grouping'])

ASSET_PRE_CACHE_FILE = 'asset_data.pkl'


def run_btax(test_run, baseline=False, start_year=DEFAULT_START_YEAR,
             iit_reform=None, data=None, **user_params):
    """
    Runner script that kicks off the calculations for B-Tax

    Args:
        test_run: boolean, True if test run (doesn't use puf.csv)
        baseline: boolean, True if run with current law parameters
        start_year: integer, tax year METRs computed for
        iit_reform: dictionary, reform to pass to Tax-Calculator
        user_params: dictionary, user defined parametesr for B-Tax

    Returns:
        output_by_asset: dataframe, output variables for all assets
        output_by_industry: dataframe, output variables for all industries

    """
    calc_assets = False
    iit_reform = iit_reform or {}
    asset_data = None
    for repeat in range(2):
        if calc_assets or not os.path.exists(ASSET_PRE_CACHE_FILE):
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
            # save result to pickle so don't have to do this everytime
            print('Dump', ASSET_PRE_CACHE_FILE)
            pickle.dump(asset_data, open(ASSET_PRE_CACHE_FILE, "wb"))
        else:
            try:
                asset_data = pickle.load(open(ASSET_PRE_CACHE_FILE, 'rb'))
                print('Loaded', ASSET_PRE_CACHE_FILE)
                break
            except Exception as e:
                if os.path.exists(ASSET_PRE_CACHE_FILE):
                    print('Remove', ASSET_PRE_CACHE_FILE)
                    os.remove(ASSET_PRE_CACHE_FILE)
    if asset_data is None:
        raise
    # get parameters
    parameters = params.get_params(test_run, baseline, start_year,
                                   iit_reform, data, **user_params)

    # make calculations by asset and create formated output
    output_by_asset = calc_final_outputs.asset_calcs(parameters,
                                                     asset_data)

    # make calculations by industry and create formated output
    output_by_industry = calc_final_outputs.industry_calcs(parameters,
                                                           asset_data,
                                                           output_by_asset)

    return output_by_asset, output_by_industry


def run_btax_with_baseline_delta(test_run,
                                 start_year=DEFAULT_START_YEAR,
                                 iit_reform=None, data=None,
                                 **user_params):
    """
    Runner script that kicks off the calculations for B-Tax

    Args:
        test_run: boolean, True if test run (doesn't use puf.csv)
        start_year: interger, tax year METRs computed for
        iit_reform: dictionary, reform to pass to Tax-Calculator
        user_params: dictionary, user defined parametesr for B-Tax

    Returns:
        ModelDiffs: tuple, contains 6 dataframes for output by asset and
                    industry for baseline, refor, and difference

    """

    econ_params = filter_user_params_for_econ(**user_params)
    base_output_by_asset, base_output_by_industry = \
        run_btax(test_run, True, start_year, {}, data=data, **econ_params)
    asset_row_grouping = {}
    subset = zip(*(getattr(base_output_by_asset, at) for at in
                   ('Asset', 'asset_category', 'mettr_c', 'mettr_nc')))
    for asset, cat, mettr_c, mettr_nc in subset:
        if cat != cat:  # A string column that may have NaN, so can't do isnan
            cat = asset  # These are some summary rows that don't have all info
        asset, cat = map(replace_unicode_spaces, (asset, cat))
        asset_row_grouping[cat] = asset_row_grouping[asset] =\
            {'major_grouping': cat, 'summary_c': mettr_c,
             'summary_nc': mettr_nc, }
    industry_row_grouping = {}
    subset = zip(*(getattr(base_output_by_industry, at) for at in
                   ('Industry', 'major_industry', 'mettr_c', 'mettr_nc')))
    for industry, cat, mettr_c, mettr_nc in subset:
        industry, cat = map(replace_unicode_spaces, (industry, cat))
        industry_row_grouping[cat] = industry_row_grouping[industry] =\
            {'major_grouping': cat, 'summary_c': mettr_c,
             'summary_nc': mettr_nc, }
    row_grouping = {'asset': asset_row_grouping,
                    'industry': industry_row_grouping}
    reform_output_by_asset, reform_output_by_industry =\
        run_btax(test_run, False, start_year, iit_reform, data=data, **user_params)
    changed_output_by_asset =\
        diff_two_tables(reform_output_by_asset, base_output_by_asset)
    changed_output_by_industry =\
        diff_two_tables(reform_output_by_industry, base_output_by_industry)

    # save output to csv - useful if run locally
    base_output_by_industry.to_csv('baseline_byindustry.csv',
                                   encoding='utf-8')
    reform_output_by_industry.to_csv('reform_byindustry.csv',
                                     encoding='utf-8')
    base_output_by_asset.to_csv('baseline_byasset.csv', encoding='utf-8')
    reform_output_by_asset.to_csv('reform_byasset.csv',
                                  encoding='utf-8')
    changed_output_by_industry.to_csv('changed_byindustry.csv',
                                      encoding='utf-8')
    changed_output_by_asset.to_csv('changed_byasset.csv',
                                   encoding='utf-8')

    return ModelDiffs(base_output_by_asset, reform_output_by_asset,
                      changed_output_by_asset, base_output_by_industry,
                      reform_output_by_industry,
                      changed_output_by_industry, row_grouping)


def main():
    run_btax()


if __name__ == '__main__':
    main()
