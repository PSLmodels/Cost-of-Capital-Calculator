import pytest
import os
import pandas as pd
import numpy as np
import numbers
import subprocess
from pandas.testing import assert_frame_equal
from ccc.parameters import Specifications
from ccc.calculator import Calculator
from ccc.data import Assets

CUR_PATH = os.path.abspath(os.path.dirname(__file__))

# Load input values
p = Specifications()
assets = Assets()
calc1 = Calculator(p, assets)
# Compute results
test_by_asset = calc1.calc_by_asset()
test_by_industry = calc1.calc_by_industry()
# Load expected results
result_by_asset = pd.read_json(os.path.join(
    CUR_PATH, 'run_ccc_asset_output.json'))
result_by_industry = pd.read_json(os.path.join(
    CUR_PATH, 'run_ccc_industry_output.json'))


@pytest.mark.parametrize('test_df,expected_df',
                         [(test_by_asset, result_by_asset),
                          (test_by_industry, result_by_industry)],
                         ids=['by assset', 'by industry'])
def test_run_ccc(test_df, expected_df):
    # Test the run_ccc.run_ccc() function by reading in inputs and
    # confirming that output variables have the same values.
    test_df.sort_index(inplace=True)
    test_df.reset_index(inplace=True)
    expected_df.sort_index(inplace=True)
    expected_df.reset_index(inplace=True)
    assert tuple(test_df.columns) == tuple(expected_df.columns)
    for c in expected_df.columns:
        try:
            example = getattr(test_df, c).iloc[0]
            can_diff = isinstance(example, numbers.Number)
            if can_diff:
                assert np.allclose(test_df[c].values,
                                   expected_df[c].values, atol=1e-5)
            else:
                pass
        except AttributeError:
            pass


def test_run_ccc_example():
    '''
    Test that the example script runs
    '''
    run_example_path = os.path.join(CUR_PATH, '..', '..', 'run_examples')
    subprocess.call('cd ' + run_example_path +
                    ' ; python run_ccc_example.py', shell=True)


@pytest.mark.local
@pytest.mark.parametrize(
    'file_name', ['baseline_byindustry', 'baseline_byasset',
                  'reform_byindustry', 'reform_byasset',
                  'changed_byindustry', 'changed_byasset'],
    ids=['baseline by industry', 'baseline by asset',
         'reform by industry', 'reform by asset', 'changed by industry',
         'changed by asset'])
def test_run_ccc_example_output(file_name):
    '''
    Tests the script in ../../run_examples/run_ccc_example.py to
    ensure that it produces the expected results that are checked into
    the repo.
    '''
    run_example_path = os.path.join(CUR_PATH, '..', '..', 'run_examples')
    test_path = os.path.join(run_example_path, file_name + '.csv')
    test_df = pd.read_csv(test_path)
    expected_path = os.path.join(run_example_path, file_name +
                                 '_expected.csv')
    expected_df = pd.read_csv(expected_path)
    assert_frame_equal(test_df, expected_df)
