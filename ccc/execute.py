"""
Runner Script (run_ccc.py):
------------------------------------------------------------------------
Initial module that contains the method to start the calculations in
Cost-of-Capital-Calculator. Makes function calls to split out fixed assets by entity type
(pull_soi_data), allocate fixed assets to industries (read_bea), grab
all the parameters for the final calculations (get_params), and
calculate the Cost of Capital, Marginal Effective Tax Rates, and
Marginal Effective Total Tax Rates (asset_calcs). Additionally, this
method compares the calculated values with those produced by the CBO.
"""
# Import packages
from __future__ import unicode_literals
from collections import namedtuple
from ccc.util import (get_paths, diff_two_tables,
                       filter_user_params_for_econ)
from ccc.front_end_util import replace_unicode_spaces
from ccc.run_ccc import run_ccc

globals().update(get_paths())
TABLE_ORDER = ['base_output_by_asset', 'reform_output_by_asset',
               'changed_output_by_asset', 'base_output_by_industry',
               'reform_output_by_industry',
               'changed_output_by_industry']
ModelDiffs = namedtuple('ModelDiffs', TABLE_ORDER + ['row_grouping'])
ASSET_PRE_CACHE_FILE = 'asset_data.pkl'


def runner(test_run, start_year, iit_reform, **user_params):
    """
    Runs Cost-of-Capital-Calculator, computing results for a baseline and reform and then
    the differnece between the two.

    Args:
        test_run: boolean, indicator for if this is a test run or not
        start_year: integer, year to start Tax-Calculator and year of
                    business income tax parameters to use
        iit_reform: dictionary, tax parameters to pass to Tax-calculator
                    for reform policies
        user_params: dictionary, user-defined parameter values

    Returns:
        ModelDiffs: namedtuple, tuple with 7 objects, 6 DataFrames of
                    results and list of groupings for rows
    """
    econ_params = filter_user_params_for_econ(**user_params)
    base_output_by_asset, base_output_by_industry =\
        run_ccc(test_run, True, start_year, {}, **econ_params)
    asset_row_grouping = {}
    subset = zip(*(getattr(base_output_by_asset, at) for at in
                   ('Asset', 'asset_category', 'mettr_c', 'mettr_nc')))
    for asset, cat, mettr_c, mettr_nc in subset:
        if cat != cat:  # A string column that may have NaN, so can't do isnan()
            cat = asset  # These are some summary rows that don't have all info
        asset, cat = map(replace_unicode_spaces, (asset, cat))
        asset_row_grouping[cat] = asset_row_grouping[asset] =\
            {'major_grouping': cat, 'summary_c': mettr_c,
             'summary_nc': mettr_nc}
    industry_row_grouping = {}
    subset = zip(*(getattr(base_output_by_industry, at) for at in
                   ('Industry', 'major_industry', 'mettr_c', 'mettr_nc')))
    for industry, cat, mettr_c, mettr_nc in subset:
        industry, cat = map(replace_unicode_spaces, (industry, cat))
        industry_row_grouping[cat] = industry_row_grouping[industry] =\
            {'major_grouping': cat, 'summary_c': mettr_c,
             'summary_nc': mettr_nc}
    row_grouping = {'asset': asset_row_grouping,
                    'industry': industry_row_grouping}
    reform_output_by_asset, reform_output_by_industry =\
        run_ccc(test_run, False, start_year, iit_reform, **user_params)
    changed_output_by_asset = diff_two_tables(reform_output_by_asset,
                                              base_output_by_asset)
    changed_output_by_industry = diff_two_tables(reform_output_by_industry,
                                                 base_output_by_industry)

    return ModelDiffs(base_output_by_asset, reform_output_by_asset,
                      changed_output_by_asset, base_output_by_industry,
                      reform_output_by_industry,
                      changed_output_by_industry, row_grouping)


def main():
    run_ccc()


if __name__ == '__main__':
    main()
