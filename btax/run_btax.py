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
from collections import namedtuple, OrderedDict
import cPickle as pickle
import numbers
import numpy as np
import os.path
import pandas as pd
import sys

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
    # break out the asset data by entity type (c corp, s corp, sole proprietorships, and partners)
    #entity_dfs = pull_soi_data()

    # get parameters
    parameters = params.get_params(**user_params)

    # read in the BEA data on fixed assets and separate them by corp and non-corp
    fixed_assets = read_bea.read_bea()

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


def _diff_two_tables(df1, df2):
    assert tuple(df1.columns) == tuple(df2.columns)
    diffs = OrderedDict()
    for c in df1.columns:
        example = getattr(df1, c).iloc[0]
        can_diff = isinstance(example, numbers.Number)
        if can_diff:
            diffs[c] = getattr(df1, c) - getattr(df2, c)
        else:
            diffs[c] = getattr(df1, c)
    return pd.DataFrame(diffs)


def run_btax_with_baseline_delta(**user_params):
    base_output_by_asset, base_output_by_industry = run_btax()
    reform_output_by_asset, reform_output_by_industry = run_btax(**user_params)
    delta_output_by_asset = _diff_two_tables(reform_output_by_asset,
                                             base_output_by_asset)
    delta_output_by_industry = _diff_two_tables(reform_output_by_industry,
                                                base_output_by_industry)
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
