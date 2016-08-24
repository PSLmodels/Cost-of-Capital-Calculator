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
import os.path
import sys
import pandas as pd
import numpy as np
import cPickle as pickle
from btax.soi_processing import pull_soi_data
from btax import calc_final_outputs
from btax import check_output
from btax.util import (get_paths, read_from_egg,
                       output_by_asset_to_json_table,
                       output_by_industry_to_json_table)
from btax import read_bea
import btax.soi_processing as soi
import btax.parameters as params
from btax import format_output
from btax import visuals
from btax import visuals_plotly

globals().update(get_paths())

def run_btax(**user_params):
    """Runner script that kicks off the calculations for B-Tax

	:param user_params: The user input for implementing reforms
	:type user_params: dictionary
	:returns: METR (by industry and asset) and METTR (by asset)
	:rtype: DataFrame
    """
    # get soi totals for assets
    soi_data = pull_soi_data()

    # read in the BEA data on fixed assets and separate them by corp and non-corp
    fixed_assets = read_bea.fixed_assets(soi_data)

    # read in BEA data on inventories and separate by corp and non-corp and industry
    inventories = read_bea.inventories(soi_data)

    # read in BEA data on land and separate by corp and non-corp and industry
    # this function also takes care of residential fixed assets
    land, fixed_assets = read_bea.land(soi_data, bea_FA)

    # get parameters
    parameters = params.get_params(**user_params)


    # make calculations by asset and create formated output
    output_by_asset = calc_final_outputs.asset_calcs(parameters,fixed_assets)
    output_by_asset.to_csv('testDF.csv',encoding='utf-8')
    pickle.dump( output_by_asset, open( "by_asset.pkl", "wb" ) )

    # check against CBO
    format_output.CBO_compare(output_by_asset)

    # make calculations by industry and create formated output
    output_by_industry = calc_final_outputs.industry_calcs(parameters, fixed_assets, output_by_asset)


    # create plots
    # by asset
    visuals.asset_crossfilter(output_by_asset)
    #visuals_plotly.asset_bubble(output_by_asset)

    # print output_by_industry.head(n=50)

    return output_by_asset, output_by_industry


def run_btax_to_json_tables(**user_params):
    output_by_asset, output_by_industry = run_btax(**user_params)
    tables = output_by_asset_to_json_table(output_by_asset)
    tables.update(output_by_industry_to_json_table(output_by_industry))
    return tables


def main():
    run_btax()

if __name__ == '__main__':
    main()
