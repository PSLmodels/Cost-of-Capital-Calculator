"""
Runner Script (run_btax.py):
-------------------------------------------------------------------------------
Initial module that contains the method to start the calculations in B-Tax. Makes function calls to split out fixed assets by entity type
(pull_soi_data), allocate fixed assets to industries (read_bea), grab all the parameters for the final calculations (get_params), and
calculate the Cost of Capital, Marginal Effective Tax Rates, and Marginal Effective Total Tax Rates (asset_calcs). Additionally, this
method compares the calculated values with those produced by the CBO.
Last updated: 7/25/2016.

"""
# Import packages
from collections import namedtuple
import cPickle as pickle
import numpy as np
import os.path
import pandas as pd
import sys

from btax.soi_processing import pull_soi_data
from btax import calc_final_outputs
from btax import check_output
from btax.util import (get_paths,
                       read_from_egg,
                       output_by_asset_to_json_table,
                       output_by_industry_to_json_table,
                       diff_two_tables,
                       filter_user_params_for_econ)
from btax import read_bea
import btax.soi_processing as soi
import btax.parameters as params
from btax import format_output
from btax import visuals
from btax import visuals_plotly

globals().update(get_paths())
TABLE_ORDER = ['base_output_by_asset',
               'reform_output_by_asset',
               'delta_output_by_asset',
               'base_output_by_industry',
               'reform_output_by_industry',
               'delta_output_by_industry',]
ModelDiffs = namedtuple('ModelDiffs', TABLE_ORDER)

def run_btax(**user_params):
    """Runner script that kicks off the calculations for B-Tax

	:param user_params: The user input for implementing reforms
	:type user_params: dictionary
	:returns: METR (by industry and asset) and METTR (by asset)
	:rtype: DataFrame
    """
    calc_assets = False
    if calc_assets:
        # get soi totals for assets
        soi_data = pull_soi_data()
        # read in the BEA data on fixed assets and separate them by corp and non-corp
        fixed_assets = read_bea.fixed_assets(soi_data)
        # read in BEA data on inventories and separate by corp and non-corp and industry
        inventories = read_bea.inventories(soi_data)
        # read in BEA data on land and separate by corp and non-corp and industry
        # this function also takes care of residential fixed assets
        # and the owner-occupied housing sector
        land, res_assets, owner_occ_dict = read_bea.land(soi_data, fixed_assets)
        # put all asset data together
        asset_data = read_bea.combine(fixed_assets,inventories,land,res_assets,owner_occ_dict)
    else:
        asset_data = pickle.load(open('asset_data.pkl', 'rb'))

    # get parameters
    parameters = params.get_params(**user_params)

    # make calculations by asset and create formated output
    output_by_asset = calc_final_outputs.asset_calcs(parameters,asset_data)
    pickle.dump( output_by_asset, open( "by_asset.pkl", "wb" ) )

    # make calculations by industry and create formated output
    output_by_industry = calc_final_outputs.industry_calcs(parameters, asset_data, output_by_asset)


    return output_by_asset, output_by_industry


def run_btax_with_baseline_delta(**user_params):
    econ_params = filter_user_params_for_econ(**user_params)
    base_output_by_asset, base_output_by_industry = run_btax(**econ_params)
    reform_output_by_asset, reform_output_by_industry = run_btax(**user_params)
    delta_output_by_asset = diff_two_tables(reform_output_by_asset,
                                            base_output_by_asset)
    delta_output_by_industry = diff_two_tables(reform_output_by_industry,
                                               base_output_by_industry)

    # create plots
    # by asset
    visuals.asset_crossfilter(base_output_by_asset,'baseline')
    visuals.asset_crossfilter(reform_output_by_asset,'reform')
    #visuals_plotly.asset_bubble(output_by_asset)

    # save output to csv - useful if run locally
    base_output_by_industry.to_csv('baseline_byindustry.csv',encoding='utf-8')
    reform_output_by_industry.to_csv('reform_byindustry.csv',encoding='utf-8')
    base_output_by_asset.to_csv('base_byasset.csv',encoding='utf-8')
    reform_output_by_asset.to_csv('reform_byasset.csv',encoding='utf-8')



    return ModelDiffs(base_output_by_asset,
                      reform_output_by_asset,
                      delta_output_by_asset,
                      base_output_by_industry,
                      reform_output_by_industry,
                      delta_output_by_industry)


def run_btax_to_json_tables(**user_params):
    out = run_btax_with_baseline_delta(**user_params)
    tables = {}
    for table_name, table in zip(TABLE_ORDER, out):
        if 'asset' in table_name:
            tables.update(output_by_asset_to_json_table(table, table_name))
        elif 'industry' in table_name:
            tables.update(output_by_industry_to_json_table(table, table_name))
        else:
            raise ValueError('Expected an "asset" or "industry" related table')
    return tables


def main():
    run_btax()

if __name__ == '__main__':
    main()
