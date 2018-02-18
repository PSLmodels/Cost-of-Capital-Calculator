import pytest
import os
import pickle
import pandas as pd
from pandas.testing import assert_frame_equal
from btax import run_btax
os.path.abspath(os.path.dirname(__file__))

CUR_PATH = os.path.abspath(os.path.dirname(__file__))

# Load input values
input_tuple = pickle.load(open(
    os.path.join(CUR_PATH, 'run_btax_baseline_inputs.pkl'),
    'rb'), encoding='Latin')
test_run, baseline, start_year, iit_reform, user_params = input_tuple
# Load pickle with results to check against
(result_by_asset, result_by_industry) =\
    pickle.load(open(
        os.path.join(CUR_PATH, 'run_btax_baseline_outputs.pkl'),
        'rb'), encoding='Latin')
# Run B-Tax with these inputs
test_by_asset, test_by_industry = run_btax.run_btax(
    test_run, baseline, start_year, iit_reform, **user_params)
# Lists of variables to compare
asset_var_list = ['delta', 'z_c', 'z_c_d', 'z_c_e', 'z_nc',
                  'z_nc_d', 'z_nc_e', 'rho_c', 'rho_c_d', 'rho_c_e',
                  'rho_nc', 'rho_nc_d', 'rho_nc_e', 'ucc_c',
                  'ucc_c_d', 'ucc_c_e', 'ucc_nc', 'ucc_nc_d',
                  'ucc_nc_e', 'metr_c', 'metr_c_d', 'metr_c_e',
                  'metr_nc', 'metr_nc_d', 'metr_nc_e', 'mettr_c',
                  'mettr_c_d', 'mettr_c_e', 'mettr_nc',
                  'mettr_nc_d', 'mettr_nc_e', 'assets_c',
                  'assets_nc']
industry_var_list = ['delta_c', 'delta_c', 'z_c', 'z_c_d', 'z_c_e',
                     'z_nc', 'z_nc_d', 'z_nc_e', 'rho_c', 'rho_c_d',
                     'rho_c_e', 'rho_nc', 'rho_nc_d', 'rho_nc_e',
                     'ucc_c', 'ucc_c_d', 'ucc_c_e', 'ucc_nc',
                     'ucc_nc_d', 'ucc_nc_e', 'metr_c', 'metr_c_d',
                     'metr_c_e', 'metr_nc', 'metr_nc_d',
                     'metr_nc_e', 'mettr_c', 'mettr_c_d',
                     'mettr_c_e', 'mettr_nc', 'mettr_nc_d',
                     'mettr_nc_e', 'assets_c', 'assets_nc']


@pytest.mark.parametrize('test_params,expected',
                         [((asset_var_list, test_by_asset),
                           result_by_asset),
                          ((industry_var_list, test_by_industry),
                           result_by_industry)],
                         ids=['by assset', 'by industry'])
def test_run_btax_asset(test_params, expected):
    # Test the run_btax.run_btax() function by reading in inputs and
    # confirming that output variables have the same values.
    # Don't just compare pickles of output because want this test to
    # work as add new output variables.
    var_list, test_df = test_params

    assert_frame_equal(test_df[var_list], expected[var_list],
                       check_dtype=False)
