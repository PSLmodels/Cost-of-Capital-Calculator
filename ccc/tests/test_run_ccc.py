import pytest
import os
import numbers
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import ccc
from ccc.parameters import Specification, AssetParams
from ccc.calculator import Calculator
from ccc.data import Assets


TDIR = os.path.abspath(os.path.dirname(__file__))


def test_calc_by_methods():
    """
    Test the Calculator calc_by_asset and calc_by_industry methods by
    comparing actual and expect dataframes
    """
    # execute Calculator calc_by methods to get actual results
    p = Specification()
    dp = AssetParams()
    assets = Assets()
    calc = Calculator(p, dp, assets)
    actual_by_asset = calc.calc_by_asset()
    actual_by_industry = calc.calc_by_industry()
    # load expected results from the calc_by_ methods
    expect_by_asset = pd.read_json(
        os.path.join(TDIR, 'run_ccc_asset_output.json')
    )
    expect_by_industry = pd.read_json(
        os.path.join(TDIR, 'run_ccc_industry_output.json')
    )
    # compare the actual and expect DataFrames
    for actual_df, expect_df in zip([actual_by_asset, actual_by_industry],
                                    [expect_by_asset, expect_by_industry]):
        actual_df.sort_index(inplace=True)
        actual_df.reset_index(inplace=True)
        expect_df.sort_index(inplace=True)
        expect_df.reset_index(inplace=True)
        assert tuple(actual_df.columns) == tuple(expect_df.columns)
        for col in expect_df.columns:
            try:
                example = getattr(actual_df, col).iloc[0]
                can_diff = isinstance(example, numbers.Number)
                if can_diff:
                    assert np.allclose(actual_df[col].values,
                                       expect_df[col].values, atol=1e-5)
                else:
                    pass
            except AttributeError:
                pass


def test_example_output():
    """
    Test that can produce expected output from code in ../../example.py script
    """
    # execute code as found in ../../example.py script
    cyr = 2019
    # ... specify baseline and reform Calculator objects
    assets = Assets()
    dp = AssetParams()
    baseline_parameters = Specification(year=cyr)
    calc1 = Calculator(baseline_parameters, dp, assets)
    reform_parameters = Specification(year=cyr)
    business_tax_adjustments = {
        'CIT_rate': 0.35, 'BonusDeprec_3yr': 0.50, 'BonusDeprec_5yr': 0.50,
        'BonusDeprec_7yr': 0.50, 'BonusDeprec_10yr': 0.50,
        'BonusDeprec_15yr': 0.50, 'BonusDeprec_20yr': 0.50}
    reform_parameters.update_specification(business_tax_adjustments)
    calc2 = Calculator(reform_parameters, dp, assets)
    # ... calculation by asset and by industry
    baseline_assets_df = calc1.calc_by_asset()
    reform_assets_df = calc2.calc_by_asset()
    baseline_industry_df = calc1.calc_by_industry()
    reform_industry_df = calc2.calc_by_industry()
    diff_assets_df = ccc.utils.diff_two_tables(reform_assets_df,
                                               baseline_assets_df)
    diff_industry_df = ccc.utils.diff_two_tables(reform_industry_df,
                                                 baseline_industry_df)
    # ... save calculated results as csv files in ccc/test directory
    baseline_industry_df.to_csv(os.path.join(TDIR, 'baseline_byindustry.csv'),
                                float_format='%.5f')
    reform_industry_df.to_csv(os.path.join(TDIR, 'reform_byindustry.csv'),
                              float_format='%.5f')
    baseline_assets_df.to_csv(os.path.join(TDIR, 'baseline_byasset.csv'),
                              float_format='%.5f')
    reform_assets_df.to_csv(os.path.join(TDIR, 'reform_byasset.csv'),
                            float_format='%.5f')
    diff_industry_df.to_csv(os.path.join(TDIR, 'changed_byindustry.csv'),
                            float_format='%.5f')
    diff_assets_df.to_csv(os.path.join(TDIR, 'changed_byasset.csv'),
                          float_format='%.5f')
    # compare actual calculated results to expected results
    failmsg = ''
    expect_output_dir = os.path.join(TDIR, '..', '..', 'example_output')
    for fname in ['baseline_byasset', 'baseline_byindustry',
                  'reform_byasset', 'reform_byindustry',
                  'changed_byasset', 'changed_byindustry']:
        actual_path = os.path.join(TDIR, fname + '.csv')
        actual_df = pd.read_csv(actual_path)
        expect_path = os.path.join(expect_output_dir, fname + '_expected.csv')
        expect_df = pd.read_csv(expect_path)
        try:
            assert_frame_equal(actual_df, expect_df)
            # cleanup actual results if it has same  contents as expected file
            os.remove(actual_path)
        except AssertionError:
            failmsg += 'ACTUAL-vs-EXPECT DIFFERENCES FOR {}\n'.format(fname)
    if failmsg:
        raise AssertionError('\n' + failmsg)
